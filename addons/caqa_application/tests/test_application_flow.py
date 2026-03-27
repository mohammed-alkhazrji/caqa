from odoo.tests.common import TransactionCase


class TestCaqaApplicationFlow(TransactionCase):

    def test_application_demo_exists(self):
        app = self.env.ref('caqa_application.demo_application_1')
        self.assertTrue(app.reference)
        self.assertTrue(app.institution_id)
        self.assertIn(app.state, ['under_evaluation', 'submitted', 'approved', 'conditional_approved', 'need_more_information'])
