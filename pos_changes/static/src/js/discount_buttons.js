/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { CustomDiscountNumberPopup } from "@pos_changes/js/custom_discount_number_popup";
import { patch } from "@web/core/utils/patch";

patch(ControlButtons.prototype, {

    async clickCustomDiscount() {

        if (!this.pos) {
            return;
        }

        this.dialog.add(CustomDiscountNumberPopup, {
            title: _t("Global Discount"),
            startingValue: 0,
        });
    },

});