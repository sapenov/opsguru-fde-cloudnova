import argparse
import csv
import json
from pathlib import Path
import sys
from .core import ask, build

QUESTIONS = [
 'What was our total recognized revenue in USD for paid invoices in 2024?',
 'Which region has the highest average MRR per account?',
 'How much have we given back in refunds?',
 "What's the churn rate among Enterprise accounts vs Starter?",
 'List the top 5 accounts by revenue, and flag any with CSAT ≤ 2.',
 "How many invoices are stuck in pending/failed and what's the exposed $?",
]

def main():
    parser = argparse.ArgumentParser(description='Local CloudNova question demo')
    parser.add_argument('--question', help='One supported question; omit to run all six')
    parser.add_argument('--csv', default=str(Path(__file__).resolve().parent.parent/'source/cloudnova_invoices.csv'))
    args = parser.parse_args()
    try:
        with open(args.csv, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            required = {'invoice_id','account_id','account_name','region','plan','billing_cycle','seats','currency','amount','discount_pct','status','invoice_date','churned','csat_score'}
            if not reader.fieldnames or not required.issubset(reader.fieldnames): raise ValueError('CSV missing required columns')
            db, quality = build(reader)
        print('Quality and exclusions:',json.dumps(quality,sort_keys=True))
        print('Amounts and MRR are USD cents; dates use documented conventions. Account metrics use latest dated snapshot; churn is not dated. Refunds are signed. Missing/invalid values are excluded from dependent sums.')
        for question in [args.question] if args.question else QUESTIONS:
            print(json.dumps(ask(db,question),ensure_ascii=False,indent=2))
    except (OSError, ValueError, csv.Error) as exc:
        print('Error:',exc,file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__': sys.exit(main())
