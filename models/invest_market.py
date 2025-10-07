from odoo import fields, models


class InvestMarket(models.Model):
    _name = 'invest.market'

    name = fields.Char(
        string="Name",
    )
    code = fields.Char(
        string="Market Identifier Code",
    )
    country_id = fields.Many2one(
        string="Country",
        comodel_name='res.country',
    )
    security_ids = fields.One2many(
        string="Securities",
        comodel_name='invest.security',
        inverse_name='market_id',
    )
