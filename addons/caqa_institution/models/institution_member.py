from odoo import fields, models


class CaqaInstitutionMember(models.Model):
    _name = 'caqa.institution.member'
    _description = 'Institution Member'
    _order = 'institution_id, role, id'

    institution_id = fields.Many2one('res.partner', required=True, ondelete='cascade', domain=[('is_caqa_institution', '=', True)])
    user_id = fields.Many2one('res.users', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', related='user_id.partner_id', store=True, readonly=True)
    role = fields.Selection(
        [('supervisor', 'Supervisor'), ('user', 'User'), ('coordinator', 'Coordinator'), ('readonly', 'Readonly')],
        required=True, default='user',
    )
    active = fields.Boolean(default=True)
    note = fields.Char()

    _sql_constraints = [
        ('caqa_institution_member_uniq', 'unique(institution_id, user_id)', 'Each user can only be assigned once per institution.'),
    ]
