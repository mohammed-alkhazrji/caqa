# -*- coding: utf-8 -*-
{
    'name': 'CAQA Scoring Engine',
    'version': '1.0',
    'category': 'Quality Assurance',
    'summary': 'Quantitative Rubric-based Scoring Engine for CAQA Accreditation',
    'description': """
        Provides a comprehensive scoring engine for CAQA.
        Features:
        - Configurable 1-5 point Rubrics
        - Evaluation Cycles (Self-Assessment, Desk Review, Moderation)
        - Variance Detection & Discrepancy Workflows
        - Frozen Decision Snapshots
    """,
    'author': 'CAQA',
    'depends': ['caqa_application', 'caqa_standards', 'caqa_review'],
    'data': [
        'security/security_groups.xml',
        'security/caqa_scoring_rules.xml',
        'security/ir.model.access.csv',
        'data/seed_rubric.xml',
        'views/rubric_views.xml',
        'views/cycle_views.xml',
        'views/application_view_inherit.xml',
        'views/scoring_portal_templates.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
        ],
        'web.assets_frontend': [
            'caqa_scoring/static/src/scss/workspace.scss',
            'caqa_scoring/static/src/js/workspace.js',
        ],
    }
}
