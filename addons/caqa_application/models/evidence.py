# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CaqaApplicationEvidence(models.Model):
    _name = 'caqa.application.evidence'
    _description = 'Application Evidence Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Description', required=True, tracking=True)
    application_id = fields.Many2one('caqa.application', string='Application', required=True, ondelete='cascade', tracking=True)
    indicator_id = fields.Many2one('caqa.standard.indicator', string='Linked Indicator', required=True, tracking=True)
    
    attachment = fields.Binary(string='Document file', attachment=True)
    attachment_name = fields.Char(string='File Name')
    
    state = fields.Selection([
        ('missing', 'Missing'),
        ('uploaded', 'Uploaded'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='missing', tracking=True)

    @api.onchange('attachment')
    def _onchange_attachment(self):
        if self.attachment and self.state == 'missing':
            self.state = 'uploaded'
            
    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'
