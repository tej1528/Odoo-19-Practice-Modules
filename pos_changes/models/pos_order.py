from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = "pos.order"

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

    amount_untaxed = fields.Monetary(
        string="Untaxed Amount",
        compute="_compute_amount_untaxed",
        currency_field="currency_id",
        store=True,
    )

    @api.depends(
        "global_discount_amount",
        "global_discount_percentage"
    )
    def _compute_discount_display(self):
        for order in self:

            if order.global_discount_amount:

                amount = f"${order.global_discount_amount:,.2f}"

                if order.global_discount_percentage > 0:
                    order.discount_display = (
                        f"{amount} ({order.global_discount_percentage:.0f}%)"
                    )
                else:
                    order.discount_display = amount

            else:
                order.discount_display = ""

    @api.depends('lines.price_subtotal')
    def _compute_amount_untaxed(self):
        for order in self:
            order.amount_untaxed = sum(
                line.price_subtotal
                for line in order.lines
            )

    @classmethod
    def _order_fields(cls, ui_order):

        vals = super()._order_fields(ui_order)

        session_id = vals.get("session_id")

        if session_id:

            from odoo import api, SUPERUSER_ID

            env = api.Environment(
                cls._cr,
                SUPERUSER_ID,
                {}
            )

            session = env["pos.session"].browse(session_id)

            if session.config_id.default_user_id:
                vals["user_id"] = (
                    session.config_id.default_user_id.id
                )

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

    @api.model
    def create(self, vals):
        order = super().create(vals)

        default_cashier = (
            order.session_id.config_id.default_user_id
        )

        if default_cashier:
            order.write({
                "user_id": default_cashier.id,
            })

        return order