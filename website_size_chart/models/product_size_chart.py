from odoo import fields, models


class ProductSizeChart(models.Model):
    _name = "product.size.chart"
    _description = "Product Size Chart"
    _order = "name"

    name = fields.Char(string="Name", required=True)
    description = fields.Html(string="Description", sanitize=False)