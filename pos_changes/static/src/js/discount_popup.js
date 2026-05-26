/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

console.log(" open pos popup");

export class DiscountPopup extends Component {

    static template = "pos_changes.DiscountPopup";

    static components = { Dialog };

    static props = {
        close: Function,
    };

    setup() {

        this.state = useState({
            percent: "",
            amount: "",
        });
    }

    confirm() {

        console.log("Confirmed");

        this.props.close({

            confirmed: true,

            payload: {

                percent:
                    parseFloat(this.state.percent) || 0,

                amount:
                    parseFloat(this.state.amount) || 0,
            },
        });
    }

    cancel() {

        this.props.close({
            confirmed: false,
        });
    }
}