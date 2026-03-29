# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CaqaApplication(models.Model):
    _inherit = 'caqa.application'

    score_cycle_ids = fields.One2many('caqa.score.cycle', 'application_id', string='Evaluation Cycles')
    score_cycle_count = fields.Integer(string='Score Cycles', compute='_compute_score_cycle_count')

    @api.depends('score_cycle_ids')
    def _compute_score_cycle_count(self):
        for app in self:
            app.score_cycle_count = len(app.score_cycle_ids)

    def action_view_score_cycles(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("caqa_scoring.action_caqa_score_cycle")
        action['domain'] = [('application_id', '=', self.id)]
        action['context'] = {'default_application_id': self.id, 'default_program_id': self.program_id.id}
        return action
