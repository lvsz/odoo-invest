from collections import defaultdict

from odoo import api, fields, models


class InvestPortfolioWallet(models.Model):
    _name = 'invest.portfolio.wallet'
    _description = "Liquid Cash"

    name = fields.Char(compute='_compute_name', store=True)
    portfolio_id = fields.Many2one(
        comodel_name='invest.portfolio',
        required=True,
        index=True,
        ondelete='cascade',
    )
    order_ids = fields.One2many(
        'invest.portfolio.order',
        inverse_name='wallet_id',
    )
    transfer_ids = fields.One2many(
        'invest.portfolio.wallet.transfer',
        inverse_name='wallet_id',
    )
    currency_id = fields.Many2one(
        string="Wallet Currency",
        comodel_name='res.currency',
        compute='_compute_currency_id',
        precompute=True,
        store=True,
        required=True,
    )
    cash = fields.Monetary(
        currency_field='currency_id',
        compute='_compute_cash',
        store=True,
    )

    @api.depends('portfolio_id', 'currency_id')
    def _compute_name(self):
        for wallet in self:
            wallet.name = f"{wallet.portfolio_id.name} ({wallet.currency_id.name})"

    @api.depends('portfolio_id')
    def _compute_currency_id(self):
        for wallet in self:
            wallet.currency_id = wallet.portfolio_id.currency_id

    @api.depends('transfer_ids')
    def _compute_cash(self):
        for wallet in self:
            wallet.cash = wallet._get_cash_at_date(fields.Date.today())

    def _get_history(self, end_date=None):
        self.ensure_one()
        moves = defaultdict(float)
        end_date = end_date or fields.Date.today()

        self.transfer_ids.fetch(['date', 'amount'])
        for date, transfers in self.transfer_ids.grouped('date').items():
            if date > end_date:
                break
            moves[date] += sum(transfers.mapped('amount'))

        self.order_ids.fetch(['date', 'amount_total'])
        for date, orders in self.order_ids.grouped('date').items():
            if date > end_date:
                break
            moves[date] += sum(orders.mapped('amount_total'))

        run, result = 0, {}
        for date in sorted(moves):
            result[date] = run = self.currency_id.round(run + moves[date])
        return result

    def _get_cash_at_date(self, date):
        self.ensure_one()
        return next(reversed(self._get_history(date).values()), 0)
