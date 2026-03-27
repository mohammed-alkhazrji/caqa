from odoo import fields, models, api


class CaqaApplicationSarExtension(models.Model):
    _inherit = 'caqa.application'

    sar_version_ids = fields.One2many('caqa.sar.version', 'application_id')
    evidence_ids = fields.One2many('caqa.evidence', 'application_id')
    form_response_ids = fields.One2many('caqa.form.response', 'application_id')
    sar_version_count = fields.Integer(compute='_compute_sar_counts')
    evidence_count = fields.Integer(compute='_compute_sar_counts')

    @api.depends('sar_version_ids')
    def _compute_sar_counts(self):
        for rec in self:
            rec.sar_version_count = len(rec.sar_version_ids)
            rec.evidence_count = self.env['caqa.evidence'].search_count([('application_id', '=', rec.id)])

    def action_view_sar_versions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'SAR Versions',
            'res_model': 'caqa.sar.version',
            'view_mode': 'tree,form',
            'domain': [('application_id', '=', self.id)],
            'context': {'default_application_id': self.id},
        }

    def action_view_evidence(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Evidence',
            'res_model': 'caqa.evidence',
            'view_mode': 'tree,form',
            'domain': [('application_id', '=', self.id)],
            'context': {'default_application_id': self.id},
        }

    def action_generate_structure(self):
        # 1. First, execute the original structure generation
        res = super().action_generate_structure()
        
        for rec in self:
            # 2. Generate SAR Version if none exists
            if not rec.sar_version_ids:
                sar = self.env['caqa.sar.version'].create({
                    'name': 'SAR - %s' % rec.name,
                    'application_id': rec.id,
                })
                sar.action_generate_sections()
                
            # 3. Generate Evidences per Application Indicator
            for ind_line in rec.indicator_ids:
                if not ind_line.indicator_id:
                    continue
                # Get requirements defined on the standard indicator
                requirements = self.env['caqa.evidence.requirement'].search([
                    ('indicator_id', '=', ind_line.indicator_id.id)
                ])
                for req in requirements:
                    # Avoid duplicates
                    exists = self.env['caqa.evidence'].search_count([
                        ('application_id', '=', rec.id),
                        ('requirement_id', '=', req.id)
                    ])
                    if not exists:
                        self.env['caqa.evidence'].create({
                            'name': req.name,
                            'application_id': rec.id,
                            'application_indicator_id': ind_line.id,
                            'requirement_id': req.id,
                        })

            # 4. Generate Forms
            templates = self.env['caqa.form.template'].search([('applies_to', '=', 'application')])
            for template in templates:
                exists = self.env['caqa.form.response'].search_count([
                    ('application_id', '=', rec.id),
                    ('template_id', '=', template.id)
                ])
                if not exists:
                    self.env['caqa.form.response'].create({
                        'name': '%s - %s' % (template.name, rec.name),
                        'application_id': rec.id,
                        'template_id': template.id,
                    })

        return res

class CaqaApplicationIndicatorSarExtension(models.Model):
    _inherit = 'caqa.application.indicator'

    evidence_ids = fields.One2many('caqa.evidence', 'application_indicator_id')
    evidence_count = fields.Integer(compute='_compute_evidence_data')
    evidence_completion_rate = fields.Float(compute='_compute_evidence_data', store=True)

    @api.depends('evidence_ids.validation_completion_rate')
    def _compute_evidence_data(self):
        for rec in self:
            rec.evidence_count = len(rec.evidence_ids)
            rates = rec.evidence_ids.mapped('validation_completion_rate')
            rec.evidence_completion_rate = round(sum(rates) / len(rates), 2) if rates else 0.0
