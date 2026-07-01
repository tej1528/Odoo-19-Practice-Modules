/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { TaxTotalsComponent } from "@account/components/tax_totals/tax_totals";

patch(TaxTotalsComponent.prototype, {
    formatData(props) {
        let totals = JSON.parse(JSON.stringify(props.record.data[props.name]));
        if (!totals) {
            this.totals = {};
            return;
        }

        // Hide tax groups if user has hide_tax access
        if (props.record.data.hide_tax) {
            for (const subtotal of totals.subtotals || []) {
                subtotal.tax_groups = [];
            }
            totals.has_tax_groups = false;
        }

        this.totals = totals;
    },
});