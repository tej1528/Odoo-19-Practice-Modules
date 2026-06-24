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

        console.log("BARCODE PATCH LOADED");

        if (window.barcodeScannerInitialized) {
            console.log("BARCODE LISTENER ALREADY INITIALIZED");
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

                console.log("ENTER PRESSED");

                const barcode = barcodeBuffer.trim();

                console.log("BARCODE =>", barcode);

                barcodeBuffer = "";

                if (!barcode) {
                    console.log("EMPTY BARCODE");
                    return;
                }

                const controller = activeController;

                console.log("ACTIVE CONTROLLER =>", controller);

                if (!controller) {
                    console.log("NO CONTROLLER");
                    return;
                }

                console.log(
                    "MODEL =>",
                    controller.props?.resModel
                );

                console.log(
                    "RES ID =>",
                    controller.props?.resId
                );

                console.log(
                    "ROOT RES ID =>",
                    controller.model?.root?.resId
                );

                console.log(
                    "ROOT DATA =>",
                    controller.model?.root?.data
                );

                console.log(
                    "PICKING FIELD =>",
                    controller.model?.root?.data?.picking_id
                );

                console.log(
                    "RETURN LINES =>",
                    controller.model?.root?.data?.product_return_moves
                );

                console.log(
                    "RETURN LINES RAW =>",
                    controller.model?.root?.data?.product_return_moves?.records
                );
                console.log(
                    "FIRST RETURN LINE =>",
                    controller.model?.root?.data?.product_return_moves?.records?.[0]
                );

                console.log(
                    "FIRST RETURN LINE DATA =>",
                    controller.model?.root?.data?.product_return_moves?.records?.[0]?.data
                );

                console.log(
                    "PRODUCT OBJECT =>",
                    controller.model?.root?.data?.product_return_moves?.records?.[0]?.data?.product_id
                );

                console.log(
                    "MOVE ID =>",
                    controller.model?.root?.data?.product_return_moves?.records?.[0]?.data?.move_id
                );

                console.log(
                    "LINE RECORD ID =>",
                    controller.model?.root?.data?.product_return_moves?.records?.[0]?.resId
                );

                console.log(
                    "LINE DATAPOINT =>",
                    controller.model?.root?.data?.product_return_moves?.records?.[0]?.id
                );
                console.log(
                    "LINE METHODS =>",
                    Object.getOwnPropertyNames(
                        Object.getPrototypeOf(
                            controller.model?.root?.data?.product_return_moves?.records?.[0]
                        )
                    )
                );

                console.log(
                    "PRODUCT ID =>",
                    controller.model?.root?.data?.product_return_moves?.records?.[0]?.data?.product_id
                );

                console.log(
                    "ROOT KEYS =>",
                    Object.keys(controller.model?.root?.data || {})
                );

                console.log(
                    "ROOT OBJECT =>",
                    controller.model?.root);

                console.log(
                    "MODEL OBJECT =>",
                    controller.model
                );
                if (
                    ![
                        "stock.picking",
                        "stock.return.picking",
                    ].includes(controller.props?.resModel)
                ) {
                    console.log(
                        "MODEL NOT SUPPORTED =>",
                        controller.props?.resModel
                    );
                    return;
                }

                try {

                    let result;

                    if (
                        controller.props.resModel ===
                        "stock.return.picking"
                    ) {

                        console.log("INSIDE RETURN WIZARD");

                        const pickingId =
                            controller.model?.root?.data?.picking_id?.id;

                        console.log("PICKING ID =>", pickingId);

                        if (!pickingId) {
                            console.log("PICKING ID NOT FOUND");
                            return;
                        }

                        result = await controller.orm.call(
                            "stock.picking",
                            "process_return_barcode",
                            [
                                [pickingId],
                                barcode,
                            ]
                        );

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

                    if (result?.warning) {

                        console.log(
                            "WARNING RESULT =>",
                            result
                        );

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
                                controller.render(true);
                            }
                        }

                        return;
                    }

                    console.log(
                        "RELOADING VIEW"
                    );

                    if (controller.model?.root) {
                        await controller.model.root.load();
                        controller.render(true);
                    }

                } catch (error) {

                    console.error(
                        "FULL ERROR =>",
                        error
                    );

                    const rawMessage =
                        error?.data?.message ||
                        error?.message ||
                        "Barcode Scan Error";

                    console.log(
                        "RAW MESSAGE =>",
                        rawMessage
                    );

                    if (rawMessage.startsWith("RETURN_QTY_ERROR|")) {

                        const [
                            ,
                            product,
                            deliveredQty,
                            returnQty,
                        ] = rawMessage.split("|");

                        controller.notification.add(
                            `Product: ${product}
Delivered Qty: ${deliveredQty}
Return Qty: ${returnQty}`,
                            {
                                title: "Return quantity exceeds delivered quantity",
                                type: "danger",
                            }
                        );

                        return;
                    }

                    controller.notification.add(
                        rawMessage,
                        {
                            title: "Validation Error",
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