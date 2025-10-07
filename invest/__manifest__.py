{
    'name': "Invest",
    'version': '19.0.0.0.1',
    'summary': "Track & analyze investments",
    'depends': [
        'mail',
    ],
    'data': [
        'data/invest_exchange_data.xml',
        'data/invest_security_data.xml',
        'data/ir_sequence_data.xml',
        'data/res_currency_data.xml',

        'views/invest_security_views.xml',
        'views/invest_menus.xml',

        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/invest_demo_security_history.xml',
        'demo/invest_demo.xml',
    ],
    'application': True,
    'author': "Levi Siuzdak",
    'license': 'GPL-3',
}
