from odoo import _, models
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    def _validate_demand_qty(self, qty):
        self.ensure_one()

        if qty > self.product_uom_qty:
            raise UserError(
                "ORDER_QTY_ERROR|%s|%s|%s"
                % (
                    self.product_id.display_name,
                    self.product_uom_qty,
                    qty,
                )
            )

    def _validate_available_stock(self, qty):
        self.ensure_one()

        available_qty = self.product_id.qty_available

        if qty > available_qty:
            raise UserError(
                "STOCK_QTY_ERROR|%s|%s|%s"
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