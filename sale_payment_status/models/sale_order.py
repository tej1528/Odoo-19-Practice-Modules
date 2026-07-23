# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.fields import Date

class SaleOrder(models.Model):
    _inherit = "sale.order"

    payment_status = fields.Selection(
        [
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
        compute="_compute_amount_due",
        store=True,
        readonly=True,
    )

    @api.depends("invoice_ids", "invoice_ids.payment_state", "invoice_ids.move_type", "invoice_ids.amount_residual", "invoice_ids.invoice_date_due", "invoice_ids.state",)
    def _compute_payment_status(self):
        today = Date.today()
        for order in self:

            invoices = order.invoice_ids.filtered(
                lambda inv: inv.state == "posted"
                and inv.move_type == "out_invoice"
            )

            if not invoices:
                order.payment_status = "no_invoice"
                continue

            if all(inv.payment_state == "paid" for inv in invoices):
                order.payment_status = "fully_paid"
                continue

            overdue = invoices.filtered(
                lambda inv:
                    inv.amount_residual > 0
                    and inv.invoice_date_due
                    and inv.invoice_date_due < today
            )

            if overdue:
                order.payment_status = "overdue"
                continue

            partial = invoices.filtered(
                lambda inv: inv.payment_state == "partial"
            )

            if partial:
                order.payment_status = "partial_paid"
            else:
                order.payment_status = "not_paid"

    @api.depends("invoice_ids.amount_residual","invoice_ids.state", )
    def _compute_amount_due(self):

        for order in self:

            invoices = order.invoice_ids.filtered(
                lambda inv: inv.state == "posted"
                and inv.move_type == "out_invoice"
            )

            order.amount_due = sum(
                invoices.mapped("amount_residual")
            )