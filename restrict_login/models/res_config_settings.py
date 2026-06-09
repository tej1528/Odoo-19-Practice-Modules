from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    restrict_multiple_login = fields.Boolean(
        string="Restrict Multiple Login",
        config_parameter="restrict_login.restrict_multiple_login",
    )

    force_new_login = fields.Boolean(
        string="Force New Login",
        config_parameter="restrict_login.force_new_login",
    )