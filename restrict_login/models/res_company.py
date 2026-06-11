from odoo import fields, models

class ResCompany(models.Model):
    _inherit = "res.company"

    restrict_multiple_login = fields.Boolean(
        string="Restrict Multiple Login",
    )

    force_new_login = fields.Boolean(
        string="Force New Login",
    )