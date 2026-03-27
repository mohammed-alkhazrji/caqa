from odoo import api, fields, models


class CaqaStandardChapter(models.Model):
    _name = 'caqa.standard.chapter'
    _description = 'Standard Chapter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'version_id, sequence, code'

    version_id = fields.Many2one('caqa.standard.version', required=True, ondelete='cascade', tracking=True)
    sequence = fields.Integer(default=10)
    code = fields.Char(required=True, tracking=True, index=True)
    name = fields.Char(required=True, tracking=True)
    description = fields.Html()
    weight = fields.Float(default=0.0, tracking=True)
    active = fields.Boolean(default=True)
    subchapter_ids = fields.One2many('caqa.standard.subchapter', 'chapter_id', string='Subchapters')
    subchapter_count = fields.Integer(compute='_compute_counts')
    indicator_count = fields.Integer(compute='_compute_counts')

    _sql_constraints = [
        ('caqa_standard_chapter_code_version_uniq', 'unique(code, version_id)', 'Chapter code must be unique per standard version.'),
    ]

    @api.depends('subchapter_ids', 'subchapter_ids.indicator_ids')
    def _compute_counts(self):
        for rec in self:
            rec.subchapter_count = len(rec.subchapter_ids)
            rec.indicator_count = len(rec.subchapter_ids.mapped('indicator_ids'))

    def action_view_subchapters(self):
        self.ensure_one()
        action = self.env.ref('caqa_standards.action_caqa_standard_subchapter').read()[0]
        action['domain'] = [('chapter_id', '=', self.id)]
        action['context'] = {'default_chapter_id': self.id, 'default_version_id': self.version_id.id}
        return action
