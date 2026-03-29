# -*- coding: utf-8 -*-
from odoo import models, fields

class CaqaReviewNote(models.Model):
    _inherit = 'caqa.review.note'

    score_line_id = fields.Many2one(
        'caqa.score.line', 
        string='Score Line', 
        help='Optional quantitative score this qualitative note is linked to.'
    )
