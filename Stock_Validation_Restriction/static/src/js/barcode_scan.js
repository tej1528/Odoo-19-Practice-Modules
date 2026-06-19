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
        this.notification = useService("notification");
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
                        // Purchase over receipt confirmation
                        if (result.warning) {
                            const confirmQty = confirm(
                                `Ordered Qty: ${result.ordered_qty}
Current Qty: ${result.current_qty}
Entered Quantity: ${result.new_qty}
Do you want to continue?`
                            );
                            if (confirmQty) {
                                await controller.orm.call(
                                    "stock.picking",
                                    "force_barcode_scan",
                                    [
                                        [controller.props.resId],
                                        barcode,
                                    ]
                                );
                                if (
                                    controller.model &&
                                    controller.model.root
                                ) {
                                    await controller.model.root.load();
                                }
                            }
                            return;
                        }
                        if (
                            controller.model &&
                            controller.model.root
                        ) {
                            await controller.model.root.load();
                        }
                    } catch (error) {

                        const rawMessage =
                            error?.data?.message ||
                            error?.message ||
                            "Barcode Scan Error";

                        const formattedMessage = rawMessage
                            .replace(/\n/g, "<br/>");

                        controller.notification.add(
                            formattedMessage,
                            {
                                title: "Validation Error",
                                type: "danger",
                                sticky: true,
                            }
                        );

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