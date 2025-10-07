from functools import partial

from odoo import api, fields, models


class InvestOrder(models.Model):
    _name = 'invest.order'
    _inherit = ['mail.thread']
    _order = 'order_date desc'

    reference = fields.Char(
        string="Order Reference",
        copy=False,
        default="New",
    )
    state = fields.Selection(
        string="Order Status",
        selection=[
            ('draft', "Draft"),
            ('open', "Open"),
            ('done', "Done"),
        ],
        copy=False,
        default='draft',
    )
    order_date = fields.Datetime(
        string="Order Date",
        index=True,
    )
    partner_id = fields.Many2one(
        string="Buyer",
        comodel_name='res.partner',
    )
    security_id = fields.Many2one(
        string="Security",
        comodel_name='invest.security',
    )
    market_id = fields.Many2one(
        related='security_id.market_id',
    )
    currency_id = fields.Many2one(
        string="Main Currency",
        comodel_name='res.currency',
        required=True,
    )
    value = fields.Monetary(
        string="Asset Value",
        help="Asset value at time of order",
        currency_field='currency_id',
    )
    quantity = fields.Float(
        string="Quantity",
    )
    broker_id = fields.Many2one(
        string="Broker",
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
    )
    amount_total = fields.Monetary(
        string="Total Amount",
        currency_field='currency_id',
        compute='_compute_amounts',
    )

    @api.depends('broker_fee', 'currency_id', 'quantity', 'security_id', 'amount_tax', 'value')
    def _compute_amounts(self):
        for order in self:
            order.amount_base = order.currency_id._convert(
                from_amount=order.value * order.quantity,
                to_curreny=order.security_id.currency_id,
            )
            order.amount_total = order.amount_base + order.broker_fee + order.amount_tax

    @api.model_create_multi
    def create(self, vals_list):
        new_timestamp = partial(fields.Datetime.context_timestamp, self)
        new_reference = partial(self.env['ir.sequence'].next_by_code, 'invest.order')
        for vals in vals_list:
            if not vals.get('reference'):
                timestamp = new_timestamp(vals.get('order_date') or fields.Datetime.now())
                vals['reference'] = new_reference(sequence_date=timestamp)
        return super().create(vals_list)
