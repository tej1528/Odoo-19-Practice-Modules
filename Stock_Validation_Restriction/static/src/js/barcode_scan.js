/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";

patch(FormController.prototype, {

    setup() {
        super.setup(...arguments);

        this.orm = useService("orm");
        this.barcodeBuffer = "";

        if (window.barcodeScannerAttached) {
            return;
        }

        window.barcodeScannerAttached = true;

        document.addEventListener(
            "keydown",
            async (ev) => {

                if (
                    ev.key === "Shift" ||
                    ev.key === "Control" ||
                    ev.key === "Alt" ||
                    ev.key === "Meta"
                ) {
                    return;
                }

                if (ev.key === "Enter") {

                    const barcode = this.barcodeBuffer.trim();
                    this.barcodeBuffer = "";

                    if (!barcode) {
                        return;
                    }

                    if (
                        this.props?.resModel !== "stock.picking"
                    ) {
                        return;
                    }

                    try {

                        const result = await this.orm.call(
                            "stock.picking",
                            "process_barcode_scan",
                            [
                                [this.props.resId],
                                barcode,
                            ]
                        );

                        console.log(
                            "RPC RESULT =>",
                            result
                        );

                        // No reload
                        // No model.root.load()
                        // Backend quantity update thai gayi che

                    } catch (error) {

                        console.error(
                            "SCAN ERROR =>",
                            error
                        );

                        const message =
                            error?.data?.message ||
                            error?.message ||
                            "Barcode Scan Error";

                        alert(message);
                    }

                    return;
                }

                if (ev.key.length === 1) {
                    this.barcodeBuffer += ev.key;
                }
            }
        );
    },
});