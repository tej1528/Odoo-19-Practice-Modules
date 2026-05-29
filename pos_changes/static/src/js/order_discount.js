/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
console.log("ORDER DISCOUNT JS LOADED");
patch(PosOrder.prototype, {

    setup() {
        super.setup(...arguments);

        console.log(
            "HAS SERIALIZE:",
            typeof this.serializeForORM
        );

        console.log(
            "HAS EXPORT:",
            typeof this.export_as_JSON
        );
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

    // SAVE IN JSON
    export_as_JSON() {

        const json =
            super.export_as_JSON(...arguments);

        json.global_discount_amount =
            this.global_discount_amount || 0;

        json.global_discount_percentage =
            this.global_discount_percentage || 0;

        return json;
    },

    // RESTORE AFTER REFRESH
    init_from_JSON(json) {

        super.init_from_JSON(...arguments);

        console.log(
            "IMPORT",
            json.global_discount_amount
        );

        this.global_discount_amount =
            json.global_discount_amount || 0;

        this.global_discount_percentage =
            json.global_discount_percentage || 0;
    },

    // RECEIPT DATA
    export_for_printing() {

    const result =
        super.export_for_printing(...arguments);

    result.global_discount_amount =
        this.global_discount_amount || 0;

    result.global_discount_percentage =
        this.global_discount_percentage || 0;

    return result;
},

    // TOTAL AFTER DISCOUNT
    get priceIncl() {

        const originalTotal =
            this.prices.taxDetails.total_amount_no_rounding;

        return Math.max(
            0,
            originalTotal -
            (this.global_discount_amount || 0)
        );
    },

    // PAYMENT TOTAL
    get totalDue() {

        return this.currency.round(
            this.priceIncl
        );
    },

});