from odoo import models, _
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = "stock.move"
    def write(self, vals):
        if "quantity" in vals:
            for move in self:
                if move.picking_id.picking_type_id.code != "outgoing":
                    continue

                available_qty = move.product_id.qty_available
                entered_qty = float(vals["quantity"])
                if entered_qty > available_qty:
                    raise UserError(
                        _(
                            "Not enough stock available.\n\n"
                            "Product: %s\n"
                            "On Hand Quantity: %s\n"
                            "Entered Quantity: %s"
                        )
                        % (
                            move.product_id.display_name,
                            available_qty,
                            entered_qty,
                        )
                    )
        return super().write(vals)