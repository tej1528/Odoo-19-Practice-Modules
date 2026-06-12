from odoo import models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        for order in self:
            for line in order.order_line:
                product = line.product_id
                forecasted_qty = product.virtual_available
                if line.product_uom_qty > forecasted_qty:
                    raise UserError(
                        _(
                            "Not enough stock available.\n\n"
                            "Product: %s\n"
                            "Forecasted Quantity: %s\n"
                            "Requested Quantity: %s"
                        )
                        % (
                            product.display_name,
                            forecasted_qty,
                            line.product_uom_qty,
                        )
                    )
        return super().action_confirm()