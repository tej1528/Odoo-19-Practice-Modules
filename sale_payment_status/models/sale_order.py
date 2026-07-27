# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.fields import Date
from odoo.exceptions import AccessError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    payment_status = fields.Selection(
        selection=[
            ("no_invoice", "No Invoice"),
            ("not_paid", "Not Paid"),
            ("partial_paid", "Partial Paid"),
            ("overdue", "Overdue"),
            ("fully_paid", "Fully Paid"),
        ],
        string="Payment Status",
        compute="_compute_payment_status",
        store=True,
        readonly=True,
        copy=False,
    )

    amount_due = fields.Monetary(
        string="Amount Due",
        currency_field="currency_id",
        compute="_compute_payment_info",
        store=True,
        readonly=True,
    )

    show_register_payment = fields.Boolean(
        string="Show Register Payment",
        compute="_compute_show_register_payment",
    )

    invoiced_amount = fields.Monetary(
        string="Invoiced Amount",
        currency_field="currency_id",
        compute="_compute_payment_info",
        store=True,
        readonly=True,
    )

    paid_amount = fields.Monetary(
        string="Paid Amount",
        currency_field="currency_id",
        compute="_compute_payment_info",
        store=True,
        readonly=True,
    )

    # ============================================================
    # Payment Status
    # ============================================================

    @api.depends("state", "amount_total", "invoice_ids", "invoice_ids.state", "invoice_ids.move_type", "invoice_ids.payment_state",
        "invoice_ids.amount_total", "invoice_ids.amount_residual", "invoice_ids.invoice_date_due",
    )
    def _compute_payment_status(self):
        today = Date.context_today(self)

        for order in self:

            # Do not show payment status
            if order.state not in ("sale", "done"):
                order.payment_status = False
                continue

            # Get customer invoices only
            customer_invoices = order.invoice_ids.filtered(
                lambda invoice:
                    invoice.move_type == "out_invoice"
                    and invoice.state != "cancel"
            )

            if not customer_invoices:
                order.payment_status = "no_invoice"
                continue

            # Posted invoices only
            posted_invoices = customer_invoices.filtered(
                lambda invoice: invoice.state == "posted"
            )

            if not posted_invoices:
                order.payment_status = "not_paid"
                continue

            invoice_total = sum(
                posted_invoices.mapped("amount_total")
            )

            residual_total = sum(
                posted_invoices.mapped("amount_residual")
            )

            paid_total = invoice_total - residual_total

            if (
                paid_total >= order.amount_total
                and residual_total <= 0
            ):
                order.payment_status = "fully_paid"
                continue

            # ----------------------------------------------------
            # OVERDUE
            # ----------------------------------------------------
            overdue_invoices = posted_invoices.filtered(
                lambda invoice:
                    invoice.amount_residual > 0
                    and invoice.invoice_date_due
                    and invoice.invoice_date_due < today
            )

            if overdue_invoices:
                order.payment_status = "overdue"
                continue

            if paid_total > 0:
                order.payment_status = "partial_paid"
                continue

            order.payment_status = "not_paid"

    # ============================================================
    # Register Payment Button Visibility
    # ============================================================

    @api.depends( "state", "invoice_ids", "invoice_ids.state", "invoice_ids.move_type",
        "invoice_ids.amount_residual",
    )
    def _compute_show_register_payment(self):
        is_account_admin = self.env.user.has_group(
            "account.group_account_manager"
        )
        for order in self:
            if not is_account_admin:
                order.show_register_payment = False
                continue

            # Quotation / Quotation Sent
            if order.state not in ("sale", "done"):
                order.show_register_payment = False
                continue

            # Button is shown only when a posted customer invoice
            # exists and that invoice still has an outstanding amount.
            payable_invoices = order.invoice_ids.filtered(
                lambda invoice:
                    invoice.state == "posted"
                    and invoice.move_type == "out_invoice"
                    and invoice.amount_residual > 0
            )
            order.show_register_payment = bool(payable_invoices)

    # ============================================================
    # Register Payment
    # ============================================================

    def action_register_payment(self):
        self.ensure_one()
        if not self.env.user.has_group("account.group_account_manager"):
            raise AccessError(
                "Only Accounting Administrators can register payments from Sale Orders.")

        invoices = self.invoice_ids.filtered(
            lambda invoice:
                invoice.state == "posted"
                and invoice.move_type == "out_invoice"
                and invoice.amount_residual > 0
        )

        if not invoices:
            return False

        return {
            "type": "ir.actions.act_window",
            "name": "Register Payment",
            "res_model": "account.payment.register",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_model": "account.move",
                "active_ids": invoices.ids,
            },
        }

    @api.depends("state", "invoice_ids", "invoice_ids.state", "invoice_ids.move_type",
    "invoice_ids.amount_total", "invoice_ids.amount_residual", "invoice_ids.payment_state",
    )
    def _compute_payment_info(self):
        for order in self:

            order.invoiced_amount = 0.0
            order.paid_amount = 0.0
            order.amount_due = 0.0

            if order.state not in ("sale", "done"):
                continue

            posted_invoices = order.invoice_ids.filtered(
                lambda move:
                    move.state == "posted"
                    and move.move_type == "out_invoice"
            )

            posted_credit_notes = order.invoice_ids.filtered(
                lambda move:
                    move.state == "posted"
                    and move.move_type == "out_refund"
            )

            invoice_total = sum(
                posted_invoices.mapped("amount_total")
            )

            credit_note_total = sum(
                posted_credit_notes.mapped("amount_total")
            )

            net_invoiced_amount = max(
                invoice_total - credit_note_total,
                0.0,
            )

            # =========================================================
            # Find ACTUAL payments
            # =========================================================
            actual_paid_amount = 0.0

            for invoice in posted_invoices:

                receivable_lines = invoice.line_ids.filtered(
                    lambda line:
                        line.account_id.account_type == "asset_receivable"
                )

                for line in receivable_lines:

                    partials = (
                        line.matched_debit_ids
                        | line.matched_credit_ids
                    )

                    for partial in partials:

                        # Find opposite reconciled line
                        if partial.debit_move_id == line:
                            counterpart_line = partial.credit_move_id
                        else:
                            counterpart_line = partial.debit_move_id

                        counterpart_move = counterpart_line.move_id
                        # Payment journal entry(Customer Invoice,Credit Note, Payment )

                        if counterpart_move.move_type == "entry":
                            actual_paid_amount += partial.amount

            # =========================================================
               # Actual Payment - Credit Note
            # =========================================================
            net_paid_amount = max(
                actual_paid_amount - credit_note_total,
                0.0,
            )

            # =========================================================
            # Amount Due
            # Sale Order Total - Net Paid
            # =========================================================
            amount_due = max(
                order.amount_total - net_paid_amount,
                0.0,
            )

            # =========================================================
            # Final Values
            # =========================================================
            order.invoiced_amount = net_invoiced_amount
            order.paid_amount = net_paid_amount
            order.amount_due = amount_due