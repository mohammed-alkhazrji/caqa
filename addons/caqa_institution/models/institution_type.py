from odoo import api, fields, models


class CaqaInstitutionType(models.Model):
    _name = 'caqa.institution.type'
    _description = 'Institution Type'
    _order = 'sequence, name'

    sequence = fields.Integer(default=10)
    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, tracking=True, index=True)
    description = fields.Html()
    active = fields.Boolean(default=True)
    institution_ids = fields.One2many('res.partner', 'institution_type_id', string='Institutions')
    institution_count = fields.Integer(compute='_compute_counts')

    _sql_constraints = [
        ('caqa_institution_type_code_uniq', 'unique(code)', 'Institution type code must be unique.'),
    ]

    @api.depends('institution_ids')
    def _compute_counts(self):
        for rec in self:
            rec.institution_count = len(rec.institution_ids)
