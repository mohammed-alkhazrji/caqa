from odoo import fields, models


class CaqaProgramLearningOutcome(models.Model):
    _name = 'caqa.program.learning.outcome'
    _description = 'Program Learning Outcome'
    _order = 'program_id, sequence, code'

    sequence = fields.Integer(default=10)
    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
    description = fields.Html()
    outcome_type = fields.Selection([('knowledge', 'Knowledge'), ('skill', 'Skill'), ('value', 'Value')], default='knowledge', required=True)
    program_id = fields.Many2one('caqa.program', required=True, ondelete='cascade')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('caqa_program_learning_outcome_code_program_uniq', 'unique(code, program_id)', 'Learning outcome code must be unique per program.'),
    ]
