from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CaqaFramework(models.Model):
    _name = 'caqa.framework'
    _description = 'Accreditation Framework'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, code, id'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, tracking=True, index=True)
    sequence = fields.Integer(default=10)
    description = fields.Html()
    owner_organization = fields.Char(tracking=True)
    is_default = fields.Boolean(default=False, tracking=True)
    active = fields.Boolean(default=True)
    type_ids = fields.One2many('caqa.accreditation.type', 'framework_id', string='Accreditation Types')
    cycle_ids = fields.One2many('caqa.accreditation.cycle', 'framework_id', string='Cycles')
    type_count = fields.Integer(compute='_compute_counts')
    cycle_count = fields.Integer(compute='_compute_counts')

    _sql_constraints = [
        ('caqa_framework_code_uniq', 'unique(code)', 'Framework code must be unique.'),
        ('caqa_framework_name_uniq', 'unique(name)', 'Framework name must be unique.'),
    ]

    @api.depends('type_ids', 'cycle_ids')
    def _compute_counts(self):
        for rec in self:
            rec.type_count = len(rec.type_ids)
            rec.cycle_count = len(rec.cycle_ids)

    @api.constrains('code')
    def _check_code(self):
        for rec in self:
            if rec.code and ' ' in rec.code.strip():
                raise ValidationError(_('Framework code cannot contain spaces.'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        defaults = records.filtered('is_default')
        if defaults:
            self.search([('id', 'not in', defaults.ids)]).write({'is_default': False})
        return records

    def write(self, vals):
        result = super().write(vals)
        if vals.get('is_default'):
            for rec in self.filtered('is_default'):
                self.search([('id', '!=', rec.id)]).write({'is_default': False})
        return result

    def action_view_types(self):
        self.ensure_one()
        action = self.env.ref('caqa_core.action_caqa_accreditation_type').read()[0]
        action['domain'] = [('framework_id', '=', self.id)]
        action['context'] = {'default_framework_id': self.id}
        return action

    def action_view_cycles(self):
        self.ensure_one()
        action = self.env.ref('caqa_core.action_caqa_accreditation_cycle').read()[0]
        action['domain'] = [('framework_id', '=', self.id)]
        action['context'] = {'default_framework_id': self.id}
        return action
