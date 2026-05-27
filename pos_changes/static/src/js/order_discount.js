/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";

patch(PosOrder.prototype, {
    setup() {
        super.setup(...arguments);
        this.global_discount_percentage = 0;
        this.global_discount_amount = 0;
    },
    setGlobalDiscount(percent, amount) {
        this.global_discount_percentage = percent || 0;
        this.global_discount_amount = amount || 0;
        this.trigger("change");
    },
    get_total_with_tax() {
        const total = super.get_total_with_tax();
        return total - (this.global_discount_amount || 0);
    },
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.global_discount_percentage = this.global_discount_percentage;
        json.global_discount_amount = this.global_discount_amount;
        return json;
    },
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.global_discount_percentage = json.global_discount_percentage || 0;
        this.global_discount_amount = json.global_discount_amount || 0;
    },
});