/** @odoo-module **/

import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";
import { useService } from "@web/core/utils/hooks";

export class CustomDiscountNumberPopup extends NumberPopup {
    static template = "pos_changes.CustomDiscountNumberPopup";

    setup() {
        super.setup();
        this.pos = useService("pos");
    }

    async confirm() {
        const selectedMode = document.querySelector('input[name="discount_mode_toggle"]:checked')?.value || 'percent';
        const rawValue = this.state.buffer ? this.state.buffer.toString() : "0";
        const value = this.env.utils.parseValidFloat(rawValue);

        console.log(`|| Executing Direct Discount || Mode: ${selectedMode}, Value: ${value}`);

        // ઓડુ ૧૯ માં એક્ટિવ ઓર્ડર મેળવવાની સાચી રીત
        const order = this.pos?.getOrder();

        if (order) {
            // જો પહેલાથી કોઈ કસ્ટમ ડિસ્કાઉન્ટ પ્રોપર્ટી બનાવેલી હોય તો તેને રીસેટ કરો
            if (!order.originalPriceIncl) {
                order.originalPriceIncl = order.priceIncl;
                order.originalPriceExcl = order.priceExcl;
                order.originalAmountTaxes = order.amountTaxes;
            }

            let discountAmount = 0;

            if (selectedMode === "amount") {
                // ડાયરેક્ટ રકમ (Fixed Amount) માઇનસ કરો
                discountAmount = value;
            } else {
                // ટકાવારી (%) ના આધારે રકમ શોધો
                discountAmount = (order.originalPriceIncl * value) / 100;
            }

            console.log(`Calculated Discount Amount to Deduct: ${discountAmount}`);

            // ૧. કોઈ નવી લાઇન ઉમેર્યા વગર ડાયરેક્ટ ઓફિશિયલ વેરિએબલ્સ અપડેટ કરો
            order.priceIncl = Math.max(0, order.originalPriceIncl - discountAmount);

            // પ્રોપોર્શનલ ટેક્સ અને એક્સક્લુઝિવ પ્રાઈઝ સેટ કરો (ઓડુ કેલ્ક્યુલેશન સેફ્ટી માટે)
            const ratio = order.originalPriceIncl > 0 ? (order.priceIncl / order.originalPriceIncl) : 0;
            order.priceExcl = order.originalPriceExcl * ratio;
            order.amountTaxes = order.originalAmountTaxes * ratio;

            // ૨. આખા POS સ્ક્રીન (UI) ને નવું ટોટલ બતાવવા માટે ફોર્સ રી-રેન્ડર ટ્રિગર કરો
            order.trigger("change");

            console.log("New Totals Updated Directly -> PriceIncl:", order.priceIncl);

        } else {
            console.error("No active order found to apply direct discount.");
        }

        this.props.close();
    }
}