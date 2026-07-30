/** @odoo-module **/
import { registry } from "@web/core/registry";

export const PaymentNotificationService = {
    dependencies: ["bus_service", "notification", "action"],

    start(env, { bus_service, notification, action }) {
        bus_service.subscribe("payment_registered", (payload) => {
            const audio = new Audio(
                "/sale_payment_status/static/src/audio/notification.mp3"
            );
            audio.volume = 1.0;
            audio.play().catch(() => { });

            // Notification Toast Show
            const closeNotification = notification.add(
                `Payment of ₹${payload.amount} has been registered for ${payload.invoice_name || payload.sale_order} by ${payload.registered_by}.`,
                {
                    title: "Payment Registered",
                    type: "success",
                    sticky: true,
                    buttons: [
                        {
                            name: "Open Invoice",
                            primary: true,
                            onClick: async () => {
                                if (typeof closeNotification === "function") {
                                    closeNotification();
                                }
                                try {
                                    await action.doAction(payload.action);
                                } catch (_) {
                                    // Handle navigation error
                                }
                            },
                        },
                    ],
                }
            );
        });
    },
};

registry.category("services").add("payment_notification_service", PaymentNotificationService);