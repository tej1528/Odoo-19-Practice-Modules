/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";

let barcodeBuffer = "";
let activeController = null;

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        activeController = this;
        if (window.barcodeScannerInitialized) {
            return;
        }
        window.barcodeScannerInitialized = true;
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
                    const barcode = barcodeBuffer.trim();
                    barcodeBuffer = "";
                    if (!barcode) {
                        return;
                    }
                    const controller = activeController;
                    if (!controller) {
                        return;
                    }
                    if (
                        controller.props?.resModel !== "stock.picking"
                    ) {
                        return;
                    }
                    try {
                        const result = await controller.orm.call(
                            "stock.picking",
                            "process_barcode_scan",
                            [
                                [controller.props.resId],
                                barcode,
                            ]
                        );
                        console.log("RPC RESULT =>", result);
                        if (
                            controller.model &&
                            controller.model.root
                        ) {
                            await controller.model.root.load();
                        }

                    } catch (error) {
                        console.error("SCAN ERROR =>", error);
                        const message =
                            error?.data?.message ||
                            error?.message ||
                            "Barcode Scan Error";
                        alert(message);
                    }
                    return;
                }
                if (ev.key.length === 1) {
                    barcodeBuffer += ev.key;
                }
            }
        );
    },

    destroy() {
        if (activeController === this) {
            activeController = null;
        }
        super.destroy(...arguments);
    },
});