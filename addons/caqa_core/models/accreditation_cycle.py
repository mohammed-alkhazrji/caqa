from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CaqaAccreditationCycle(models.Model):
    _name = 'caqa.accreditation.cycle'
    _description = 'Accreditation Cycle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, tracking=True, index=True)
    framework_id = fields.Many2one('caqa.framework', required=True, ondelete='restrict', tracking=True)
    accreditation_type_id = fields.Many2one('caqa.accreditation.type', required=True, ondelete='restrict', tracking=True)
    start_date = fields.Date(required=True, tracking=True)
    end_date = fields.Date(required=True, tracking=True)
    academic_year = fields.Char(required=True, tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('open', 'Open'), ('closed', 'Closed')],
        default='draft',
        required=True,
        tracking=True,
    )
    description = fields.Html()
    is_current = fields.Boolean(compute='_compute_is_current')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('caqa_cycle_code_framework_uniq', 'unique(code, framework_id)', 'Cycle code must be unique per framework.'),
    ]

    @api.depends('start_date', 'end_date')
    def _compute_is_current(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_current = bool(rec.start_date and rec.end_date and rec.start_date <= today <= rec.end_date)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_('End date must be greater than or equal to start date.'))

    @api.onchange('framework_id')
    def _onchange_framework_id(self):
        if self.accreditation_type_id and self.accreditation_type_id.framework_id != self.framework_id:
            self.accreditation_type_id = False

    def action_set_draft(self):
        self.write({'state': 'draft'})

    def action_open_cycle(self):
        self.write({'state': 'open'})

    def action_close_cycle(self):
        self.write({'state': 'closed'})
