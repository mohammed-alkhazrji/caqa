from odoo import api, fields, models, _


class CaqaInstitutionProfile(models.Model):
    _name = 'caqa.institution.profile'
    _description = 'Institution Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'write_date desc, id desc'

    name = fields.Char(required=True, tracking=True)
    institution_id = fields.Many2one('res.partner', required=True, ondelete='cascade', domain=[('is_caqa_institution', '=', True)], tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('in_progress', 'In Progress'), ('submitted', 'Submitted'), ('approved', 'Approved')],
        default='draft', required=True, tracking=True,
    )
    overview = fields.Html()
    vision = fields.Html()
    mission = fields.Html()
    strategic_goals = fields.Html()
    governance_structure = fields.Html()
    quality_system_summary = fields.Html()
    student_count = fields.Integer(tracking=True)
    faculty_count = fields.Integer(tracking=True)
    admin_staff_count = fields.Integer(tracking=True)
    branch_count = fields.Integer(tracking=True)
    profile_completion = fields.Float(compute='_compute_profile_completion', digits=(16, 2), store=True)
    contact_person_id = fields.Many2one('res.partner', tracking=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('caqa_institution_profile_name_per_institution_uniq', 'unique(name, institution_id)', 'Profile name must be unique per institution.'),
    ]

    @api.depends('overview', 'vision', 'mission', 'strategic_goals', 'governance_structure', 'quality_system_summary', 'student_count', 'faculty_count', 'admin_staff_count', 'branch_count', 'contact_person_id')
    def _compute_profile_completion(self):
        for rec in self:
            checks = [
                bool(rec.overview), bool(rec.vision), bool(rec.mission), bool(rec.strategic_goals), bool(rec.governance_structure),
                bool(rec.quality_system_summary), rec.student_count > 0, rec.faculty_count > 0, rec.admin_staff_count >= 0,
                rec.branch_count >= 0, bool(rec.contact_person_id),
            ]
            rec.profile_completion = (sum(1 for c in checks if c) / len(checks)) * 100 if checks else 0.0

    @api.onchange('institution_id')
    def _onchange_institution_id(self):
        if self.institution_id and not self.name:
            self.name = _('%s - Profile') % self.institution_id.name

    def action_set_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
