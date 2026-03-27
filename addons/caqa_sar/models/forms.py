from odoo import api, fields, models, _


class CaqaFormTemplate(models.Model):
    _name = 'caqa.form.template'
    _description = 'Form Template'
    _order = 'sequence, name'

    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    applies_to = fields.Selection([('application', 'Application'), ('indicator', 'Indicator'), ('evidence', 'Evidence')], default='application', required=True)
    active = fields.Boolean(default=True)
    question_ids = fields.One2many('caqa.form.question', 'template_id')
    question_count = fields.Integer(compute='_compute_count')

    @api.depends('question_ids')
    def _compute_count(self):
        for rec in self:
            rec.question_count = len(rec.question_ids)

    _sql_constraints = [('caqa_form_template_code_uniq', 'unique(code)', 'Form template code must be unique.')]


class CaqaFormQuestion(models.Model):
    _name = 'caqa.form.question'
    _description = 'Form Question'
    _order = 'template_id, sequence, id'

    template_id = fields.Many2one('caqa.form.template', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    question_text = fields.Char(required=True)
    help_text = fields.Text()
    field_type = fields.Selection([('text', 'Text'), ('number', 'Number'), ('boolean', 'Boolean'), ('selection', 'Selection')], default='text', required=True)
    selection_options = fields.Char(help='Comma-separated values for selection fields')
    is_required = fields.Boolean(default=False)


class CaqaFormResponse(models.Model):
    _name = 'caqa.form.response'
    _description = 'Form Response'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(required=True)
    template_id = fields.Many2one('caqa.form.template', required=True, ondelete='restrict')
    application_id = fields.Many2one('caqa.application', ondelete='cascade')
    application_indicator_id = fields.Many2one('caqa.application.indicator', ondelete='cascade')
    evidence_id = fields.Many2one('caqa.evidence', ondelete='cascade')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved')], default='draft', tracking=True)
    submitted_by = fields.Many2one('res.users')
    completion_rate = fields.Float(compute='_compute_completion', store=True)
    answer_ids = fields.One2many('caqa.form.answer', 'response_id')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec.answer_ids:
                self.env['caqa.form.answer'].create([{
                    'response_id': rec.id,
                    'question_id': q.id,
                } for q in rec.template_id.question_ids])
        return records

    @api.depends('answer_ids.is_answered')
    def _compute_completion(self):
        for rec in self:
            total = len(rec.answer_ids)
            answered = len(rec.answer_ids.filtered('is_answered'))
            rec.completion_rate = round((answered / total * 100.0), 2) if total else 0.0

    def action_submit(self):
        for rec in self:
            rec.state = 'submitted'
            rec.submitted_by = self.env.user

    def action_approve(self):
        self.write({'state': 'approved'})


class CaqaFormAnswer(models.Model):
    _name = 'caqa.form.answer'
    _description = 'Form Answer'
    _order = 'question_id, id'

    response_id = fields.Many2one('caqa.form.response', required=True, ondelete='cascade')
    question_id = fields.Many2one('caqa.form.question', required=True, ondelete='cascade')
    answer_text = fields.Text()
    answer_number = fields.Float()
    answer_boolean = fields.Boolean()
    answer_selection = fields.Char()
    is_answered = fields.Boolean(compute='_compute_answered', store=True)

    @api.depends('answer_text', 'answer_number', 'answer_boolean', 'answer_selection')
    def _compute_answered(self):
        for rec in self:
            rec.is_answered = bool(rec.answer_text or rec.answer_number or rec.answer_boolean or rec.answer_selection)
