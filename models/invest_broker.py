from odoo import fields, models


class InvestBroker(models.Model):
    _name = 'invest.broker'

    name = fields.Char(
        string="Name",
        required=True,
    )
    code = fields.Char(
        string="Code",
        required=True,
    )

    _code_uniq = models.Constraint(
        'unique(code)',
        "Brokerage code must be unique.",
    )
