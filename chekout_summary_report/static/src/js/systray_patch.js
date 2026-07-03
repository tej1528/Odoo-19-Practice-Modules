/** @odoo-module **/
console.log("PATCH FILE LOADED");
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { ActivityMenu } from "@hr_attendance/components/attendance_menu/attendance_menu";
import { AttendanceSummaryDialog } from "./attendance_summary_dialog";

const original = ActivityMenu.prototype.signInOut;

patch(ActivityMenu.prototype, {
    async signInOut(...args) {
        if (!this.state.checkedIn) {
            return original.apply(this, args);
        }
        this.dropdown.close();
        const summary = await rpc("/attendance/checkout_summary");
        this.dialogService.add(AttendanceSummaryDialog, {
            summary,
            onCheckout: async () => {
                await this.checking();
            },
        });
    },
});