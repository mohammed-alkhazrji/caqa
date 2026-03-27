from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CaqaEvidence(models.Model):
    _name = 'caqa.evidence'
    _description = 'Evidence'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(required=True, tracking=True)
    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade', tracking=True)
    institution_id = fields.Many2one(related='application_id.institution_id', store=True, readonly=True)
    application_indicator_id = fields.Many2one('caqa.application.indicator', ondelete='set null')
    requirement_id = fields.Many2one('caqa.evidence.requirement', ondelete='set null')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('uploaded', 'Uploaded'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('closed', 'Closed'),
    ], default='draft', tracking=True)
    summary = fields.Html()
    due_date = fields.Date()
    validation_completion_rate = fields.Float(compute='_compute_validation', store=True)
    attachment_count = fields.Integer(compute='_compute_validation')
    version_ids = fields.One2many('caqa.evidence.version', 'evidence_id')
    current_version_id = fields.Many2one('caqa.evidence.version')
    attachment_ids = fields.One2many('caqa.evidence.attachment', 'evidence_id')

    @api.depends('attachment_ids', 'summary', 'requirement_id')
    def _compute_validation(self):
        for rec in self:
            summary_rate = 100.0 if rec.summary else 0.0
            required_rate = 100.0 if rec.requirement_id else 50.0
            attach_rate = 100.0 if rec.attachment_ids else 0.0
            rec.validation_completion_rate = round((summary_rate + required_rate + attach_rate) / 3.0, 2)
            rec.attachment_count = len(rec.attachment_ids)

    def action_new_version(self):
        for rec in self:
            seq_no = max(rec.version_ids.mapped('sequence_no') or [0]) + 1
            version = self.env['caqa.evidence.version'].create({
                'evidence_id': rec.id,
                'name': '%s V%s' % (rec.name, seq_no),
                'sequence_no': seq_no,
                'state': 'draft',
            })
            rec.current_version_id = version.id

    def action_submit(self):
        for rec in self:
            if not rec.attachment_ids:
                raise ValidationError(_('At least one attachment is required before submission.'))
            rec.state = 'submitted'

    def action_under_review(self):
        self.write({'state': 'under_review'})

    def action_accept(self):
        self.write({'state': 'accepted'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_close(self):
        self.write({'state': 'closed'})


class CaqaEvidenceVersion(models.Model):
    _name = 'caqa.evidence.version'
    _description = 'Evidence Version'
    _order = 'sequence_no desc, id desc'

    evidence_id = fields.Many2one('caqa.evidence', required=True, ondelete='cascade')
    name = fields.Char(required=True)
    sequence_no = fields.Integer(default=1)
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('accepted', 'Accepted')], default='draft')
    attachment_ids = fields.One2many('caqa.evidence.attachment', 'version_id')


class CaqaEvidenceAttachment(models.Model):
    _name = 'caqa.evidence.attachment'
    _description = 'Evidence Attachment'
    _inherits = {'ir.attachment': 'attachment_id'}

    evidence_id = fields.Many2one('caqa.evidence', required=True, ondelete='cascade')
    version_id = fields.Many2one('caqa.evidence.version', ondelete='set null')
    attachment_id = fields.Many2one('ir.attachment', required=True, ondelete='cascade')
    name = fields.Char(related='attachment_id.name', store=True, readonly=False)
    datas = fields.Binary(related='attachment_id.datas', readonly=False)
    datas_fname = fields.Char(related='attachment_id.name', readonly=False)
    file_size = fields.Integer(related='attachment_id.file_size', readonly=False)
    mimetype = fields.Char(related='attachment_id.mimetype', readonly=False)
    attachment_state = fields.Selection([('draft', 'Draft'), ('validated', 'Validated'), ('rejected', 'Rejected')], default='draft')
