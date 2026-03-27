from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_caqa_institution = fields.Boolean(string='Is Accreditation Institution', index=True, tracking=True)
    institution_type_id = fields.Many2one('caqa.institution.type', tracking=True)
    caqa_institution_code = fields.Char(string='Institution Code', tracking=True, index=True, copy=False)
    institution_state = fields.Selection(
        [('draft', 'Draft'), ('active', 'Active'), ('suspended', 'Suspended'), ('archived', 'Archived')],
        default='draft',
        tracking=True,
    )
    establishment_year = fields.Integer(tracking=True)
    license_no = fields.Char(string='License Number', tracking=True)
    commercial_registration = fields.Char(tracking=True)
    official_website = fields.Char()
    profile_ids = fields.One2many('caqa.institution.profile', 'institution_id', string='Profiles')
    member_ids = fields.One2many('caqa.institution.member', 'institution_id', string='Members')
    caqa_profile_count = fields.Integer(compute='_compute_caqa_counts')
    caqa_member_count = fields.Integer(compute='_compute_caqa_counts')
    active_profile_id = fields.Many2one('caqa.institution.profile', compute='_compute_active_profile_id')

    _sql_constraints = [
        ('caqa_institution_code_uniq', 'unique(caqa_institution_code)', 'Institution code must be unique.'),
    ]

    @api.depends('profile_ids', 'member_ids')
    def _compute_caqa_counts(self):
        for rec in self:
            rec.caqa_profile_count = len(rec.profile_ids)
            rec.caqa_member_count = len(rec.member_ids)

    @api.depends('profile_ids.state', 'profile_ids.active')
    def _compute_active_profile_id(self):
        for rec in self:
            chosen = rec.profile_ids.filtered(lambda p: p.active and p.state in ('submitted', 'approved'))[:1]
            rec.active_profile_id = chosen.id or rec.profile_ids.filtered('active')[:1].id

    def action_view_profiles(self):
        self.ensure_one()
        action = self.env.ref('caqa_institution.action_caqa_institution_profile').read()[0]
        action['domain'] = [('institution_id', '=', self.id)]
        action['context'] = {'default_institution_id': self.id}
        return action

    def action_view_members(self):
        self.ensure_one()
        action = self.env.ref('caqa_institution.action_caqa_institution_member').read()[0]
        action['domain'] = [('institution_id', '=', self.id)]
        action['context'] = {'default_institution_id': self.id}
        return action
