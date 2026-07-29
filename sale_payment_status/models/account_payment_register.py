from odoo import models

class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def action_create_payments(self):
        amount = self.amount
        res = super().action_create_payments()

        # Send notification only when context flag is True
        if not self.env.context.get("send_payment_notification"):
            return res

        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids", [])

        invoices = self.env["account.move"]
        if active_model == "account.move":
            invoices = self.env["account.move"].browse(active_ids)
        elif active_model == "account.move.line":
            invoices = self.env["account.move.line"].browse(active_ids).mapped("move_id")

        invoices = invoices.exists()
        sale_orders = invoices.mapped("line_ids.sale_line_ids.order_id")

        if sale_orders:
            sale_orders._send_payment_notification(amount, invoices)

        return res