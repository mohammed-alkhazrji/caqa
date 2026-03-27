from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    caqa_institution_member_ids = fields.One2many('caqa.institution.member', 'user_id', string='CAQA Institution Memberships')
    caqa_institution_ids = fields.Many2many('res.partner', compute='_compute_caqa_institutions', string='CAQA Institutions')

    def _compute_caqa_institutions(self):
        for rec in self:
            rec.caqa_institution_ids = rec.caqa_institution_member_ids.mapped('institution_id')
