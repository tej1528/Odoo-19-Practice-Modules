from odoo import models

class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def action_create_payments(self):
        amount = self.amount
        res = super().action_create_payments()

        if not self.env.context.get("send_payment_notification"):
            return res

        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids", False)

        if active_model == "account.move" and active_ids:
            invoices = self.env["account.move"].browse(active_ids)

            if invoices:
                invoices._send_payment_notification(amount)

        return res