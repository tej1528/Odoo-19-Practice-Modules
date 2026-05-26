from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit = "pos.order"
    cashier_final = fields.Char(string="Cashier")

    @api.model
    def create(self, vals):
        order = super().create(vals)

        if order.session_id.config_id.default_user_id:
            order.cashier_final = order.session_id.config_id.default_user_id.name

        return order