from odoo import Command, api, fields, models


class InvestPortfolioPosition(models.Model):
    _name = 'invest.portfolio.position'
    _description = "Security Position"

    portfolio_id = fields.Many2one('invest.portfolio')
    security_id = fields.Many2one('invest.security')
    quantity = fields.Float(compute='_compute_quantity', store=True)
    order_ids = fields.One2many(
        string="Order History of Position",
        comodel_name='invest.portfolio.order',
        inverse_name='position_id',
    )
    currency_id = fields.Many2one(related='security_id.currency_id')
    value = fields.Monetary(
        currency_field='currency_id',
        compute='_compute_value',
        store=True,
    )

    _position_uniq = models.Constraint(
        'unique(security_id, portfolio_id)',
        "Only one position per security per portfolio",
    )

    @api.depends('order_ids')
    def _compute_quantity(self):
        self.order_ids.fetch(['quantity'])
        for position in self:
            position.quantity = sum(position.order_ids.mapped('quantity'))

    @api.depends('quantity', 'security_id.value')
    def _compute_value(self):
        for position in self:
            position.value = position.quantity * position.security_id.value

    @api.depends('security_id', 'quantity', 'portfolio_id')
    @api.depends_context('include_portfolio')
    def _compute_display_name(self):
        portfolio_names = {}
        if self.env.context.get('include_portfolio'):
            self.portfolio_id.fetch(['display_name'])
            for portfolio in self.portfolio_id:
                portfolio_names[portfolio] = f" [{portfolio.display_name}]"
        self.security_id.fetch(['display_name'])
        for position in self:
            if (qty := position.quantity).is_integer():
                qty = int(qty)
            portfolio_name = portfolio_names.get(position.portfolio_id, "")
            position.display_name = f"{position.security_id.display_name} × {qty}{portfolio_name}"
