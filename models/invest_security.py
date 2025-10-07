from odoo import fields, models


class InvestSecurity(models.Model):
    _name = 'invest.security'
    _inherit = ['invest.asset']
    _order = 'code'

    code = fields.Char(
        string="ISIN",
        index=True,
    )
    ticker = fields.Char(
        string="Ticker Symbol",
        index=True,
    )
    market_id = fields.Many2one(
        string="Market",
        comodel_name='invest.market',
    )
    variant = fields.Selection(
        string="Type",
        selection=[
            ('stock', "Stock"),
            ('etf', "ETF"),
            ('etc', "ETC"),
            ('bond', "Bond"),
            ('misc', "Misc."),
        ],
        default='stock',
    )

    _code_uniq = models.Constraint(
        'unique(code)',
        "ISIN must be unique.",
    )
    _ticker_uniq = models.Constraint(
        'unique(ticker, market_id)',
        "Ticker symbol must be unique per market.",
    )
