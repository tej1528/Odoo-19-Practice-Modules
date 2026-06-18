from odoo import models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)
class StockPicking(models.Model):
    _inherit = "stock.picking"

    def process_barcode_scan(self, barcode):
        self.ensure_one()

        product = self.env["product.product"].search(
            [("barcode", "=", barcode)],
            limit=1,
        )

        if not product:
            raise UserError(_("Barcode not found."))

        move = self.move_ids.filtered(
            lambda m: m.product_id == product
        )

        if not move:
            raise UserError(
                _("Product not found in Delivery Order.")
            )

        move = move[0]
        new_qty = move.quantity + 1
        
        # Demand validation only for Delivery Orders
        if self.picking_type_id.code == "outgoing":
            available_qty = product.available_sale_qty
            if new_qty > available_qty:
                raise UserError(
                    _(
                        "Not enough stock available.\n\n"
                        "Product: %s\n"
                        "Available Quantity: %s\n"
                        "Scanned Quantity: %s"
                    )
                    % (
                        product.display_name,
                        available_qty,
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

    def button_validate(self):
        # Purchase Receipt Logic
        if not self.env.context.get("skip_over_receipt_popup"):
            for picking in self.filtered(
                lambda p: p.picking_type_id.code == "incoming"):
                lines = []
                for move in picking.move_ids:
                    if move.quantity > move.product_uom_qty:
                        lines.append(
                            _(
                                "%s\nOrdered: %s\nReceived: %s"
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

        # Delivery Order Logic
        for picking in self.filtered(
            lambda p: p.picking_type_id.code == "outgoing"
        ):
            product_totals = {}
            for move in picking.move_ids:
                product = move.product_id
                if product.id not in product_totals:
                    product_totals[product.id] = {
                        "product": product,
                        "qty": 0.0,
                    }

                product_totals[product.id]["qty"] += move.quantity
            for data in product_totals.values():
                product = data["product"]
                entered_qty = data["qty"]
                available_qty = product.available_sale_qty
                if entered_qty > available_qty:
                    raise UserError(
                        _(
                            "Not enough stock available.\n\n"
                            "Product: %s\n"
                            "On Hand Quantity: %s\n"
                            "Entered Quantity: %s"
                        )
                        % (
                            product.display_name,
                            available_qty,
                            entered_qty,
                        )
                    )

        return super().button_validate() 