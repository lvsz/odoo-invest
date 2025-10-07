from odoo import models


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    def _get_rates(self, company, date):
        if (gbx := self.env.ref('invest.GBX')) in self:
            gbp = self.env.ref('base.GBP')
            rates = super(ResCurrency, self + gbp - gbx)._get_rates(company, date)
            rates[gbx.id] = (rates[gbp.id] if gbp in self else rates.pop(gbp.id)) * 100
            return rates
        return super()._get_rates(company, date)
