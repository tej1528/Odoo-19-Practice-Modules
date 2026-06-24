from odoo import _, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def action_create_returns(self):
        self.ensure_one()

        for line in self.product_return_moves:

            delivered_qty = line.move_id.quantity

            _logger.info(
                "Product=%s Delivered=%s Return=%s",
                line.product_id.display_name,
                delivered_qty,
                line.quantity,
            )

            if line.quantity > delivered_qty:
                raise UserError(
                    _(
                        "You cannot return more than delivered quantity.\n\n"
                        "Product: %s\n"
                        "Delivered Qty: %s\n"
                        "Return Qty: %s"
                    )
                    % (
                        line.product_id.display_name,
                        delivered_qty,
                        line.quantity,
                    )
                )

        return super().action_create_returns()