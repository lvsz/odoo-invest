from odoo import api, fields, models


class InvestPortfolio(models.Model):
    _name = 'invest.portfolio'
    _order = 'sequence, name'

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(string="Sequence", default=100)
    partner_id = fields.Many2one(
        string="Owner",
        comodel_name='res.partner',
    )
    broker_id = fields.Many2one(
        string="Broker",
        comodel_name='invest.broker',
    )
    security_ids = fields.Many2many(
        string="Securities",
        comodel_name='invest.security',
    )
    cash = fields.Monetary(
        string="Excess Liquidity",
        currency_field='currency_id',
    )
    market_value = fields.Monetary(
        string="Market Value",
        currency_field='currency_id',
        compute='_compute_value',
    )
    total_value = fields.Monetary(
        string="Total Value",
        currency_field='currency_id',
        compute='_compute_value',
    )
    currency_id = fields.Many2one(
        string="Main Currency",
        comodel_name='res.currency',
        required=True,
    )

    @api.depends('security_ids.value')
    def _compute_value(self):
        for portfolio in self:
            market_value = 0
            for currency, assets in portfolio.security_ids.grouped('currency_id').entries():
                market_value += portfolio.currency_id._convert(
                    from_amount=sum(assets.mapped('value')),
                    to_currency=currency,
                    round=False,
                )
            portfolio.update({
                'market_value': market_value,
                'total_value': market_value + portfolio.cash,
            })
