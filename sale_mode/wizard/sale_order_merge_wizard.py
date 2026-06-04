from odoo import models, fields
from odoo.exceptions import ValidationError
from odoo.fields import Command


class SaleOrderMergeWizard(models.TransientModel):
    _name = "sale.order.merge.wizard"
    _description = "Sale Order Merge Wizard"

    source_order_ids = fields.Many2many(
        "sale.order",
        string="Orders"
    )

    merge_type = fields.Selection(
        [
            ("existing", "Existing Order"),
            ("new", "Create New Order"),
        ],
        string="Merge Type",
        default="existing",
        required=True,
    )

    target_order_id = fields.Many2one(
        "sale.order",
        string="Merge Into",
        domain="[('id', 'in', source_order_ids)]",
    )

    delete_source = fields.Boolean(
        string="Delete Source Orders",
        default=True,
    )

    def _get_target_order(self, orders):
        
        if self.merge_type == "existing":

            if not self.target_order_id:
                raise ValidationError("Please select target quotation.")

            return self.target_order_id

        return self.env["sale.order"].create({
            "partner_id": orders[0].partner_id.id,
        })

    def action_merge(self):
        self.ensure_one()

        orders = self.source_order_ids

        if len(orders) < 2:
            raise ValidationError("Please select at least two quotations.")

        if orders.filtered(
            lambda o: o.state not in ("draft", "sent")
        ):
            raise ValidationError("Only Draft and Quotation Sent orders can be merged.")

        if len(orders.mapped("partner_id")) > 1:
            raise ValidationError("Customer must be same for all quotations.")

        target_order = self._get_target_order(orders)

        source_orders = orders.filtered(
            lambda o: o.id != target_order.id
        )

        # Store names before delete
        merged_names = source_orders.mapped("name")

        for order in source_orders:

            for line in order.order_line.filtered(
                lambda l: not l.display_type
            ):

                existing_line = target_order.order_line.filtered(
                    lambda l:
                    not l.display_type
                    and l.product_id == line.product_id
                    and l.price_unit == line.price_unit
                    and l.discount == line.discount
                    and set(l.tax_ids.ids) == set(line.tax_ids.ids)
                )

                if existing_line:

                    existing_line.product_uom_qty += (
                        line.product_uom_qty
                    )

                else:

                    target_order.write({
                        "order_line": [
                            Command.create({
                                "product_id": line.product_id.id,
                                "name": line.name,
                                "product_uom_qty": line.product_uom_qty,
                                "price_unit": line.price_unit,
                                "discount": line.discount,
                                "tax_ids": [
                                    Command.set(line.tax_ids.ids)
                                ],
                            })
                        ]
                    })

        # Delete after merge completed
        if self.delete_source:

            for order in source_orders:

                if order.state == "sent":
                    order.action_cancel()

                order.unlink()

        target_order.message_post(
            body="Merged quotations: %s" %
            ", ".join(merged_names)
        )

        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }