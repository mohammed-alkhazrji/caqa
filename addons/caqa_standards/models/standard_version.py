from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CaqaStandardVersion(models.Model):
    _name = 'caqa.standard.version'
    _description = 'Standard Version'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'effective_start_date desc, id desc'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, tracking=True, index=True)
    framework_id = fields.Many2one('caqa.framework', required=True, ondelete='restrict', tracking=True)
    accreditation_type_id = fields.Many2one('caqa.accreditation.type', required=True, ondelete='restrict', tracking=True)
    effective_start_date = fields.Date(required=True, tracking=True)
    effective_end_date = fields.Date(tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('retired', 'Retired')], default='draft', required=True, tracking=True)
    is_default = fields.Boolean(default=False, tracking=True)
    description = fields.Html()
    active = fields.Boolean(default=True)
    chapter_ids = fields.One2many('caqa.standard.chapter', 'version_id', string='Chapters')
    chapter_count = fields.Integer(compute='_compute_counts')
    indicator_count = fields.Integer(compute='_compute_counts')

    _sql_constraints = [
        ('caqa_standard_version_code_framework_uniq', 'unique(code, framework_id, accreditation_type_id)', 'Standard version code must be unique per framework and accreditation type.'),
    ]

    @api.depends('chapter_ids', 'chapter_ids.subchapter_ids.indicator_ids')
    def _compute_counts(self):
        for rec in self:
            rec.chapter_count = len(rec.chapter_ids)
            rec.indicator_count = len(rec.chapter_ids.mapped('subchapter_ids.indicator_ids'))

    @api.constrains('effective_start_date', 'effective_end_date')
    def _check_dates(self):
        for rec in self:
            if rec.effective_start_date and rec.effective_end_date and rec.effective_end_date < rec.effective_start_date:
                raise ValidationError(_('Effective end date must not be earlier than effective start date.'))

    def action_activate(self):
        self.write({'state': 'active'})

    def action_retire(self):
        self.write({'state': 'retired'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_view_chapters(self):
        self.ensure_one()
        action = self.env.ref('caqa_standards.action_caqa_standard_chapter').read()[0]
        action['domain'] = [('version_id', '=', self.id)]
        action['context'] = {'default_version_id': self.id}
        return action
