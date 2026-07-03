/** @odoo-module **/
import { Dialog } from "@web/core/dialog/dialog";
import { Component } from "@odoo/owl";

export class AttendanceSummaryDialog extends Component {
    static template = "chekout_summary_report.AttendanceSummaryDialog";

    static components = {
        Dialog,
    };

    static props = {
        close: Function,
        summary: Object,
        onCheckout: Function,
    };

    async checkout() {
        await this.props.onCheckout();
        this.props.close();
    }
}