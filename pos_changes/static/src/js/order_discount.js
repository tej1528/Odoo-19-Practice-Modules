/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosOrderAccounting } from "@point_of_sale/app/models/accounting/pos_order_accounting";

patch(PosOrderAccounting.prototype, {

    setup() {

        super.setup(...arguments);

        this.global_discount_amount =
            this.global_discount_amount || 0;

        this.global_discount_percentage =
            this.global_discount_percentage || 0;
    },

    setGlobalDiscount(mode, value) {

        const originalTotal =
            this.prices.taxDetails.total_amount_no_rounding;

        if (mode === "amount") {

            this.global_discount_amount = value;
            this.global_discount_percentage = 0;

        } else {

            this.global_discount_percentage = value;

            this.global_discount_amount =
                (originalTotal * value) / 100;
        }

        console.log(
            "FINAL DISCOUNT:",
            this.global_discount_amount
        );
    },

    // MAIN TOTAL
    get priceIncl() {

        const originalTotal =
            this.prices.taxDetails.total_amount_no_rounding;

        return Math.max(
            0,
            originalTotal -
            (this.global_discount_amount || 0)
        );
    },

    // PAYMENT SCREEN
    get totalDue() {

        return this.currency.round(
            this.priceIncl
        );
    },

});