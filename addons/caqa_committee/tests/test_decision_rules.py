from odoo.tests.common import TransactionCase


class TestCaqaDecisionRules(TransactionCase):

    def test_conditional_decision_has_conditions(self):
        decision = self.env.ref('caqa_committee.demo_final_decision_1')
        self.assertEqual(decision.decision, 'conditional_approved')
        self.assertTrue(decision.conditions_html)
