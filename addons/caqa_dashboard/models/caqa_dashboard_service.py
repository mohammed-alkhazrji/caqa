from odoo import models, api, fields

class CaqaDashboardService(models.AbstractModel):
    _name = 'caqa.dashboard.service'
    _description = 'CAQA Dashboard Backend Service'

    # =========================================================================
    # 1. MAIN COMMAND DASHBOARD
    # =========================================================================

    @api.model
    def get_dashboard_payload(self, filters=None):
        return {
            'user_name': self.env.user.name,
            'kpis': self.get_kpis(filters or {}),
            'charts': self.get_charts(filters or {}),
            'recent_activity': self.get_recent_activity(filters or {}),
            'alerts': self.get_alerts(filters or {}),
        }

    @api.model
    def get_kpis(self, filters):
        def safe_count(model_name, domain):
            if model_name in self.env:
                return self.env[model_name].search_count(domain)
            return 0
            
        def safe_avg(model_name, field_name):
            if model_name in self.env and field_name in self.env[model_name]._fields:
                records = self.env[model_name].search_read([(field_name, '!=', False)], [field_name])
                if records:
                    return sum(r[field_name] for r in records) / len(records)
            return 0

        total_apps = safe_count('caqa.application', [])
        pending_review = safe_count('caqa.application', [('state', '=', 'draft')]) 
        under_eval = safe_count('caqa.application', [('state', '=', 'review')]) 
        under_visit = safe_count('caqa.application', [('state', '=', 'visit')])
        active_visits = safe_count('caqa.site.visit', [('state', 'not in', ['done', 'cancel'])])
        open_deficiencies = safe_count('caqa.application.deficiency', [('state', '!=', 'resolved')])
        findings_count = safe_count('caqa.site.visit.finding', [])
        institutions = safe_count('res.partner', [('is_institution', '=', True)]) or safe_count('caqa.institution.profile', [])

        readiness_score = safe_avg('caqa.application', 'readiness_score')
        sar_completion = safe_avg('caqa.application', 'completion_rate')
        followup_progress = safe_avg('caqa.followup.plan', 'progress_rate')

        return {
            'total_applications': total_apps,
            'pending_review': pending_review,
            'under_evaluation': under_eval,
            'under_site_visit': under_visit,
            'open_deficiencies': open_deficiencies,
            'active_visits': active_visits,
            'findings_count': findings_count,
            'institutions': institutions,
            'readiness_score': round(readiness_score, 1),
            'sar_completion': round(sar_completion, 1),
            'followup_progress': round(followup_progress, 1),
        }

    @api.model
    def get_charts(self, filters):
        charts = {
            'apps_by_state': [],
            'deficiencies_by_severity': [],
            'apps_by_program': [],
        }

        if 'caqa.application' in self.env:
            app_groups = self.env['caqa.application'].read_group([], ['state'], ['state'])
            model_fields = self.env['caqa.application']._fields
            for g in app_groups:
                if g['state']:
                    sel_lbl = dict(model_fields['state'].selection).get(g['state'], g['state']) if hasattr(model_fields.get('state'), 'selection') and model_fields['state'].selection else g['state']
                    charts['apps_by_state'].append({'label': str(sel_lbl), 'value': g['state_count']})

            if 'program_id' in model_fields:
                prog_groups = self.env['caqa.application'].read_group([], ['program_id'], ['program_id'])
                for p in prog_groups:
                    if p['program_id']:
                        charts['apps_by_program'].append({'label': p['program_id'][1], 'value': p['program_id_count']})

        if 'caqa.application.deficiency' in self.env:
            if 'severity' in self.env['caqa.application.deficiency']._fields:
                def_groups = self.env['caqa.application.deficiency'].read_group([('state', '!=', 'resolved')], ['severity'], ['severity'])
                for g in def_groups:
                    if g['severity']:
                        charts['deficiencies_by_severity'].append({'label': str(g['severity']), 'value': g['severity_count']})

        return charts

    @api.model
    def get_recent_activity(self, filters):
        activities = []
        if 'caqa.application' in self.env:
            recent_apps = self.env['caqa.application'].search_read([], ['name', 'state', 'create_date'], limit=5, order='create_date desc')
            model_fields = self.env['caqa.application']._fields
            for app in recent_apps:
                state_lbl = dict(model_fields['state'].selection).get(app['state'], app['state']) if hasattr(model_fields.get('state'), 'selection') and model_fields['state'].selection else app['state']
                activities.append({
                    'title': f"إجراء على طلب {app['name']}",
                    'description': f"انتقل إلى الحالة: {state_lbl}",
                    'date': app['create_date'].strftime('%Y-%m-%d %H:%M') if app['create_date'] else '',
                })
        return activities

    @api.model
    def get_alerts(self, filters):
        alerts = []
        if 'caqa.application.deficiency' in self.env:
            open_defs = self.env['caqa.application.deficiency'].search_count([('state', '!=', 'resolved')])
            if open_defs > 0:
                alerts.append({'type': 'warning', 'message': f'يوجد عدد {open_defs} حالات عدم مطابقة مفتوحة تتطلب تدخلاً ومراجعة.'})
        return alerts

    # =========================================================================
    # 2. STANDARDS ANALYTICS DASHBOARD
    # =========================================================================

    @api.model
    def get_standards_payload(self, filters=None):
        return {
            'user_name': self.env.user.name,
            'kpis': self.get_standards_kpis(filters or {}),
            'charts': self.get_standards_charts(filters or {}),
            'risks': self.get_standards_risks(filters or {}),
        }

    @api.model
    def get_standards_kpis(self, filters):
        def safec(model_name):
            return self.env[model_name].search_count([]) if model_name in self.env else 0
            
        return {
            'versions': safec('caqa.standard.version'),
            'chapters': safec('caqa.standard.chapter'),
            'subchapters': safec('caqa.standard.subchapter'),
            'standards': safec('caqa.standard'), # Legacy bridge support
            'indicators': safec('caqa.standard.indicator'),
            'checkpoints': safec('caqa.evidence') or safec('caqa.standard.checkpoint'),
        }

    @api.model
    def get_standards_charts(self, filters):
        charts = {'distribution': []}
        if 'caqa.standard.version' in self.env:
            charts['distribution'].append({'label': 'النسخ والإطارات', 'value': self.env['caqa.standard.version'].search_count([])})
        if 'caqa.standard.chapter' in self.env:
            charts['distribution'].append({'label': 'الأبواب الرئيسية', 'value': self.env['caqa.standard.chapter'].search_count([])})
        if 'caqa.standard.subchapter' in self.env:
            charts['distribution'].append({'label': 'الفصول والمعايير الفرعية', 'value': self.env['caqa.standard.subchapter'].search_count([])})
        if 'caqa.standard' in self.env:
            charts['distribution'].append({'label': 'المعايير المباشرة', 'value': self.env['caqa.standard'].search_count([])})
        if 'caqa.standard.indicator' in self.env:
            charts['distribution'].append({'label': 'المؤشرات التفصيلية', 'value': self.env['caqa.standard.indicator'].search_count([])})
        return charts

    @api.model
    def get_standards_risks(self, filters):
        risks = []
        if 'caqa.application.deficiency' in self.env and 'indicator_id' in self.env['caqa.application.deficiency']._fields:
            def_groups = self.env['caqa.application.deficiency'].read_group(
                [('indicator_id', '!=', False)], 
                ['indicator_id'], 
                ['indicator_id'], 
                limit=5, 
                order='indicator_id_count desc'
            )
            max_count = def_groups[0]['indicator_id_count'] if def_groups else 1
            
            for g in def_groups:
                count = g['indicator_id_count']
                risks.append({
                    'name': g['indicator_id'][1] if g['indicator_id'] else 'مؤشر غير معرف',
                    'count': count,
                    'severity_percent': int((count / max_count) * 100)
                })
        return risks
