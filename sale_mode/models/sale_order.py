from odoo import models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_open_merge_wizard(self):
        if len(self) < 2:
            raise ValidationError("Please select at least two quotations.")

        if self.filtered(lambda o: o.state not in ("draft", "sent")):
            raise ValidationError("Only Draft and Quotation Sent orders can be merged.")

        if len(self.mapped("partner_id")) > 1:
            raise ValidationError("You can merge only quotations of the same customer.")

        return {
            "type": "ir.actions.act_window",
            "name": "Merge Orders",
            "res_model": "sale.order.merge.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_source_order_ids": [(6, 0, self.ids)],
                "default_target_order_id": self[0].id,
            },
        }