/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { CustomDiscountNumberPopup } from "@pos_changes/js/custom_discount_number_popup";
import { patch } from "@web/core/utils/patch";

patch(ControlButtons.prototype, {
    async clickDiscount() {
        console.log("Opening Custom Discount Popup...");

        if (!this.pos) {
            console.error("POS service not found on this component context.");
            return;
        }

        this.dialog.add(CustomDiscountNumberPopup, {
            title: _t("Global Discount"),
            startingValue: this.pos.config?.discount_pc || 0,
        });
    },
});