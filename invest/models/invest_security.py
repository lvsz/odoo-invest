from itertools import dropwhile

from requests import HTTPError

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command, Domain

from odoo.addons.invest import utils


class InvestSecurity(models.Model):
    _name = 'invest.security'
    _description = "Investment Security"
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=100)
    ticker = fields.Char(string="Ticker Symbol", required=True, index=True)
    code = fields.Char(string="ISIN", index=True)
    exchange_id = fields.Many2one('invest.exchange')
    exchange_code = fields.Char(related='exchange_id.code')
    currency_id = fields.Many2one('res.currency')
    entry_ids = fields.One2many('invest.security.entry', inverse_name='security_id')
    last_update = fields.Date(compute='_compute_last_update', store=True)
    value = fields.Monetary(
        currency_field='currency_id',
        compute='_compute_value',
        store=True,
    )
    type = fields.Selection(
        selection=[
            ('stock', "Stock"),
            ('etf', "ETF"),
        ],
        default='stock',
    )

    _code_uniq = models.Constraint(
        'unique(code, exchange_id)',
        "ISIN must be unique per market.",
    )
    _ticker_uniq = models.Constraint(
        'unique(ticker, exchange_id)',
        "Ticker symbol must be unique per market.",
    )

    @api.depends('entry_ids')
    def _compute_last_update(self):
        self.last_update = fields.Date.today()

    @api.depends('last_update')
    def _compute_value(self):
        for security in self:
            if not security.entry_ids:
                security.value = 0
            else:
                security.value = next(iter(security.entry_ids)).close

    @api.depends('ticker', 'exchange_code')
    @api.depends_context('display_short')
    def _compute_display_name(self):
        if self.env.context.get('display_short', True):
            self.fetch(['ticker', 'exchange_code'])
            for security in self:
                security.display_name = f"{security.ticker}.{security.exchange_code}"
        else:
            super()._compute_display_name()

    def _update_entries(self, api=None):
        force_update = self.env.context.get('force_update')
        self.entry_ids.fetch(['date'])
        for security in self:
            entered = {entry.date for entry in security.entry_ids}
            if entered and not force_update and max(entered) >= security.last_update:
                continue
            if api is None:
                try:
                    security._update_entries(api='fmp')
                except HTTPError:
                    security._update_entries(api='av')
                continue
            api_get = getattr(utils, f'{api}_get')
            self.entry_ids = [
                Command.create(dict(values, date=date))
                for date, values in api_get(security).items()
                if date not in entered
            ]
        self.last_update = fields.Date.today()

    def _get_entry(self, date):
        self.ensure_one()
        if date > fields.Date.today():
            raise UserError(self.env._("Cannot look into the future."))
        if not self.last_update or date > self.last_update:
            self._update_entries()
        self.entry_ids.fetch(['date'])
        if date < self.entry_ids[-1].date:
            return self.env['invest.security.entry']
        return next(dropwhile(lambda e: e.date > date, self.entry_ids))

    @api.readonly
    def action_update_entries(self):
        return self._update_entries()

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        result = []
        if not operator in Domain.NEGATIVE_OPERATORS:
            domain = Domain(domain or Domain.TRUE)
            if '.' in name:
                name, mic = name.split('.')
                domain &= Domain('exchange_code', 'ilike', mic)
            securities = self.search_fetch(
                domain & Domain('ticker', operator, name),
                ['display_name'],
                limit=limit,
            )
            result.extend((sec.id, sec.display_name) for sec in securities.sudo())
            domain &= Domain('id', 'not in', securities.ids)
            limit = None if limit is None else limit - len(securities)
        if limit is None or limit > 0:
            result.extend(super().name_search(name, domain, operator, limit))
        return result
