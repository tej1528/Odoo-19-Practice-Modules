# -*- coding: utf-8 -*-

from odoo import api, fields, models
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
        compute="_compute_payment_info",
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
    # Payment Info Computation based on Sale Order Total
    # ============================================================
    @api.depends(
        "state",
        "amount_total",
        "invoice_ids",
        "invoice_ids.state",
        "invoice_ids.move_type",
        "invoice_ids.payment_state",
        "invoice_ids.amount_total_in_currency_signed",
        "invoice_ids.amount_residual_signed",
        "invoice_ids.invoice_date_due",
    )
    def _compute_payment_info(self):
        today = fields.Date.context_today(self)

        for order in self:
            #If the Sale Order is not confirmed (sale/done)
            if order.state not in ("sale", "done"):
                order.payment_status = False
                order.invoiced_amount = 0.0
                order.paid_amount = 0.0
                order.amount_due = 0.0
                continue

            # To filter only POSTED invoices
            valid_moves = order.invoice_ids.filtered(
                lambda m: m.state == "posted"
                and m.move_type in ("out_invoice", "out_refund")
            )

            # If there is no Confirmed / Posted invoice -> No Invoice
            if not valid_moves:
                order.payment_status = "no_invoice"
                order.invoiced_amount = 0.0
                order.paid_amount = 0.0
                order.amount_due = order.amount_total
                continue

            # Calculation of Invoiced, Residual, and Paid amounts
            total_invoiced = sum(valid_moves.mapped("amount_total_in_currency_signed"))
            total_residual = sum(valid_moves.mapped("amount_residual_signed"))

            order.invoiced_amount = max(total_invoiced, 0.0)
            order.paid_amount = max(total_invoiced - total_residual, 0.0)
            order.amount_due = max(order.amount_total - order.paid_amount, 0.0)

            # fully_paid
            if order.amount_due <= 0 and order.paid_amount > 0:
                order.payment_status = "fully_paid"
            else:
                #  Overdue 
                has_overdue = any(
                    inv.move_type == "out_invoice"
                    and inv.amount_residual > 0
                    and inv.invoice_date_due
                    and inv.invoice_date_due < today
                    for inv in valid_moves
                )

                if has_overdue:
                    order.payment_status = "overdue"
                elif order.paid_amount > 0:
                    order.payment_status = "partial_paid"
                else:
                    order.payment_status = "not_paid"

    # ============================================================
    # Register Payment Action
    # ============================================================
    def action_register_payment(self):
        self.ensure_one()

        if not self.env.user.has_group("account.group_account_manager"):
            raise AccessError(
                "Only Accounting Administrators can register payments from Sale Orders."
            )

        invoices = self.invoice_ids.filtered(
            lambda invoice: invoice.state == "posted"
            and invoice.move_type in ("out_invoice", "out_refund")
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