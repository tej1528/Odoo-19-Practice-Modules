from odoo import fields, models


class ProductSizeChart(models.Model):
    _name = "product.size.chart"
    _description = "Product Size Chart"
    _order = "name"

    name = fields.Char(string="Name", required=True)
    description = fields.Html(string="Description", sanitize=False)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    size_chart_id = fields.Many2one(
        comodel_name="product.size.chart",
        string="Size Chart",
        help="Select the size chart to display on the website.",
    )