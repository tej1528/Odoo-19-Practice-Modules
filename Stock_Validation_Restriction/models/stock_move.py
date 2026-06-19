from odoo import _, models
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    def _validate_demand_qty(self, qty):

        if qty > self.product_uom_qty:
            raise UserError(
                _(
                    "You cannot deliver more than ordered quantity.\n\n"
                    "Product: %s\n"
                    "Ordered Quantity: %s\n"
                    "Entered Quantity: %s"
                )
                % (
                    self.product_id.display_name,
                    self.product_uom_qty,
                    qty,
                )
            )

    def _validate_available_stock(self, qty):

        available_qty = self.product_id.qty_available

        if qty > available_qty:
            raise UserError(
                _(
                    "Not enough stock available.\n\n"
                    "Product: %s\n"
                    "Available Quantity: %s\n"
                    "Entered Quantity: %s"
                )
                % (
                    self.product_id.display_name,
                    available_qty,
                    qty,
                )
            )

    def validate_outgoing_qty(self, qty):

        self.ensure_one()

        self._validate_demand_qty(qty)
        self._validate_available_stock(qty)

    def write(self, vals):

        if "quantity" in vals:

            for move in self.filtered(
                lambda m: m.picking_id.picking_type_id.code == "outgoing"
            ):
                move.validate_outgoing_qty(
                    float(vals["quantity"])
                )

        return super().write(vals)