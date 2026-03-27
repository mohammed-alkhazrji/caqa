from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CaqaAccreditationType(models.Model):
    _name = 'caqa.accreditation.type'
    _description = 'Accreditation Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'framework_id, sequence, code, id'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, tracking=True, index=True)
    sequence = fields.Integer(default=10)
    framework_id = fields.Many2one('caqa.framework', required=True, ondelete='restrict', tracking=True)
    scope = fields.Selection(
        [('institutional', 'Institutional'), ('programmatic', 'Programmatic'), ('specialized', 'Specialized')],
        required=True,
        default='programmatic',
        tracking=True,
    )
    description = fields.Html()
    active = fields.Boolean(default=True)
    cycle_ids = fields.One2many('caqa.accreditation.cycle', 'accreditation_type_id', string='Cycles')
    cycle_count = fields.Integer(compute='_compute_cycle_count')

    _sql_constraints = [
        ('caqa_accreditation_type_code_framework_uniq', 'unique(code, framework_id)', 'Accreditation type code must be unique per framework.'),
    ]

    @api.depends('cycle_ids')
    def _compute_cycle_count(self):
        for rec in self:
            rec.cycle_count = len(rec.cycle_ids)

    @api.constrains('code')
    def _check_code(self):
        for rec in self:
            if rec.code and ' ' in rec.code.strip():
                raise ValidationError(_('Accreditation type code cannot contain spaces.'))

    def action_view_cycles(self):
        self.ensure_one()
        action = self.env.ref('caqa_core.action_caqa_accreditation_cycle').read()[0]
        action['domain'] = [('accreditation_type_id', '=', self.id)]
        action['context'] = {
            'default_framework_id': self.framework_id.id,
            'default_accreditation_type_id': self.id,
        }
        return action
