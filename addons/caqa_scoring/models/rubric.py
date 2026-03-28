# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CaqaScoreRubric(models.Model):
    _name = 'caqa.score.rubric'
    _description = 'Evaluation Rubric Template'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True, copy=False)
    active = fields.Boolean(string='Active', default=True)
    is_default = fields.Boolean(string='Default Seed Rubric', default=False)
    
    level_ids = fields.One2many('caqa.score.rubric.level', 'rubric_id', string='Levels')

    @api.constrains('is_default')
    def _check_unique_default(self):
        for record in self:
            if record.is_default:
                defaults = self.search([('is_default', '=', True), ('id', '!=', record.id)])
                if defaults:
                    raise ValidationError(_('There can only be one default rubric in the system.'))


class CaqaScoreRubricLevel(models.Model):
    _name = 'caqa.score.rubric.level'
    _description = 'Rubric Level'
    _order = 'sequence, value_numeric'

    rubric_id = fields.Many2one('caqa.score.rubric', string='Rubric', required=True, ondelete='cascade')
    name_ar = fields.Char(string='Name (Arabic)', required=True)
    name_en = fields.Char(string='Name (English)', required=True)
    description = fields.Text(string='Description', translate=True)
    value_numeric = fields.Integer(string='Numeric Value', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    is_default_fail = fields.Boolean(string='Is Failing Level', default=False, 
                                     help="If true, a score of this level indicates failure or non-compliance.")
    color = fields.Char(string='Color', default='#B87C19', help="Hex color code for UI badges.")

    def name_get(self):
        result = []
        for level in self:
            name = f"{level.value_numeric} - {level.name_en} ({level.name_ar})"
            result.append((level.id, name))
        return result
