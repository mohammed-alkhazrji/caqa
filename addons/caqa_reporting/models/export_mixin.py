from odoo import models


class CaqaApplicationExportMixin(models.Model):
    _inherit = 'caqa.application'

    def action_export_xlsx(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_url', 'url': '/caqa/report/xlsx/application/%s' % self.id, 'target': 'self'}


class CaqaSiteVisitReportExportMixin(models.Model):
    _inherit = 'caqa.site.visit.report'

    def action_export_xlsx(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_url', 'url': '/caqa/report/xlsx/site_visit/%s' % self.id, 'target': 'self'}


class CaqaFinalDecisionExportMixin(models.Model):
    _inherit = 'caqa.final.decision'

    def action_export_xlsx(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_url', 'url': '/caqa/report/xlsx/decision/%s' % self.id, 'target': 'self'}


class CaqaFollowupPlanExportMixin(models.Model):
    _inherit = 'caqa.followup.plan'

    def action_export_xlsx(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_url', 'url': '/caqa/report/xlsx/followup/%s' % self.id, 'target': 'self'}
