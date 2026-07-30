from odoo import models
from odoo.exceptions import UserError
from odoo import _
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    def _send_payment_notification(self, amount):

        group = self.env.ref("account.group_account_manager",raise_if_not_found=False)

        if group:
            users = group.user_ids.filtered(
                lambda u: u != self.env.user
                )

            action = {
                "type": "ir.actions.act_window",
                "res_model": "account.move",
                "target": "current",
            }

            if len(self) == 1:
                action.update({
                    "res_id": self.id,
                    "views": [(False, "form")],
                })
                invoice_name = self.name
            else:
                action.update({
                    "name": "Invoices",
                    "views": [(False, "list"), (False, "form")],
                    "domain": [("id", "in", self.ids)],
                })
                invoice_name = ", ".join(self.mapped("name"))

            for user in users:
                
                    self.env["bus.bus"]._sendone(
                        user.partner_id,
                        "payment_registered",
                        {
                            "invoice_name": invoice_name,
                            "registered_by": self.env.user.name,
                            "amount": amount,
                            "action": action,
                        },
                    )
            