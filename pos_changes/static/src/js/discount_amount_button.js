/** @odoo-module **/

import { patch } from "@web/core/utils/patch";

import { useService } from "@web/core/utils/hooks";

import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";

import { DiscountPopup } from "@pos_changes/js/discount_popup";

patch(ControlButtons.prototype, {

    setup() {

        super.setup();

        // DIALOG SERVICE
        this.dialog = useService("dialog");
    },

    async openAmountDiscountPopup() {

        console.log(" Button Clicked");

        // OPEN POPUP
        this.dialog.add(DiscountPopup, {

            close: (result) => {

                console.log("Popup Closed", result);

                // CANCEL
                if (!result.confirmed) {
                    return;
                }

                // CURRENT ORDER
                const order = this.pos.get_order();

                if (!order) {
                    return;
                }

                // ORIGINAL TOTAL
                const total =
                    order.getTotalWithoutGlobalDiscount();

                if (total <= 0) {

                    alert("Order total is zero");

                    return;
                }

                let percentage = 0;
                let amount = 0;

                const percent =
                    parseFloat(result.payload.percent) || 0;

                const fixedAmount =
                    parseFloat(result.payload.amount) || 0;

                // BOTH FILLED
                if (percent > 0 && fixedAmount > 0) {

                    alert("Use either % OR Amount");

                    return;
                }

                // PERCENT DISCOUNT
                if (percent > 0) {

                    percentage = percent;

                    amount =
                        (total * percent) / 100;
                }

                // FIXED AMOUNT DISCOUNT
                else if (fixedAmount > 0) {

                    amount = fixedAmount;

                    percentage =
                        (fixedAmount / total) * 100;
                }

                else {

                    alert("Enter discount");

                    return;
                }

                // SAVE GLOBAL DISCOUNT
                order.setGlobalDiscount(
                    percentage,
                    amount
                );

                console.log(
                    " Global Discount Applied:",
                    percentage + "%",
                    amount
                );

                // REFRESH UI
                order.trigger("change");

                // NOTIFICATION
                this.pos.notification.add(
                    "Discount Applied Successfully",
                    3000
                );
            },
        });
    },
});