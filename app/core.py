"""Deterministic CSV cleaning and bounded SQL question answering."""
import collections
import datetime as dt
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
import sqlite3

MAPS = {
 'status': {'paid':'paid','complete':'paid','completed':'paid','success':'paid','pending':'pending','in_review':'pending','awaiting':'pending','failed':'failed','declined':'failed','error':'failed','refunded':'refunded','refund':'refunded','charged_back':'refunded','void':'void','cancelled':'void','canceled':'void'},
 'plan': {'starter':'Starter','start':'Starter','tier 1':'Starter','pro':'Pro','professional':'Pro','tier 2':'Pro','enterprise':'Enterprise','ent':'Enterprise','tier 3':'Enterprise'},
 'billing_cycle': {'monthly':'monthly','annual':'annual','annually':'annual','yearly':'annual'},
 'churned': {'true':1,'yes':1,'1':1,'y':1,'false':0,'no':0,'0':0,'n':0}}
FX = {'USD':Decimal('1'), 'EUR':Decimal('1.08'), 'GBP':Decimal('1.27')}
PRICE = {'Starter':49,'Pro':99,'Enterprise':299}

def parse_date(value):
    value = value.strip()
    ambiguous = False
    m = re.fullmatch(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', value)
    if m:
        ambiguous = int(m[1]) <= 12 and int(m[2]) <= 12
    formats = ('%Y-%m-%d','%Y/%m/%d','%m/%d/%Y','%d-%m-%Y','%b %d %Y','%B %d %Y')
    for fmt in formats:
        try: return dt.datetime.strptime(value,fmt).date().isoformat(), ambiguous
        except ValueError: pass
    return None, ambiguous

def money(value, currency):
    s = value.strip().upper()
    markers = set(re.findall(r'USD|EUR|GBP|[$€£]', s))
    marker_currency = {'$':'USD','€':'EUR','£':'GBP','USD':'USD','EUR':'EUR','GBP':'GBP'}
    if currency not in FX or any(marker_currency[x] != currency for x in markers): return None
    s = re.sub(r'USD|EUR|GBP|[$€£,\s]', '', s)
    try:
        amount = Decimal(s)
        if not amount.is_finite(): return None
        return int((amount * FX[currency] * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError, OverflowError): return None

def build(rows):
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE invoices (seq INTEGER, invoice_id TEXT, account_id TEXT, account_name TEXT, region TEXT, plan TEXT, billing_cycle TEXT, seats INTEGER, discount TEXT, status TEXT, usd_cents INTEGER, invoice_date TEXT, churned INTEGER, csat INTEGER, mrr_cents INTEGER)')
    q = collections.Counter(input_rows=0, exact_duplicate_rows=0, conflicting_ids=0, missing_invoice_id=0, invalid_invoice_dates=0, ambiguous_invoice_dates=0, invalid_usd_amount=0, positive_refunds=0, invalid_mrr=0, invalid_churn=0, invalid_csat=0, malformed_email=0)
    seen, conflict = {}, set()
    for seq, raw in enumerate(rows):
        q['input_rows'] += 1
        invoice = raw.get('invoice_id','').strip()
        if not invoice:
            q['missing_invoice_id'] += 1; continue
        identity = tuple(raw.get(k,'') for k in sorted(raw))
        if invoice in seen:
            if identity == seen[invoice]: q['exact_duplicate_rows'] += 1
            else: conflict.add(invoice)
            continue
        seen[invoice] = identity
        parsed = {}
        for field, mapping in MAPS.items():
            parsed[field] = mapping.get(raw.get(field,'').strip().lower())
            if parsed[field] is None: q['unknown_'+field] += 1
        date, ambiguous = parse_date(raw.get('invoice_date',''))
        if not date: q['invalid_invoice_dates'] += 1
        if ambiguous: q['ambiguous_invoice_dates'] += 1
        currency = raw.get('currency','').strip().upper()
        cents = money(raw.get('amount',''),currency)
        if cents is None: q['invalid_usd_amount'] += 1
        if parsed['status'] == 'refunded' and cents is not None and cents >= 0:
            q['positive_refunds'] += 1; cents = None
        try:
            seats = int(raw.get('seats',''))
            discount = Decimal(raw.get('discount_pct',''))
            if seats <= 0 or not discount.is_finite() or not 0 <= discount <= 100 or parsed['plan'] is None: raise ValueError
            mrr = int((Decimal(PRICE[parsed['plan']]) * seats * (1-discount/100)*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
        except (ValueError, InvalidOperation):
            seats, discount, mrr = None, None, None; q['invalid_mrr'] += 1
        if parsed['churned'] is None: q['invalid_churn'] += 1
        try:
            csat = int(raw.get('csat_score',''))
            if not 1 <= csat <= 5: raise ValueError
        except ValueError:
            csat = None
            if raw.get('csat_score','').strip(): q['invalid_csat'] += 1
        email = raw.get('contact_email','').strip()
        if email and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email): q['malformed_email'] += 1
        account = raw.get('account_id','').strip()
        if not account: q['missing_account_id'] += 1
        db.execute('INSERT INTO invoices VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (seq,invoice,account or None,raw.get('account_name','').strip(),raw.get('region','').strip().upper() or None,parsed['plan'],parsed['billing_cycle'],seats,str(discount) if discount is not None else None,parsed['status'],cents,date,parsed['churned'],csat,mrr))
    q['conflicting_ids'] = len(conflict)
    q['canonical_invoices'] = len(seen)
    q['conflicting_invoice_ids'] = sorted(conflict)
    db.execute('''CREATE VIEW accounts AS SELECT * FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY invoice_date DESC, seq ASC) AS rn FROM invoices WHERE account_id IS NOT NULL AND invoice_date IS NOT NULL) WHERE rn=1''')
    q['accounts_without_valid_date'] = db.execute('SELECT count(DISTINCT account_id) FROM invoices WHERE account_id IS NOT NULL AND account_id NOT IN (SELECT account_id FROM accounts)').fetchone()[0]
    db.commit()
    db.execute('PRAGMA query_only=ON')
    return db, dict(q)

QUERIES = {
 'revenue': ('''SELECT ? AS year, COALESCE(SUM(CASE WHEN status='paid' THEN usd_cents END),0) AS paid_cents, COALESCE(SUM(CASE WHEN status='refunded' THEN usd_cents END),0) AS refund_cents, COALESCE(SUM(usd_cents),0) AS net_cents FROM invoices WHERE status IN ('paid','refunded') AND invoice_date >= ? AND invoice_date < ?''', ['year','paid_cents','refund_cents','net_cents']),
 'mrr': ('''SELECT region, ROUND(AVG(mrr_cents),2) AS average_mrr_cents, COUNT(*) AS active_accounts FROM accounts WHERE churned=0 AND mrr_cents IS NOT NULL AND region IS NOT NULL GROUP BY region ORDER BY average_mrr_cents DESC, region LIMIT 1''',['region','average_mrr_cents','active_accounts']),
 'refund': ('''SELECT COALESCE(SUM(usd_cents),0) AS refund_cents, COUNT(usd_cents) AS refund_invoices FROM invoices WHERE status='refunded' ''',['refund_cents','refund_invoices']),
 'churn': ('''SELECT plan, SUM(churned) AS churned_accounts, COUNT(*) AS known_accounts, ROUND(100.0*SUM(churned)/COUNT(*),2) AS churn_pct FROM accounts WHERE plan IN ('Enterprise','Starter') AND churned IS NOT NULL GROUP BY plan ORDER BY plan''',['plan','churned_accounts','known_accounts','churn_pct']),
 'top': ('''SELECT r.account_id, a.account_name, r.revenue_cents, a.csat, CASE WHEN a.csat IS NULL THEN NULL WHEN a.csat<=2 THEN 1 ELSE 0 END AS low_csat FROM (SELECT account_id, SUM(usd_cents) AS revenue_cents FROM invoices WHERE status IN ('paid','refunded') AND usd_cents IS NOT NULL AND account_id IS NOT NULL GROUP BY account_id) r LEFT JOIN accounts a ON a.account_id=r.account_id ORDER BY r.revenue_cents DESC, r.account_id LIMIT 5''',['account_id','account_name','revenue_cents','csat','low_csat']),
 'exposure': ('''SELECT COUNT(*) AS invoice_count, COALESCE(SUM(CASE WHEN usd_cents > 0 THEN usd_cents END),0) AS exposure_cents FROM invoices WHERE status IN ('pending','failed')''',['invoice_count','exposure_cents'])}

def ask(db, question):
    s = re.sub(r"[^a-z0-9]+", " ", question.lower()).strip()
    years = re.findall(r"\b(?:19|20)\d{2}\b", s)
    normalized = re.sub(r"\b(?:19|20)\d{2}\b", "YEAR", s)
    templates = {
        'what was our total recognized revenue in usd for paid invoices in YEAR': 'revenue',
        'what was total recognized revenue in usd for paid invoices in YEAR': 'revenue',
        'which region has the highest average mrr per account': 'mrr',
        'which region has highest average mrr per account': 'mrr',
        'how much have we given back in refunds': 'refund',
        'what s the churn rate among enterprise accounts vs starter': 'churn',
        'what is churn rate among enterprise accounts vs starter': 'churn',
        'list the top 5 accounts by revenue and flag any with csat 2': 'top',
        'list top 5 accounts by revenue and flag csat 2': 'top',
        'how many invoices are stuck in pending failed and what s the exposed': 'exposure',
        'how many invoices are pending failed and what is the exposed': 'exposure',
    }
    # Preserve the comparison operator: a different CSAT question must not silently match.
    if 'csat' in s and not ('≤' in question or '<=' in question):
        raise ValueError('Unsupported CSAT comparison; see README for supported templates')
    key = templates.get(normalized)
    if key is None: raise ValueError('Unsupported question; see README for supported templates')
    params = []
    if key == 'revenue':
        year = int(years[0]); params = [year, f'{year:04d}-01-01', f'{year+1:04d}-01-01']
    sql, columns = QUERIES[key]
    return {'question':question,'sql':sql,'parameters':params,'columns':columns,'rows':db.execute(sql,params).fetchall()}
