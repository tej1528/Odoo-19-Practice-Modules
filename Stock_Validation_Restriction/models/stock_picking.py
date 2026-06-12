from odoo import models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):

        # Delivery Orders
        for picking in self.filtered(
            lambda p: p.picking_type_id.code == "outgoing"
        ):

            for move in picking.move_ids:

                if move.quantity > move.product_id.qty_available:
                    raise UserError(
                        _(
                            "Not enough stock available.\n\n"
                            "Product: %s\n"
                            "Available Quantity: %s\n"
                            "Delivery Quantity: %s"
                        )
                        % (
                            move.product_id.display_name,
                            move.product_id.qty_available,
                            move.quantity,
                        )
                    )

        return super().button_validate()