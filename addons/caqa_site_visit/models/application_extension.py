from odoo import fields, models, api


class CaqaApplicationSiteVisitExtension(models.Model):
    _inherit = 'caqa.application'

    site_visit_ids = fields.One2many('caqa.site.visit', 'application_id')
    site_visit_count = fields.Integer(compute='_compute_site_visit_count')

    @api.depends('site_visit_ids')
    def _compute_site_visit_count(self):
        for rec in self:
            rec.site_visit_count = len(rec.site_visit_ids)

    def action_view_site_visits(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Site Visits',
            'res_model': 'caqa.site.visit',
            'view_mode': 'tree,form',
            'domain': [('application_id', '=', self.id)],
            'context': {'default_application_id': self.id},
        }
