from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    hide_tax = fields.Boolean(
        compute="_compute_hide_tax",
    )

    @api.depends_context("uid")
    def _compute_hide_tax(self):
        hide_tax = not self.env.user.has_group(
            "Hide_Tax_from_Invoice.group_hide_tax"
        )
        for move in self:
            move.hide_tax = hide_tax