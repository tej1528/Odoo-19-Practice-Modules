from odoo import api, models
from odoo.fields import Domain

class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "product.search"]

    def _build_term_domain(self, term):
        return (super()._build_term_domain(term)
            | Domain("product_template_attribute_value_ids.name","ilike",term,)
        )

    def _get_display_match_domain(self, search_value):
        return Domain("display_name", "=", search_value)