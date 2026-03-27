from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CaqaSarVersion(models.Model):
    _name = 'caqa.sar.version'
    _description = 'SAR Version'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'version_no desc, id desc'

    name = fields.Char(required=True, tracking=True)
    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade', tracking=True)
    institution_id = fields.Many2one(related='application_id.institution_id', store=True, readonly=True)
    version_no = fields.Integer(default=1, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('archived', 'Archived'),
    ], default='draft', tracking=True)
    generated_on = fields.Datetime(default=fields.Datetime.now)
    generated_by = fields.Many2one('res.users', default=lambda self: self.env.user)
    completion_rate = fields.Float(compute='_compute_completion', store=True)
    section_ids = fields.One2many('caqa.sar.section', 'version_id')
    note = fields.Html()

    @api.depends('section_ids.completion_rate')
    def _compute_completion(self):
        for rec in self:
            rates = rec.section_ids.mapped('completion_rate')
            rec.completion_rate = round(sum(rates) / len(rates), 2) if rates else 0.0

    def action_generate_sections(self):
        for rec in self:
            if rec.section_ids:
                continue
            for chapter in rec.application_id.chapter_ids:
                self.env['caqa.sar.section'].create({
                    'version_id': rec.id,
                    'application_id': rec.application_id.id,
                    'chapter_line_id': chapter.id,
                    'name': chapter.name,
                })

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_submit(self):
        for rec in self:
            if rec.completion_rate < 30:
                raise ValidationError(_('SAR completion is too low to submit.'))
            rec.state = 'submitted'

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_archive(self):
        self.write({'state': 'archived'})


class CaqaSarSection(models.Model):
    _name = 'caqa.sar.section'
    _description = 'SAR Section'
    _order = 'chapter_line_id, id'

    version_id = fields.Many2one('caqa.sar.version', required=True, ondelete='cascade')
    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade')
    chapter_line_id = fields.Many2one('caqa.application.chapter', ondelete='set null')
    name = fields.Char(required=True)
    content_html = fields.Html()
    state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('submitted', 'Submitted')], default='draft')
    completion_rate = fields.Float(compute='_compute_completion', store=True)

    @api.depends('content_html', 'state')
    def _compute_completion(self):
        for rec in self:
            content_rate = 100.0 if rec.content_html else 0.0
            state_rate = 100.0 if rec.state == 'submitted' else (50.0 if rec.state == 'in_progress' else 0.0)
            rec.completion_rate = round((content_rate + state_rate) / 2.0, 2)
