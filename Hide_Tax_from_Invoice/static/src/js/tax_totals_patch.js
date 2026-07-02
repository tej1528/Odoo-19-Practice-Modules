/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { onWillStart } from "@odoo/owl";
import { user } from "@web/core/user";
import { TaxTotalsComponent } from "@account/components/tax_totals/tax_totals";

patch(TaxTotalsComponent.prototype, {
    setup() {
        super.setup();

        this.hideTax = false;

        onWillStart(async () => {
            this.hideTax = (await user.hasGroup(
                "Hide_Tax_from_Invoice.group_hide_tax"
            ));
        });
    },

    formatData(props) {
        const totals = JSON.parse(JSON.stringify(props.record.data[props.name] || {}));

        if (!totals.subtotals) {
            this.totals = totals;
            return;
        }

        if (this.hideTax) {
            for (const subtotal of totals.subtotals) {
                subtotal.tax_groups = [];
            }
            totals.has_tax_groups = false;
        }

        this.totals = totals;
    },
});