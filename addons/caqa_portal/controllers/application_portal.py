import base64
from odoo import http
from odoo.http import request
from .portal import CaqaCustomerPortal

class CaqaApplicationPortal(CaqaCustomerPortal):

    @http.route(['/my/caqa/form/<int:response_id>'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_caqa_form_response_detail(self, response_id, **post):
        form_response = self._check_caqa_record('caqa.form.response', response_id, 'application_id.institution_id')
        if hasattr(form_response, 'status_code'):
            return form_response
            
        if request.httprequest.method == 'POST':
            # Save answers dynamically based on question ID
            for answer in form_response.answer_ids:
                a_id = answer.id
                field_type = answer.question_id.field_type
                
                if field_type == 'text':
                    val = post.get('answer_text_%s' % a_id)
                    if val is not None: 
                        answer.sudo().write({'answer_text': val})
                elif field_type == 'number':
                    val = post.get('answer_number_%s' % a_id)
                    if val:
                        try:
                            answer.sudo().write({'answer_number': float(val)})
                        except ValueError:
                            pass
                elif field_type == 'boolean':
                    val = post.get('answer_boolean_%s' % a_id) == 'on'
                    answer.sudo().write({'answer_boolean': val})
                elif field_type == 'selection':
                    val = post.get('answer_selection_%s' % a_id)
                    if val is not None: 
                        answer.sudo().write({'answer_selection': val})
                elif field_type == 'attachment':
                    file = post.get('answer_attachment_%s' % a_id)
                    if file and getattr(file, 'filename', False):
                        file_bytes = file.read()
                        answer.sudo().write({
                            'answer_attachment': base64.b64encode(file_bytes),
                            'answer_attachment_name': file.filename
                        })
                    
            if post.get('submit_now'):
                form_response.sudo().action_submit()
                
        return request.render('caqa_portal.portal_caqa_form_response_detail', {'form_response': form_response})
