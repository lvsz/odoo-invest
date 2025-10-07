from odoo import api, fields, models


class InvestPortfolioValuation(models.Model):
    _name = 'invest.portfolio.valuation'
    _description = "Valuation"
    _order = 'date DESC'

    date = fields.Date(required=True)
    portfolio_id = fields.Many2one('invest.portfolio', required=True)
    wallet_ids = fields.One2many(related='portfolio_id.wallet_ids')
    currency_id = fields.Many2one(related='portfolio_id.currency_id')
    cash = fields.Monetary(
        string="Excess Liquidity",
        currency_field='currency_id',
        readonly=True,
    )
    market_value = fields.Monetary(
        string="Market Value",
        currency_field='currency_id',
        readonly=True,
    )
    total_value = fields.Monetary(
        string="Total Value",
        currency_field='currency_id',
        compute='_compute_total_value',
    )

    _date_uniq = models.Constraint(
        'unique(date, portfolio_id)',
        "Only one valuation per day per portfolio",
    )

    @api.depends('cash', 'market_value')
    def _compute_total_value(self):
        for valuation in self:
            valuation.total_value = valuation.cash + valuation.market_value

    def _recompute_valuation(self):
        self.ensure_one()
        positions_at_date = self.portfolio_id._get_positions_at_date(self.date)
        self.update({
            'cash': sum(currency._convert(
                from_amount=sum(wallet._get_cash_at_date(self.date) for wallet in wallets),
                to_currency=self.currency_id,
                date=self.date,
                round=False,
            ) for currency, wallets in self.wallet_ids.grouped('currency_id').items()),
            'market_value': sum(currency._convert(
                from_amount=sum(positions.mapped('value')),
                to_currency=self.currency_id,
                date=self.date,
                round=False,
            ) for currency, positions in positions_at_date.grouped('currency_id').items()),
        })

    @api.model_create_multi
    def create(self, vals_list):
        valuations = super().create(vals_list)
        # Calculate cash & market value
        for valuation, vals in zip(valuations, vals_list):
            if not vals.keys() & {'cash', 'market_value'}:
                valuation._recompute_valuation()
        return valuations
