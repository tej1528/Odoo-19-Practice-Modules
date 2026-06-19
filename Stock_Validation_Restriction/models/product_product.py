from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    available_sale_qty = fields.Float(
        string="Available Sale Qty",
        compute="_compute_available_sale_qty",
    )

    def _compute_available_sale_qty(self):
        StockMove = self.env["stock.move"]

        for product in self:
            outgoing_qty = sum(
                StockMove.search([
                    ("product_id", "=", product.id),
                    ("state", "in", ["confirmed", "assigned", "waiting"]),
                    ("picking_type_id.code", "=", "outgoing"),
                ]).mapped("product_uom_qty")
            )

            product.available_sale_qty = (
                product.qty_available - outgoing_qty
            )