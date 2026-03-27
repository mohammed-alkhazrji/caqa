from odoo import fields, models, _


class CaqaOperationalDashboard(models.TransientModel):
    _name = 'caqa.operational.dashboard'
    _description = 'Operational Dashboard'

    total_applications = fields.Integer(compute='_compute_values')
    pending_initial_review = fields.Integer(compute='_compute_values')
    under_evaluation = fields.Integer(compute='_compute_values')
    under_site_visit = fields.Integer(compute='_compute_values')
    open_deficiencies = fields.Integer(compute='_compute_values')
    avg_completion = fields.Float(compute='_compute_values')
    summary_html = fields.Html(compute='_compute_values')

    def _compute_values(self):
        App = self.env['caqa.application']
        Def = self.env['caqa.application.deficiency']
        for rec in self:
            apps = App.search([])
            rec.total_applications = len(apps)
            rec.pending_initial_review = App.search_count([('state', '=', 'under_initial_review')])
            rec.under_evaluation = App.search_count([('state', '=', 'under_evaluation')])
            rec.under_site_visit = App.search_count([('state', '=', 'under_site_visit')])
            rec.open_deficiencies = Def.search_count([('state', 'not in', ['resolved', 'closed'])])
            rec.avg_completion = sum(apps.mapped('completion_rate')) / len(apps) if apps else 0.0
            rec.summary_html = (
                '<div class="row g-3">'
                '<div class="col-3"><div class="alert alert-primary mb-0"><strong>%s</strong><br/>Applications</div></div>'
                '<div class="col-3"><div class="alert alert-warning mb-0"><strong>%s</strong><br/>Initial Review</div></div>'
                '<div class="col-3"><div class="alert alert-info mb-0"><strong>%s</strong><br/>Site Visit</div></div>'
                '<div class="col-3"><div class="alert alert-danger mb-0"><strong>%s</strong><br/>Open Deficiencies</div></div>'
                '</div>'
            ) % (rec.total_applications, rec.pending_initial_review, rec.under_site_visit, rec.open_deficiencies)

    def action_open_applications(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Applications'),
            'res_model': 'caqa.application',
            'view_mode': 'tree,graph,pivot,form',
        }


class CaqaExecutiveDashboard(models.TransientModel):
    _name = 'caqa.executive.dashboard'
    _description = 'Executive Dashboard'

    institution_count = fields.Integer(compute='_compute_values')
    approved_count = fields.Integer(compute='_compute_values')
    conditional_count = fields.Integer(compute='_compute_values')
    rejected_count = fields.Integer(compute='_compute_values')
    approval_rate = fields.Float(compute='_compute_values')
    avg_readiness = fields.Float(compute='_compute_values')
    summary_html = fields.Html(compute='_compute_values')

    def _compute_values(self):
        App = self.env['caqa.application']
        Inst = self.env['res.partner']
        for rec in self:
            apps = App.search([])
            approved = App.search_count([('state', '=', 'approved')])
            conditional = App.search_count([('state', '=', 'conditional_approved')])
            rejected = App.search_count([('state', '=', 'rejected')])
            rec.institution_count = Inst.search_count([('is_caqa_institution', '=', True)])
            rec.approved_count = approved
            rec.conditional_count = conditional
            rec.rejected_count = rejected
            rec.approval_rate = ((approved + conditional) / len(apps) * 100.0) if apps else 0.0
            rec.avg_readiness = sum(apps.mapped('readiness_score')) / len(apps) if apps else 0.0
            rec.summary_html = (
                '<div class="row g-3">'
                '<div class="col-4"><div class="alert alert-success mb-0"><strong>%s</strong><br/>Approved</div></div>'
                '<div class="col-4"><div class="alert alert-warning mb-0"><strong>%s</strong><br/>Conditional</div></div>'
                '<div class="col-4"><div class="alert alert-danger mb-0"><strong>%s</strong><br/>Rejected</div></div>'
                '</div>'
            ) % (rec.approved_count, rec.conditional_count, rec.rejected_count)

    def action_open_decisions(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Final Decisions'),
            'res_model': 'caqa.final.decision',
            'view_mode': 'tree,graph,pivot,form',
        }
