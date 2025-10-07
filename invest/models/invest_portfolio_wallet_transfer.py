from odoo import fields, models


class InvestPortfolioWalletTransfer(models.Model):
    _name = 'invest.portfolio.wallet.transfer'
    _description = "Cash Tansfer"
    _order = 'date ASC'

    wallet_id = fields.Many2one('invest.portfolio.wallet', required=True)
    currency_id = fields.Many2one(related='wallet_id.currency_id')
    amount = fields.Monetary(currency_field='currency_id')
    date = fields.Date(required=True)
