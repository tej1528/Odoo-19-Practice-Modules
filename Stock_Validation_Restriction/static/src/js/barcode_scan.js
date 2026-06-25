/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

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
        document.addEventListener("keydown", async (ev) => {
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
                // Only Stock Picking & Return Picking
                if (
                    controller.props?.resModel !== "stock.picking" &&
                    controller.props?.resModel !== "stock.return.picking"
                ) {
                    return;
                }
                try {
                    const modelName = controller.props.resModel;
                    let result;
                    if (modelName === "stock.return.picking") {
                        // Barcode thi product shodho
                        const productIds = await controller.orm.search(
                            "product.product",
                            [["barcode", "=", barcode]]
                        );
                        if (!productIds.length) {
                            controller.notification.add(
                                _t("Barcode not found."),
                                {
                                    type: "danger",
                                }
                            );
                            return;
                        }

                        const productId = productIds[0];
                        const lines =
                            controller.model.root.data.product_return_moves.records;
                        const line = lines.find((l) =>
                            l.data.product_id?.id === productId);

                        if (!line) {
                            controller.notification.add(
                                _t("Product not found in return lines."),
                                {
                                    type: "danger",
                                }
                            );
                            return;
                        }

                        // Current Qty
                        const currentQty = line.data.quantity || 0;
                        // Delivered Qty (move_quantity field)
                        const deliveredQty = line.data.move_quantity || 0;
                        // New Qty after scan
                        const newQty = currentQty + 1;
                        // Scan time validation
                        if (newQty > deliveredQty) {
                            controller.notification.add(
                                _t(
                                    `You cannot return more than delivered quantity.\n\n` +
                                    `Product: ${line.data.product_id.display_name}\n` +
                                    `Delivered Qty: ${deliveredQty}\n` +
                                    `Return Qty: ${newQty}`
                                ),
                                {
                                    title: _t("Validation Error"),
                                    type: "danger",
                                }
                            );
                            return;
                        }

                        // Update quantity
                        await line.update({
                            quantity: newQty,
                        });
                        return;
                    } else {
                        result = await controller.orm.call(
                            "stock.picking",
                            "process_barcode_scan",
                            [
                                [controller.props.resId],
                                barcode,
                            ]
                        );
                    }

                    // Purchase Over Receipt Warning
                    if (result?.warning) {

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

                            if (controller.model?.root) {
                                await controller.model.root.load();
                            }
                        }
                        return;
                    }
                    if (controller.model?.root) {
                        await controller.model.root.load();
                    }
                } catch (error) {
                    const rawMessage =
                        error?.data?.message ||
                        error?.message ||
                        "Barcode Scan Error";

                    // Ordered Quantity Validation
                    if (rawMessage.startsWith("ORDER_QTY_ERROR|")) {
                        const [
                            ,
                            product,
                            orderedQty,
                            enteredQty,
                        ] = rawMessage.split("|");
                        controller.notification.add(
                            `Product: ${product}
Order Qty: ${orderedQty}
Entered Qty: ${enteredQty}`,
                            {
                                title: "You cannot deliver more than ordered quantity",
                                type: "danger",
                            }
                        );
                        return;
                    }

                    // Stock Validation
                    if (rawMessage.startsWith("STOCK_QTY_ERROR|")) {
                        const [
                            ,
                            product,
                            availableQty,
                            enteredQty,
                        ] = rawMessage.split("|");
                        controller.notification.add(
                            `Product: ${product}
Available Qty: ${availableQty}
Entered Qty: ${enteredQty}`,
                            {
                                title: "Not enough stock available",
                                type: "danger",
                            }
                        );
                        return;
                    }

                    controller.notification.add(
                        rawMessage,
                        {
                            title: _t("Validation Error"),
                            type: "danger",
                        }
                    );
                }
                return;
            }
            if (ev.key.length === 1) {
                barcodeBuffer += ev.key;
            }
        });
    },

    destroy() {
        if (activeController === this) {
            activeController = null;
        }
        super.destroy(...arguments);
    },
});