import json
import math
from collections import defaultdict
from datetime import UTC, timedelta
from functools import partial
from zoneinfo import ZoneInfo

from odoo import api, fields, models
from odoo.fields import Command, Date, Domain
from odoo.tools import format_date


class InvestPortfolio(models.Model):
    _name = 'invest.portfolio'
    _description = "Investment Portfolio"
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
    currency_id = fields.Many2one(
        string="Main Currency",
        comodel_name='res.currency',
        required=True,
    )
    order_ids = fields.One2many(
        string="Orders",
        comodel_name='invest.portfolio.order',
        inverse_name='portfolio_id',
    )
    order_count = fields.Integer(compute='_compute_counts')
    position_ids = fields.One2many(
        string="Positions",
        comodel_name='invest.portfolio.position',
        inverse_name='portfolio_id',
        compute='_compute_position_ids',
        store=True,
    )
    position_count = fields.Integer(compute='_compute_counts')
    valuation_ids = fields.One2many(
        comodel_name='invest.portfolio.valuation',
        inverse_name='portfolio_id',
        compute='_compute_valuation_ids',
        store=True,
    )
    wallet_ids = fields.One2many(
        string="Wallets",
        comodel_name='invest.portfolio.wallet',
        inverse_name='portfolio_id',
    )
    cash = fields.Monetary(
        string="Excess Liquidity",
        currency_field='currency_id',
        compute='_compute_value',
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
    kanban_dashboard_graph = fields.Text(compute='_compute_kanban_dashboard_graph')

    @api.depends('order_ids')
    def _compute_position_ids(self):
        for portfolio in self:
            positions_by_security = portfolio.position_ids.grouped('security_id')
            for security, orders in portfolio.order_ids.grouped('security_id').items():
                if security in positions_by_security:
                    positions_by_security[security].order_ids = orders
                else:
                    portfolio.position_ids = [Command.create({
                        'security_id': security.id,
                        'order_ids': orders.ids,
                    })]

    @api.depends('order_ids', 'position_ids')
    def _compute_counts(self):
        for portfolio in self:
            portfolio.order_count = len(portfolio.order_ids)
            portfolio.position_count = len(portfolio.position_ids)

    @api.depends('write_date', 'position_ids')
    def _compute_valuation_ids(self):
        for portfolio in self:
            tz = ZoneInfo(portfolio.partner_id.tz or 'UTC')
            date = portfolio.write_date.replace(tzinfo=UTC).astimezone(tz).date()
            if date >= (today := Date.today()):
                # Currently limited to data from previous day's close
                date = today - timedelta(days=1)
            if next((v.date for v in portfolio.valuation_ids), date.min) < date:
                portfolio._add_valuation(date)

    @api.depends('valuation_ids')
    def _compute_value(self):
        keys = ['cash', 'market_value', 'total_value']
        for portfolio in self:
            if valuation := next(iter(portfolio.valuation_ids), False):
                vals = valuation.read(keys)
            else:
                vals = dict.from_keys(keys, 0)
            portfolio.update({
                'cash': vals['cash'],
                'market_value': vals['market_value'],
                'total_value': vals['total_value'],
            })

    def _get_positions_at_date(self, date):
        self.ensure_one()
        if max(self.order_ids.mapped('date')) <= date:
            return self.position_ids
        PortfolioPosition = positions = self.env['invest.portfolio.position']
        counts = defaultdict(float)
        domain = Domain('security_id', '=', self.id) & Domain('date', '<=', date)
        for order in self.order_ids.search_fetch(domain, ['security_id', 'quantity']):
            counts[order.security_id] += order.quantity
        for security, qty in counts.items():
            positions += PortfolioPosition.new({
                'portfolio_id': self.id,
                'security_id': security.id,
                'count': qty,
            })
        return positions

    def _get_valuation(self, date):
        self.ensure_one()
        self.valuation_ids.fetch(['date'])
        for valuation in self.valuation_ids:
            if valuation.date == date:
                return valuation
            if valuation.date < date:
                break
        return self._add_valuation(date)

    def _add_valuation(self, date):
        self.ensure_one()
        return self.valuation_ids.create({
            'date': date,
            'portfolio_id': self.id,
        })

    def _compute_kanban_dashboard_graph(self):
        fmt = partial(format_date, env=self.env, format_date='d LLLL Y')
        for portfolio in self:
            if valuations := self.valuation_ids:
                valuations.fetch(['date', 'total_value'])
                min_date = next(v.date for v in reversed(valuations))
                values = [{
                    'x': fmt(value=min_date - timedelta(days=1)),
                    'y': 0,
                }]
                values.extend({
                    'x': fmt(value=valuation.date),
                    'y': valuation.total_value,
                } for valuation in reversed(valuations))
            else:
                values = [{
                    'x': '',
                    'y': 100.0 * (10.0 + math.cos(math.pi ** i)),
                } for i in range(6)]
            portfolio.kanban_dashboard_graph = json.dumps([{
                'title': "",
                'values': values,
                'key': self.env._("Valuation"),
                'is_sample_data': not len(valuations),
            }])

    @api.model_create_multi
    def create(self, vals_list):
        install_mode = self.env.context.get('install_mode')
        for vals in vals_list:
            # Add a default wallet
            if not (install_mode or vals.get('wallet_ids')):
                vals['wallet_ids'] = [Command.create({'currency_id': vals['currency_id']})]
        return super().create(vals_list)
