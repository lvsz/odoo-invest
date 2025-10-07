from functools import partial

from odoo import api, fields, models


class InvestOrder(models.Model):
    _name = 'invest.portfolio.order'
    _description = "Investment Order"
    _order = 'date ASC, reference'

    reference = fields.Char(
        string="Order Reference",
        copy=False,
        default="New",
    )
    date = fields.Date(
        string="Order Date",
        index=True,
        required=True,
    )
    wallet_id = fields.Many2one(comodel_name='invest.portfolio.wallet', required=True)
    portfolio_id = fields.Many2one(related='wallet_id.portfolio_id', store=True)
    position_id = fields.Many2one('invest.portfolio.position')
    currency_id = fields.Many2one(related='wallet_id.currency_id', store=True)
    partner_id = fields.Many2one(
        string="Buyer",
        related='portfolio_id.partner_id',
    )
    security_id = fields.Many2one(comodel_name='invest.security')
    exchange_id = fields.Many2one(related='security_id.exchange_id')
    value = fields.Monetary(
        string="Asset Value",
        help="Asset Value at Time of Order",
        currency_field='currency_id',
    )
    quantity = fields.Float()
    broker_id = fields.Many2one(
        comodel_name='invest.broker',
        required=True,
    )
    broker_fee = fields.Monetary(
        string="Broker Fee",
        currency_field='currency_id',
    )
    amount_tax = fields.Monetary(
        string="Taxes",
        currency_field='currency_id',
    )
    amount_base = fields.Monetary(
        string="Base Amount",
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True,
    )
    amount_total = fields.Monetary(
        string="Total Amount",
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True,
    )
    attachment_ids = fields.One2many('ir.attachment', 'res_id')

    @api.depends('broker_fee', 'currency_id', 'quantity', 'security_id', 'amount_tax', 'value')
    def _compute_amounts(self):
        for order in self:
            order.amount_base = order.security_id.currency_id._convert(
                from_amount=order.value * -order.quantity,
                to_currency=order.currency_id,
            )
            order.amount_total = order.amount_base - order.broker_fee - order.amount_tax

    @api.model_create_multi
    def create(self, vals_list):
        new_reference = partial(self.env['ir.sequence'].next_by_code, 'invest.order')
        for vals in vals_list:
            if not (order_date := vals.get('date')):
                vals['date'] = order_date = fields.Date.today()
            elif isinstance(order_date, str):
                order_date = fields.Date.from_string(order_date)
            if not vals.get('reference'):
                vals['reference'] = new_reference(sequence_date=order_date)
        return super().create(vals_list)
