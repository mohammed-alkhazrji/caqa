{
    'name': 'CAQA Dashboard',
    'version': '17.0.2.0.0',
    'summary': 'Premium Executive and Operational Dashboard for CAQA',
    'sequence': 1,
    'description': """
        CAQA Premium Dashboard Module.
        Provides an OWL-based high-level analytics and operational dashboard 
        that serves as the landing page for the CAQA application, as well as a Standards Dashboard.
    """,
    'category': 'CAQA',
    'author': 'CAQA',
    'depends': ['base', 'web', 'caqa_core'], 
    'data': [
        'views/dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'caqa_dashboard/static/src/scss/dashboard.scss',
            'caqa_dashboard/static/src/js/dashboard.js',
            'caqa_dashboard/static/src/xml/dashboard.xml',
            'caqa_dashboard/static/src/js/standards_dashboard.js',
            'caqa_dashboard/static/src/xml/standards_dashboard.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
