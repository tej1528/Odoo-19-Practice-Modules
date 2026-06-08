from odoo import api, models
from odoo.fields import Domain

class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "product.search"]

    def _build_term_domain(self, term):
        return (
            super()._build_term_domain(term)
            | Domain("product_variant_ids.default_code","ilike",term,)
            | Domain("product_variant_ids.barcode","ilike",term,)
        )

    def _get_exact_match_domain(self, search_value):
        return (
            super()._get_exact_match_domain(search_value)
            | Domain("product_variant_ids.default_code", "=", search_value,)
            | Domain("product_variant_ids.barcode","=",search_value,)
        )

    def _get_display_match_domain(self, search_value):
        return Domain("display_name", "=", search_value)