from odoo import api, models
from odoo.fields import Domain


class ProductSearchMixin(models.AbstractModel):
    _name = "product.search"
    _description = "Product Search Mixin"

    def _build_term_domain(self, term):
        return (
            Domain("name", "ilike", term)
            | Domain("default_code", "ilike", term)
            | Domain("barcode", "ilike", term)
        )

    def _get_exact_match_domain(self, search_value):
        return (
            Domain("default_code", "=", search_value)
            | Domain("barcode", "=", search_value)
        )

    def _get_display_match_domain(self, search_value):
        return Domain.FALSE

    def _process_search_domain(self, domain):
        domain = domain or []
        new_domain = []

        for item in domain:
            if (
                isinstance(item, (list, tuple))
                and len(item) == 3
                and item[0] == "name"
                and item[1] == "ilike"
                and item[2]
            ):
                search_value = item[2].strip()

                exact_record = self.search(
                    self._get_display_match_domain(search_value)
                    | self._get_exact_match_domain(search_value),
                    limit=1,
                )

                if exact_record:
                    new_domain.append(("id", "=", exact_record.id))
                    continue

                terms = [
                    t.replace("[", "").replace("]", "")
                    for t in search_value.split()
                    if t.strip()
                ]

                if len(terms) > 1:
                    and_domain = Domain.AND(
                        [self._build_term_domain(term) for term in terms]
                    )

                    if self.search(and_domain, limit=1):
                        new_domain.extend(list(and_domain))
                    else:
                        or_domain = Domain.OR(
                            [self._build_term_domain(term) for term in terms]
                        )
                        new_domain.extend(list(or_domain))

                    continue

            new_domain.append(item)

        return new_domain

    @api.model
    def web_search_read(self, domain=None, specification=None, offset=0, limit=None, order=None, count_limit=None,):
        return super().web_search_read(
            domain=self._process_search_domain(domain),
            specification=specification,
            offset=offset,
            limit=limit,
            order=order,
            count_limit=count_limit,
        )