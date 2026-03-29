from odoo import api, fields, models


class CaqaStandardIndicator(models.Model):
    _name = 'caqa.standard.indicator'
    _description = 'Standard Indicator'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'subchapter_id, sequence, code'

    subchapter_id = fields.Many2one('caqa.standard.subchapter', required=True, ondelete='cascade', tracking=True)
    chapter_id = fields.Many2one('caqa.standard.chapter', related='subchapter_id.chapter_id', store=True, readonly=True)
    version_id = fields.Many2one('caqa.standard.version', related='subchapter_id.version_id', store=True, readonly=True)
    sequence = fields.Integer(default=10)
    code = fields.Char(required=True, tracking=True, index=True)
    name = fields.Char(required=True, tracking=True)
    indicator_type = fields.Selection([('documentary', 'Documentary'), ('qualitative', 'Qualitative'), ('quantitative', 'Quantitative'), ('governance', 'Governance'), ('capacity', 'Capacity')], default='documentary', required=True, tracking=True)
    description = fields.Html()
    measurement_method = fields.Text()
    weight = fields.Float(default=0.0, tracking=True)
    expected_evidence_count = fields.Integer(default=1, tracking=True)
    active = fields.Boolean(default=True)
    is_critical = fields.Boolean(string='Is Critical', default=False, tracking=True)
    checkpoint_ids = fields.One2many('caqa.standard.checkpoint', 'indicator_id', string='Checkpoints')
    evidence_requirement_ids = fields.One2many('caqa.evidence.requirement', 'indicator_id', string='Evidence Requirements')
    checkpoint_count = fields.Integer(compute='_compute_counts')
    evidence_requirement_count = fields.Integer(compute='_compute_counts')

    _sql_constraints = [
        ('caqa_standard_indicator_code_subchapter_uniq', 'unique(code, subchapter_id)', 'Indicator code must be unique per subchapter.'),
    ]

    @api.depends('checkpoint_ids', 'evidence_requirement_ids')
    def _compute_counts(self):
        for rec in self:
            rec.checkpoint_count = len(rec.checkpoint_ids)
            rec.evidence_requirement_count = len(rec.evidence_requirement_ids)

    def action_view_checkpoints(self):
        self.ensure_one()
        action = self.env.ref('caqa_standards.action_caqa_standard_checkpoint').read()[0]
        action['domain'] = [('indicator_id', '=', self.id)]
        action['context'] = {'default_indicator_id': self.id}
        return action

    def action_view_evidence_requirements(self):
        self.ensure_one()
        action = self.env.ref('caqa_standards.action_caqa_evidence_requirement').read()[0]
        action['domain'] = [('indicator_id', '=', self.id)]
        action['context'] = {'default_indicator_id': self.id}
        return action
