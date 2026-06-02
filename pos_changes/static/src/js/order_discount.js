/** @odoo-module **/

console.log("✅ ORDER_DISCOUNT JS LOADED");

import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";

patch(PosOrder.prototype, {

    getCashierName() {

        console.log("🔥 getCashierName CALLED");

        console.log("POS =", this.pos);
        console.log("CONFIG =", this.pos?.config);
        console.log("DEFAULT USER =", this.pos?.config?.default_user_id);
        console.log("USER =", this.user_id);

        return super.getCashierName(...arguments);
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
    },

    export_as_JSON() {

        const json =
            super.export_as_JSON(...arguments);

        json.global_discount_amount =
            this.global_discount_amount || 0;

        json.global_discount_percentage =
            this.global_discount_percentage || 0;

        return json;
    },

    init_from_JSON(json) {

        super.init_from_JSON(...arguments);

        this.global_discount_amount =
            json.global_discount_amount || 0;

        this.global_discount_percentage =
            json.global_discount_percentage || 0;
    },

    export_for_printing() {

        console.log("🔥 EXPORT FOR PRINTING CALLED");

        const result =
            super.export_for_printing(...arguments);

        console.log("🔥 RECEIPT RESULT =", result);

        result.global_discount_amount =
            this.global_discount_amount || 0;

        result.global_discount_percentage =
            this.global_discount_percentage || 0;

        return result;
    },

    get priceIncl() {

        const originalTotal =
            this.prices.taxDetails.total_amount_no_rounding;

        return Math.max(
            0,
            originalTotal -
            (this.global_discount_amount || 0)
        );
    },

    get totalDue() {

        return this.currency.round(
            this.priceIncl
        );
    },

});