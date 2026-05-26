/** @odoo-module **/

import { ReceiptHeader } from "@point_of_sale/app/screens/receipt_screen/receipt/receipt_header/receipt_header";

import { patch } from "@web/core/utils/patch";

patch(ReceiptHeader.prototype, {

    get cashierName() {

        const order = this.props.order;

        if (order && order.cashier_final) {
            return order.cashier_final;
        }

        return "";
    },

    get discountValue() {

        const order = this.props.data;

        return order.global_discount_percentage || 0;
    },

    get discountAmount() {

        const order = this.props.data;

        return order.global_discount_amount || 0;
    },
});