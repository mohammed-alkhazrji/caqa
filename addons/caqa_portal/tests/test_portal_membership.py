from odoo.tests.common import TransactionCase


class TestCaqaPortalMembership(TransactionCase):

    def test_demo_member_exists(self):
        member = self.env.ref('caqa_institution.demo_member_portal_1')
        self.assertTrue(member.user_id)
        self.assertTrue(member.institution_id)
