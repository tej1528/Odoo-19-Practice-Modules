from odoo import _, models
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = "stock.move"

    def write(self, vals):
        if "quantity" in vals:
            for move in self.filtered(
                lambda m: m.picking_id.picking_type_id.code == "outgoing"
            ):
                entered_qty = float(vals["quantity"])
                # Ordered Qty Validation
                if entered_qty > move.product_uom_qty:
                    raise UserError(
                        _(
                            "You cannot deliver more than ordered quantity.\n\n"
                            "Product: %s\n"
                            "Ordered Quantity: %s\n"
                            "Entered Quantity: %s"
                        )
                        % (
                            move.product_id.display_name,
                            move.product_uom_qty,
                            entered_qty,
                        )
                    )

                # Stock Validation
                available_qty = move.product_id.available_sale_qty
                if entered_qty > available_qty:
                    raise UserError(
                        _(
                            "Not enough stock available.\n\n"
                            "Product: %s\n"
                            "Available Quantity: %s\n"
                            "Entered Quantity: %s"
                        )
                        % (
                            move.product_id.display_name,
                            available_qty,
                            entered_qty,
                        )
                    )
        return super().write(vals)