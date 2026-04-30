/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount, onWillUpdateProps } from "@odoo/owl";
import { deserializeDateTime } from "@web/core/l10n/dates";
import { registry } from "@web/core/registry";

export class ProcessingTimer extends Component {
    setup() {
        this.state = useState({ time: "00:00:00" });
        this.interval = null;

        onMounted(() => {
            this.startTimer();
        });

        // જો પ્રોપ્સ બદલાય (જેમ કે એક રેકોર્ડ પરથી બીજા પર જાવ), તો ટાઈમર ફરી શરૂ કરો
        onWillUpdateProps((nextProps) => {
            this.startTimer(nextProps);
        });

        onWillUnmount(() => {
            this.stopTimer();
        });
    }

    stopTimer() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }

    startTimer(props = this.props) {
        this.stopTimer(); // પહેલા ચાલતા ટાઈમરને બંધ કરો

        const record = props.record;
        const startTimeStr = record && record.data.processing_start_time;

        if (!startTimeStr) {
            this.state.time = "00:00:00";
            return;
        }

        // Odoo DateTime ને Luxon માં ફેરવો
        const start = typeof startTimeStr === 'string'
            ? deserializeDateTime(startTimeStr)
            : startTimeStr;

        this.interval = setInterval(() => {
            // ખાતરી કરો કે component હજી અસ્તિત્વમાં છે
            if (!this.state) {
                this.stopTimer();
                return;
            }

            const now = luxon.DateTime.now();
            const diff = now.diff(start, ['hours', 'minutes', 'seconds']);

            if (diff.as('seconds') < 0) {
                this.state.time = "00:00:00";
                return;
            }

            // સમય ફોર્મેટિંગ
            const hrs = String(Math.floor(diff.hours || 0)).padStart(2, "0");
            const mins = String(Math.floor(diff.minutes || 0)).padStart(2, "0");
            const secs = String(Math.floor(diff.seconds || 0)).padStart(2, "0");

            this.state.time = `${hrs}:${mins}:${secs}`;
        }, 1000);
    }
}

ProcessingTimer.template = "hospital.ProcessingTimer";
ProcessingTimer.props = ["*"];

registry.category("view_widgets").add("processing_timer", {
    component: ProcessingTimer,
});