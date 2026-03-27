import io
import xlsxwriter
from odoo import http
from odoo.http import request, content_disposition


class CaqaReportXlsxController(http.Controller):

    def _build_response(self, filename, content):
        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition(filename)),
        ]
        return request.make_response(content, headers=headers)

    @http.route('/caqa/report/xlsx/application/<int:record_id>', type='http', auth='user')
    def application_xlsx(self, record_id, **kw):
        record = request.env['caqa.application'].sudo().browse(record_id)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = workbook.add_worksheet('Application')
        rows = [
            ('Reference', record.reference),
            ('Name', record.name),
            ('Institution', record.institution_id.display_name),
            ('Program', record.program_id.display_name),
            ('State', record.state),
            ('Completion', record.completion_rate),
            ('Readiness', record.readiness_score),
        ]
        for row, (label, value) in enumerate(rows):
            ws.write(row, 0, label)
            ws.write(row, 1, value or '')
        workbook.close()
        return self._build_response('%s.xlsx' % record.reference, output.getvalue())

    @http.route('/caqa/report/xlsx/site_visit/<int:record_id>', type='http', auth='user')
    def site_visit_xlsx(self, record_id, **kw):
        record = request.env['caqa.site.visit.report'].sudo().browse(record_id)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = workbook.add_worksheet('Site Visit')
        rows = [('Report', record.name), ('Application', record.application_id.reference), ('State', record.state), ('Date', str(record.report_date or ''))]
        for row, (label, value) in enumerate(rows):
            ws.write(row, 0, label); ws.write(row, 1, value or '')
        workbook.close()
        return self._build_response('%s.xlsx' % record.name.replace(' ', '_'), output.getvalue())

    @http.route('/caqa/report/xlsx/decision/<int:record_id>', type='http', auth='user')
    def decision_xlsx(self, record_id, **kw):
        record = request.env['caqa.final.decision'].sudo().browse(record_id)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = workbook.add_worksheet('Decision')
        rows = [('Reference', record.reference), ('Application', record.application_id.reference), ('Decision', record.decision), ('Date', str(record.decision_date or ''))]
        for row, (label, value) in enumerate(rows):
            ws.write(row, 0, label); ws.write(row, 1, value or '')
        workbook.close()
        return self._build_response('%s.xlsx' % record.reference, output.getvalue())

    @http.route('/caqa/report/xlsx/followup/<int:record_id>', type='http', auth='user')
    def followup_xlsx(self, record_id, **kw):
        record = request.env['caqa.followup.plan'].sudo().browse(record_id)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = workbook.add_worksheet('FollowUp')
        rows = [('Plan', record.name), ('Application', record.application_id.reference), ('State', record.state), ('Progress', record.progress_rate)]
        for row, (label, value) in enumerate(rows):
            ws.write(row, 0, label); ws.write(row, 1, value or '')
        workbook.close()
        return self._build_response('%s.xlsx' % record.name.replace(' ', '_'), output.getvalue())
