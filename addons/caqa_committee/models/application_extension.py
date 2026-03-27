from odoo import fields, models, api


class CaqaApplicationCommitteeExtension(models.Model):
    _inherit = 'caqa.application'

    final_decision_ids = fields.One2many('caqa.final.decision', 'application_id')
    final_decision_count = fields.Integer(compute='_compute_final_decision_count')

    @api.depends('final_decision_ids')
    def _compute_final_decision_count(self):
        for rec in self:
            rec.final_decision_count = len(rec.final_decision_ids)

    def action_view_final_decisions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Final Decisions',
            'res_model': 'caqa.final.decision',
            'view_mode': 'tree,form',
            'domain': [('application_id', '=', self.id)],
            'context': {'default_application_id': self.id},
        }
