/** @odoo-module **/

import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";
import { useService } from "@web/core/utils/hooks";

export class CustomDiscountNumberPopup extends NumberPopup {
    static template = "pos_changes.CustomDiscountNumberPopup";

    setup() {
        super.setup();
        this.pos = useService("pos");
    }

    getPayload() {
        return {};
    }

    async confirm() {

        const selectedMode =
            document.querySelector(
                'input[name="discount_mode_toggle"]:checked'
            )?.value || "percent";

        const rawValue =
            this.state.buffer
                ? this.state.buffer.toString()
                : "0";

        const value =
            this.env.utils.parseValidFloat(rawValue);

        const order = this.pos.getOrder();

        if (order) {

            order.setGlobalDiscount(
                selectedMode,
                value
            );

            this.pos.selectedOrderUuid =
                this.pos.selectedOrderUuid;
        }
        this.props.close();
    }
}