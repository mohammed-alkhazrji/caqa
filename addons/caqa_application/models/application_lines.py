from odoo import api, fields, models


class CaqaApplicationChapter(models.Model):
    _name = 'caqa.application.chapter'
    _description = 'Application Chapter'
    _order = 'application_id, code'

    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade')
    chapter_id = fields.Many2one('caqa.standard.chapter', ondelete='restrict')
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    weight = fields.Float(default=0.0)
    completion_rate = fields.Float(compute='_compute_completion', store=True)
    subchapter_ids = fields.One2many('caqa.application.subchapter', 'chapter_line_id')
    indicator_ids = fields.One2many('caqa.application.indicator', 'chapter_line_id')

    @api.depends('indicator_ids.completion_rate')
    def _compute_completion(self):
        for rec in self:
            scores = rec.indicator_ids.mapped('completion_rate')
            rec.completion_rate = round(sum(scores) / len(scores), 2) if scores else 0.0


class CaqaApplicationSubchapter(models.Model):
    _name = 'caqa.application.subchapter'
    _description = 'Application Subchapter'
    _order = 'application_id, code'

    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade')
    chapter_line_id = fields.Many2one('caqa.application.chapter', required=True, ondelete='cascade')
    subchapter_id = fields.Many2one('caqa.standard.subchapter', ondelete='restrict')
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    weight = fields.Float(default=0.0)
    completion_rate = fields.Float(compute='_compute_completion', store=True)
    indicator_ids = fields.One2many('caqa.application.indicator', 'subchapter_line_id')

    @api.depends('indicator_ids.completion_rate')
    def _compute_completion(self):
        for rec in self:
            scores = rec.indicator_ids.mapped('completion_rate')
            rec.completion_rate = round(sum(scores) / len(scores), 2) if scores else 0.0


class CaqaApplicationIndicator(models.Model):
    _name = 'caqa.application.indicator'
    _description = 'Application Indicator'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'application_id, code'

    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade')
    chapter_line_id = fields.Many2one('caqa.application.chapter', required=True, ondelete='cascade')
    subchapter_line_id = fields.Many2one('caqa.application.subchapter', required=True, ondelete='cascade')
    indicator_id = fields.Many2one('caqa.standard.indicator', ondelete='restrict')
    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, tracking=True)
    indicator_type = fields.Selection([('documentary', 'Documentary'), ('qualitative', 'Qualitative'), ('quantitative', 'Quantitative'), ('governance', 'Governance'), ('capacity', 'Capacity')], default='documentary', required=True, tracking=True)
    weight = fields.Float(default=0.0, tracking=True)
    response_state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('submitted', 'Submitted'), ('reviewed', 'Reviewed'), ('returned', 'Returned')], default='draft', tracking=True)
    compliance_result = fields.Selection([('not_met', 'Not Met'), ('partially_met', 'Partially Met'), ('fully_met', 'Fully Met')], default='not_met', tracking=True)
    narrative_html = fields.Html()
    completion_rate = fields.Float(compute='_compute_completion', store=True)
    evidence_completion_rate = fields.Float(default=0.0)
    checkpoint_ids = fields.One2many('caqa.application.checkpoint', 'application_indicator_id')
    open_deficiency_count = fields.Integer(compute='_compute_completion')

    @api.depends('response_state', 'checkpoint_ids.state', 'evidence_completion_rate')
    def _compute_completion(self):
        for rec in self:
            checkpoint_total = len(rec.checkpoint_ids)
            checkpoint_done = len(rec.checkpoint_ids.filtered(lambda c: c.state in ('completed', 'reviewed')))
            checkpoint_rate = (checkpoint_done / checkpoint_total * 100.0) if checkpoint_total else 0.0
            narrative_rate = 100.0 if rec.narrative_html else 0.0
            state_rate = 100.0 if rec.response_state in ('submitted', 'reviewed') else (60.0 if rec.response_state == 'in_progress' else 0.0)
            rec.completion_rate = round((checkpoint_rate + narrative_rate + rec.evidence_completion_rate + state_rate) / 4.0, 2)
            rec.open_deficiency_count = self.env['caqa.application.deficiency'].search_count([
                ('application_indicator_id', '=', rec.id),
                ('state', 'not in', ['resolved', 'closed']),
            ])


class CaqaApplicationCheckpoint(models.Model):
    _name = 'caqa.application.checkpoint'
    _description = 'Application Checkpoint'
    _order = 'application_id, code'

    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade')
    chapter_line_id = fields.Many2one('caqa.application.chapter', ondelete='cascade')
    subchapter_line_id = fields.Many2one('caqa.application.subchapter', ondelete='cascade')
    application_indicator_id = fields.Many2one('caqa.application.indicator', required=True, ondelete='cascade')
    checkpoint_id = fields.Many2one('caqa.standard.checkpoint', ondelete='restrict')
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    weight = fields.Float(default=0.0)
    max_score = fields.Float(default=1.0)
    state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('reviewed', 'Reviewed')], default='draft')
    boolean_value = fields.Boolean()
    text_value = fields.Text()
    numeric_value = fields.Float()
    score = fields.Float()
    note = fields.Text()
