from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    size_chart_id = fields.Many2one(
        comodel_name="product.size.chart",
        string="Size Chart",
        help="Select the size chart to display on the website.",
    )