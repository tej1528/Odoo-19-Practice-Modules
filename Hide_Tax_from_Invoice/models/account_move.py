from copy import deepcopy
from lxml import etree

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    hide_tax = fields.Boolean(
        string="Hide Tax",
        compute="_compute_hide_tax",
    )

    @api.depends_context("uid")
    def _compute_hide_tax(self):
        for move in self:
            move.hide_tax = self.env.company.hide_tax

    @api.model
    def get_views(self, views, options=None):
        result = super().get_views(views, options=options)

        if not self.env.company.hide_tax:
            return result

        form_view = result["views"].get("form")
        if form_view:
            arch = etree.fromstring(form_view["arch"])

            # Invoice Line Taxes
            for node in arch.xpath("//field[@name='invoice_line_ids']//field[@name='tax_ids']"):
                node.set("column_invisible", "1")

            # Journal Item Taxes
            for node in arch.xpath("//field[@name='line_ids']//field[@name='tax_ids']"):
                node.set("column_invisible", "1")

            # Tax Tags
            for node in arch.xpath("//field[@name='line_ids']//field[@name='tax_tag_ids']"):
                node.set("column_invisible", "1")

            # Tax Totals
            for node in arch.xpath("//field[@name='tax_totals']"):
                node.set("invisible", "1")

            form_view["arch"] = etree.tostring(
                arch,
                encoding="unicode",
            )

        list_view = result["views"].get("list")
        if list_view:
            arch = etree.fromstring(list_view["arch"])

            # Hide Tax column
            for node in arch.xpath("//field[@name='amount_tax_signed']"):
                node.set("column_invisible", "1")

            list_view["arch"] = etree.tostring(
                arch,
                encoding="unicode",
            )
        return result