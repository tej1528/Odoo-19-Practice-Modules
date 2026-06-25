from odoo import _, api, models
from odoo.exceptions import UserError


class StockReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    @api.constrains('quantity')
    def _check_return_quantity(self):
        for line in self:
            delivered_qty = line.move_id.quantity
            if line.quantity > delivered_qty:
                raise UserError(
                    _(
                        "Validation Error!\n"
                        "You cannot manually enter a return quantity greater than what was delivered.\n\n"
                        "Product: %s\n"
                        "Delivered Qty: %s\n"
                        "Entered Qty: %s"
                    ) % (line.product_id.display_name, delivered_qty, line.quantity)
                )