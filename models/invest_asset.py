from odoo import fields, models


class InvestAsset(models.AbstractModel):
    _name = 'invest.asset'

    name = fields.Char(
        string="Name",
        required=True,
    )
    value = fields.Monetary(
        string="Value",
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        string="Currency",
        comodel_name='res.currency',
    )
