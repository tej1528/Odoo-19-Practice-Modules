from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = "pos.order"

    cashier_final = fields.Char(string="Cashier")

    global_discount_amount = fields.Float(
        string="Global Discount Amount",
        default=0.0
    )

    global_discount_percentage = fields.Float(
        string="Global Discount Percentage",
        default=0.0
    )

    discount_display = fields.Char(
        string="Discount",
        compute="_compute_discount_display",
    )

    @api.depends(
    "global_discount_amount",
    "global_discount_percentage"
)
    def _compute_discount_display(self):

        for order in self:

            if order.global_discount_amount:

                order.discount_display = (
                    f"Discount ({order.global_discount_percentage:.0f}%) : "
                    f"{order.global_discount_amount:.2f}"
                )

            else:
                order.discount_display = ""

    @api.model
    def create(self, vals):

        order = super().create(vals)

        if order.session_id.config_id.default_user_id:
            order.cashier_final = (
                order.session_id.config_id.default_user_id.name
            )

        return order

    @classmethod
    def _order_fields(cls, ui_order):

        vals = super()._order_fields(ui_order)

        vals.update({
            "global_discount_amount":
                ui_order.get(
                    "global_discount_amount",
                    0.0
                ),

            "global_discount_percentage":
                ui_order.get(
                    "global_discount_percentage",
                    0.0
                ),
        })

        return vals