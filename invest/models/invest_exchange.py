from odoo import api, fields, models
from odoo.fields import Domain


class InvestExchange(models.Model):
    _name = 'invest.exchange'
    _description = "Stock Exchange"

    name = fields.Char()
    code = fields.Char(
        string="Market Identifier Code",
    )
    country_id = fields.Many2one(
        string="Country",
        comodel_name='res.country',
    )
    country_code = fields.Char(related='country_id.code')
    security_ids = fields.One2many(
        string="Securities",
        comodel_name='invest.security',
        inverse_name='exchange_id',
    )

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        result = []
        domain = Domain(domain or Domain.TRUE)
        if not operator in Domain.NEGATIVE_OPERATORS:
            exchanges = self.search_fetch(
                domain & Domain('code', operator, name),
                ['display_name'],
                limit=limit,
            )
            result.extend((exch.id, exch.display_name) for exch in exchanges.sudo())
            domain &= Domain('id', 'not in', exchanges.ids)
            if limit is not None:
                limit -= len(exchanges)
                if limit <= 0:
                    return result
        result.extend(super().name_search(name, domain, operator, limit))
        return result
