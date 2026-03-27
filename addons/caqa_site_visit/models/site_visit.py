from odoo import api, fields, models, _


class CaqaSiteVisit(models.Model):
    _name = 'caqa.site.visit'
    _description = 'Site Visit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    reference = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    name = fields.Char(required=True, tracking=True)
    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade', tracking=True)
    institution_id = fields.Many2one(related='application_id.institution_id', store=True, readonly=True)
    leader_id = fields.Many2one('res.users', tracking=True)
    start_date = fields.Datetime(tracking=True)
    end_date = fields.Datetime(tracking=True)
    state = fields.Selection([
        ('planned', 'Planned'),
        ('approved', 'Approved'),
        ('agenda_confirmed', 'Agenda Confirmed'),
        ('in_visit', 'In Visit'),
        ('completed', 'Completed'),
        ('report_submitted', 'Report Submitted'),
        ('closed', 'Closed'),
    ], default='planned', tracking=True)
    team_ids = fields.One2many('caqa.site.visit.team', 'visit_id')
    agenda_ids = fields.One2many('caqa.site.visit.agenda', 'visit_id')
    session_ids = fields.One2many('caqa.site.visit.session', 'visit_id')
    finding_ids = fields.One2many('caqa.site.visit.finding', 'visit_id')
    report_id = fields.Many2one('caqa.site.visit.report')
    finding_count = fields.Integer(compute='_compute_counts')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        seq = self.env['ir.sequence']
        for rec in records:
            if rec.reference == _('New'):
                rec.reference = seq.next_by_code('caqa.site.visit') or _('New')
            if not rec.report_id:
                report = self.env['caqa.site.visit.report'].create({
                    'name': '%s Report' % rec.name,
                    'visit_id': rec.id,
                    'application_id': rec.application_id.id,
                })
                rec.report_id = report.id
        return records

    @api.depends('finding_ids')
    def _compute_counts(self):
        for rec in self:
            rec.finding_count = len(rec.finding_ids)

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_confirm_agenda(self):
        self.write({'state': 'agenda_confirmed'})

    def action_start(self):
        self.write({'state': 'in_visit'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_submit_report(self):
        self.write({'state': 'report_submitted'})

    def action_close(self):
        self.write({'state': 'closed'})


class CaqaSiteVisitTeam(models.Model):
    _name = 'caqa.site.visit.team'
    _description = 'Site Visit Team Member'
    _order = 'visit_id, role, id'

    visit_id = fields.Many2one('caqa.site.visit', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', required=True)
    role = fields.Selection([('leader', 'Leader'), ('reviewer', 'Reviewer'), ('observer', 'Observer')], default='reviewer', required=True)
    organization = fields.Char()


class CaqaSiteVisitAgenda(models.Model):
    _name = 'caqa.site.visit.agenda'
    _description = 'Site Visit Agenda'
    _order = 'start_datetime, id'

    visit_id = fields.Many2one('caqa.site.visit', required=True, ondelete='cascade')
    title = fields.Char(required=True)
    start_datetime = fields.Datetime(required=True)
    end_datetime = fields.Datetime(required=True)
    location = fields.Char()
    owner_id = fields.Many2one('res.users')


class CaqaSiteVisitSession(models.Model):
    _name = 'caqa.site.visit.session'
    _description = 'Site Visit Session'
    _order = 'start_datetime, id'

    visit_id = fields.Many2one('caqa.site.visit', required=True, ondelete='cascade')
    agenda_id = fields.Many2one('caqa.site.visit.agenda', ondelete='set null')
    title = fields.Char(required=True)
    session_type = fields.Selection([('meeting', 'Meeting'), ('interview', 'Interview'), ('tour', 'Facility Tour')], default='meeting')
    start_datetime = fields.Datetime()
    end_datetime = fields.Datetime()
    participants = fields.Text()
    notes = fields.Html()


class CaqaSiteVisitFinding(models.Model):
    _name = 'caqa.site.visit.finding'
    _description = 'Site Visit Finding'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'severity desc, id'

    visit_id = fields.Many2one('caqa.site.visit', required=True, ondelete='cascade')
    application_id = fields.Many2one(related='visit_id.application_id', store=True, readonly=True)
    application_indicator_id = fields.Many2one('caqa.application.indicator', ondelete='set null')
    title = fields.Char(required=True)
    description = fields.Html()
    severity = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'), ('resolved', 'Resolved'), ('closed', 'Closed')], default='draft')
    corrective_action = fields.Html()


class CaqaSiteVisitReport(models.Model):
    _name = 'caqa.site.visit.report'
    _description = 'Site Visit Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'report_date desc, id desc'

    name = fields.Char(required=True)
    visit_id = fields.Many2one('caqa.site.visit', required=True, ondelete='cascade')
    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade')
    report_date = fields.Date(default=fields.Date.context_today)
    executive_summary = fields.Html()
    strengths = fields.Html()
    improvement_areas = fields.Html()
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved')], default='draft')

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})
