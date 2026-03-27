from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CaqaProgramCourse(models.Model):
    _name = 'caqa.program.course'
    _description = 'Program Course'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'program_id, semester_no, level_no, code'

    name = fields.Char(required=True, tracking=True)
    arabic_name = fields.Char(tracking=True)
    code = fields.Char(required=True, tracking=True, index=True)
    program_id = fields.Many2one('caqa.program', required=True, ondelete='cascade', tracking=True)
    level_no = fields.Integer(tracking=True)
    semester_no = fields.Integer(tracking=True)
    credit_hours = fields.Float(tracking=True)
    contact_hours = fields.Float(tracking=True)
    learning_outcomes = fields.Html()
    syllabus_summary = fields.Html()
    prerequisite_course_ids = fields.Many2many('caqa.program.course', 'caqa_program_course_prerequisite_rel', 'course_id', 'prerequisite_id', string='Prerequisites')
    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('retired', 'Retired')], default='draft', required=True, tracking=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('caqa_program_course_code_program_uniq', 'unique(code, program_id)', 'Course code must be unique per program.'),
    ]

    @api.constrains('credit_hours', 'contact_hours')
    def _check_hours(self):
        for rec in self:
            if rec.credit_hours and rec.credit_hours < 0:
                raise ValidationError(_('Credit hours cannot be negative.'))
            if rec.contact_hours and rec.contact_hours < 0:
                raise ValidationError(_('Contact hours cannot be negative.'))
