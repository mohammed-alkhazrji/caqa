from odoo import api, fields, models


class CaqaStandardSubchapter(models.Model):
    _name = 'caqa.standard.subchapter'
    _description = 'Standard Subchapter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'chapter_id, sequence, code'

    chapter_id = fields.Many2one('caqa.standard.chapter', required=True, ondelete='cascade', tracking=True)
    version_id = fields.Many2one('caqa.standard.version', related='chapter_id.version_id', store=True, readonly=True)
    sequence = fields.Integer(default=10)
    code = fields.Char(required=True, tracking=True, index=True)
    name = fields.Char(required=True, tracking=True)
    description = fields.Html()
    weight = fields.Float(default=0.0, tracking=True)
    active = fields.Boolean(default=True)
    indicator_ids = fields.One2many('caqa.standard.indicator', 'subchapter_id', string='Indicators')
    indicator_count = fields.Integer(compute='_compute_counts')

    _sql_constraints = [
        ('caqa_standard_subchapter_code_chapter_uniq', 'unique(code, chapter_id)', 'Subchapter code must be unique per chapter.'),
    ]

    @api.depends('indicator_ids')
    def _compute_counts(self):
        for rec in self:
            rec.indicator_count = len(rec.indicator_ids)

    def action_view_indicators(self):
        self.ensure_one()
        action = self.env.ref('caqa_standards.action_caqa_standard_indicator').read()[0]
        action['domain'] = [('subchapter_id', '=', self.id)]
        action['context'] = {'default_subchapter_id': self.id}
        return action
