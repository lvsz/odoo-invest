from odoo import fields, models


class InvestBroker(models.Model):
    _name = 'invest.broker'
    _description = "Stockbroker"
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer()
    currency_id = fields.Many2one('res.currency')
