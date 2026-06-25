from odoo import _, models
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_move_from_barcode(self, barcode):
        self.ensure_one()
        product = self.env["product.product"].search( [("barcode", "=", barcode)], limit=1, )
        if not product:
            raise UserError(_("Barcode not found."))

        move = self.move_ids.filtered( lambda m: m.product_id == product )[:1]

        if not move:
            raise UserError(
                _("Product not found in this Picking.")
            )
        return product, move

    def process_barcode_scan(self, barcode):
        self.ensure_one()

        product, move = self._get_move_from_barcode(barcode)
        new_qty = move.quantity + 1
        # Purchase Receipt
        if self.picking_type_id.code == "incoming":
            
            # Return Picking
            if self.return_id:

                if new_qty > move.product_uom_qty:
                    raise UserError(
                        _(
                            "You cannot receive more than return quantity.\n\n"
                            "Product: %s\n"
                            "Return Quantity: %s\n"
                            "Entered Quantity: %s"
                        )
                        % (
                            product.display_name,
                            move.product_uom_qty,
                            new_qty,
                        )
                    )

                move.write({
                    "quantity": new_qty,
                })

                return {
                    "success": True,
                    "quantity": move.quantity,
                }
            
            if new_qty > move.product_uom_qty:
                return {
                    "warning": True,
                    "product": product.display_name,
                    "ordered_qty": move.product_uom_qty,
                    "current_qty": move.quantity,
                    "new_qty": new_qty,
                }

            move.write({
                "quantity": new_qty,
            })
            return {
                "success": True,
                "quantity": move.quantity,
            }

        # Delivery / Internal
        move.write({
            "quantity": new_qty,
        })
        return {
            "success": True,
            "quantity": move.quantity,
        }

    def force_barcode_scan(self, barcode):
        self.ensure_one()
        _, move = self._get_move_from_barcode(barcode)
        move.write({
            "quantity": move.quantity + 1,
        })
        return {
            "success": True,
            "quantity": move.quantity,
        }

    def button_validate(self):
        if not self.env.context.get("skip_over_receipt_popup"):
            for picking in self.filtered(
                lambda p: p.picking_type_id.code == "incoming"
            ):
                lines = []
                for move in picking.move_ids:
                    if move.quantity > move.product_uom_qty:
                        lines.append(
                            _(
                                "%s\n"
                                "Ordered: %s\n"
                                "Received: %s"
                            )
                            % (
                                move.product_id.display_name,
                                move.product_uom_qty,
                                move.quantity,
                            )
                        )

                if lines:
                    return {
                        "type": "ir.actions.act_window",
                        "name": _("Over Receipt Warning"),
                        "res_model": "over.receipt.wizard",
                        "view_mode": "form",
                        "target": "new",
                        "context": {
                            "default_picking_id": picking.id,
                            "default_message": "\n\n".join(lines),
                        },
                    }
        return super().button_validate()