from odoo import api, fields, models


class CaqaEvidenceRequirement(models.Model):
    _name = 'caqa.evidence.requirement'
    _description = 'Evidence Requirement'
    _order = 'indicator_id, sequence, code'

    sequence = fields.Integer(default=10)
    indicator_id = fields.Many2one('caqa.standard.indicator', required=True, ondelete='cascade')
    checkpoint_id = fields.Many2one('caqa.standard.checkpoint', ondelete='set null', domain="[('indicator_id', '=', indicator_id)]")
    version_id = fields.Many2one('caqa.standard.version', related='indicator_id.version_id', store=True, readonly=True)
    requirement_level = fields.Selection([('indicator', 'Indicator'), ('checkpoint', 'Checkpoint')], default='indicator', required=True)
    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
    description = fields.Html()
    evidence_type = fields.Selection([('document', 'Document'), ('report', 'Report'), ('policy', 'Policy'), ('minutes', 'Meeting Minutes'), ('statistics', 'Statistics'), ('image', 'Image'), ('link', 'Link'), ('other', 'Other')], default='document', required=True)
    is_required = fields.Boolean(default=True)
    min_attachments = fields.Integer(default=1)
    accepted_extensions = fields.Char(default='pdf,doc,docx,xlsx,png,jpg')
    max_file_size_mb = fields.Integer(default=25)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('caqa_evidence_requirement_code_indicator_uniq', 'unique(code, indicator_id)', 'Evidence requirement code must be unique per indicator.'),
    ]

    @api.onchange('requirement_level')
    def _onchange_requirement_level(self):
        if self.requirement_level != 'checkpoint':
            self.checkpoint_id = False
