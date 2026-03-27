from odoo import api, fields, models


class CaqaStandardCheckpoint(models.Model):
    _name = 'caqa.standard.checkpoint'
    _description = 'Standard Checkpoint'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'indicator_id, sequence, code'

    indicator_id = fields.Many2one('caqa.standard.indicator', required=True, ondelete='cascade', tracking=True)
    version_id = fields.Many2one('caqa.standard.version', related='indicator_id.version_id', store=True, readonly=True)
    sequence = fields.Integer(default=10)
    code = fields.Char(required=True, tracking=True, index=True)
    name = fields.Char(required=True, tracking=True)
    description = fields.Html()
    weight = fields.Float(default=0.0, tracking=True)
    max_score = fields.Float(default=1.0, tracking=True)
    mandatory = fields.Boolean(default=True, tracking=True)
    active = fields.Boolean(default=True)
    evidence_requirement_ids = fields.One2many('caqa.evidence.requirement', 'checkpoint_id', string='Evidence Requirements')
    evidence_requirement_count = fields.Integer(compute='_compute_counts')

    _sql_constraints = [
        ('caqa_standard_checkpoint_code_indicator_uniq', 'unique(code, indicator_id)', 'Checkpoint code must be unique per indicator.'),
    ]

    @api.depends('evidence_requirement_ids')
    def _compute_counts(self):
        for rec in self:
            rec.evidence_requirement_count = len(rec.evidence_requirement_ids)
