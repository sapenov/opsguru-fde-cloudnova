import unittest
from app.core import build, ask

# Independent arithmetic: EUR 100 -> $108, EUR -20 -> -$21.60;
# Pro 2 seats at 10% -> $178.20 monthly, annual invoice $1,782.
def row(invoice, account, **overrides):
    base = dict(invoice_id=invoice, account_id=account, account_name=account,
                contact_email='', region='NA', industry='', plan='Pro', billing_cycle='annual',
                seats='2', currency='EUR', amount='100', discount_pct='10', status='paid',
                payment_method='', signup_date='2023-01-01', invoice_date='2024-01-05',
                churned='false', csat_score='', support_tickets='0')
    base.update(overrides)
    return base

class Evaluation(unittest.TestCase):
    def setUp(self):
        self.rows = [row('1','A'), row('1','A',amount='999'), row('2','A',amount='-20',status='refund',invoice_date='05-01-2024'),
          row('3','B',plan='Starter',seats='1',discount_pct='0',currency='USD',amount='49',churned='yes',csat_score='2'),
          row('4','C',plan='Enterprise',seats='1',discount_pct='0',currency='USD',amount='299',status='pending'),
          row('5','C',plan='Enterprise',seats='1',discount_pct='0',currency='USD',amount='10',status='failed',invoice_date='2024-02-01')]
        self.db, self.quality = build(self.rows)
    def result(self, question):
        return ask(self.db, question)['rows']
    def test_paid_and_refund(self):
        self.assertEqual(self.result('What was total recognized revenue in USD for paid invoices in 2024?')[0], (2024,15700,-2160,13540))
    def test_region_average_distinct_active_accounts(self):
        self.assertEqual(self.result('Which region has highest average MRR per account?')[0], ('NA',23860,2))
    def test_refunds(self):
        self.assertEqual(self.result('How much have we given back in refunds?')[0], (-2160,1))
    def test_churn_snapshot(self):
        self.assertEqual(self.result('What is churn rate among Enterprise accounts vs Starter?'), [('Enterprise',0,1,0.0),('Starter',1,1,100.0)])
    def test_top_accounts_csat(self):
        self.assertEqual(self.result('List top 5 accounts by revenue and flag CSAT ≤ 2.'), [('A','A',8640,None,None),('B','B',4900,2,1)])
    def test_exposure(self):
        self.assertEqual(self.result('How many invoices are pending/failed and what is the exposed $?')[0], (2,30900))
    def test_conflict_and_ambiguous_date(self):
        self.assertEqual(self.quality['conflicting_ids'],1)
        self.assertEqual(self.quality['ambiguous_invoice_dates'],1)
    def test_unsupported_is_rejected(self):
        with self.assertRaises(ValueError): ask(self.db,'DROP TABLE invoices')
    @unittest.expectedFailure
    def test_historical_churn_date_unavailable(self):
        self.assertIsNotNone(ask(self.db,'What was churn rate in 2024?'))

if __name__ == '__main__': unittest.main(verbosity=2)
