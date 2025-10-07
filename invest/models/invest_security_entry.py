from itertools import pairwise

from odoo import api, fields, models


class InvestSecurityEntry(models.Model):
    _name = 'invest.security.entry'
    _description = "Security Entry"
    _order = 'date DESC'

    date = fields.Date(required=True, index=True)
    security_id = fields.Many2one('invest.security', index=True)
    currency_id = fields.Many2one('res.currency', related='security_id.currency_id')
    previous_entry_id = fields.Many2one(
        'invest.security.entry',
        compute='_compute_linked_ids',
        store=True,
    )
    next_entry_id = fields.Many2one(
        'invest.security.entry',
        compute='_compute_linked_ids',
        store=True,
    )

    open = fields.Monetary(currency_field='currency_id')
    close = fields.Monetary(currency_field='currency_id')
    high = fields.Monetary(currency_field='currency_id')
    low = fields.Monetary(currency_field='currency_id')
    volume = fields.Integer()
    change = fields.Float(compute='_compute_change')

    _date_uniq = models.Constraint(
        'unique(date, security_id)',
        "Only one entry per day per security",
    )

    @api.depends('security_id.entry_ids')
    def _compute_linked_ids(self):
        all_entries = self.search([('security_id', 'in', self.security_id.ids)])
        for entries in all_entries.grouped('security_id').values():
            for curr, prev in pairwise(entries):
                curr.previous_entry_id = prev
                prev.next_entry_id = curr

    @api.depends('next_entry_ids')
    def _compute_next_entry_id(self):
        for entry in self:
            entry.next_entry_id = next(iter(entry.next_entry_ids), None)

    def _compute_change(self):
        for entry in self:
            if prev := entry.previous_entry_id:
                entry.change = entry.close / prev.close - 1
            else:
                entry.change = 0
