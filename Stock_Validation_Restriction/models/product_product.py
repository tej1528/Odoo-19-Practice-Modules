from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    available_sale_qty = fields.Float(
        string="Available Sale Qty",
        compute="_compute_available_sale_qty",
    )

    def _compute_available_sale_qty(self):

        for product in self:

            outgoing_moves = self.env["stock.move"].search([
                ("product_id", "=", product.id),
                ("state", "in", [
                    "confirmed",
                    "assigned",
                    "waiting",
                ]),
                ("picking_type_id.code", "=", "outgoing"),
            ])

            outgoing_qty = sum(
                outgoing_moves.mapped("product_uom_qty")
            )

            product.available_sale_qty = (
                product.qty_available - outgoing_qty
            )