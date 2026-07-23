from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _notify_get_recipients(self, message, msg_vals=False, **kwargs):
        recipients = super()._notify_get_recipients(
            message,
            msg_vals=msg_vals,
            **kwargs,
        )

        if self.env.context.get("approval_request_only_managers") or \
           self.env.context.get("mail_only_explicit_partners"):

            partner_ids = set(
                (msg_vals or {}).get("partner_ids")
                or message.partner_ids.ids
            )

            recipients = [
                r for r in recipients
                if not r.get("id") or r["id"] in partner_ids
            ]

        return recipients