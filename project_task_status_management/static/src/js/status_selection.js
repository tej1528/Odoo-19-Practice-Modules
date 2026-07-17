/** @odoo-module **/

import { Component, onWillStart, onPatched, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class StatusSelection extends Component {
    static template = "project_task_status_management.StatusSelection";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            statuses: [],
            currentStatus: null,
        });
        this.lastStageId = false;

        onWillStart(async () => {
            await this.loadStatuses();
        });

        onPatched(async () => {
            const stage = this.props.record.data.stage_id;
            const stageId = stage?.id || stage?.resId || stage?.[0] || false;

            if (stageId !== this.lastStageId) {
                await this.loadStatuses();
            }
        });
    }

    async loadStatuses() {
        const stage = this.props.record.data.stage_id;
        if (!stage) {
            this.lastStageId = false;
            this.state.statuses = [];
            this.state.currentStatus = null;
            return;
        }

        const stageId = stage.id || stage.resId || stage[0];
        this.lastStageId = stageId;

        const statuses = await this.orm.call("project.task", "get_statuses", [], { stage_id: stageId });
        this.state.statuses = statuses;

        const value = this.props.record.data.status_id;
        const id = value ? (value.id || value.resId || value[0]) : false;
        const selected = id ? statuses.find(s => s.id === id) : null;

        if (selected) {
            this.state.currentStatus = selected;
        } else {
            if (statuses.length > 0) {
                const firstStatus = statuses[0];
                this.state.currentStatus = firstStatus;
                await this.props.record.update({
                    status_id: {
                        id: firstStatus.id,
                        display_name: firstStatus.name,
                    },
                });
            } else {
                this.state.currentStatus = null;
                await this.props.record.update({ status_id: false });
            }
        }
    }

    get dividerStatusId() {
        if (!this.state.statuses || this.state.statuses.length === 0) return false;

        const doneStatus = this.state.statuses.find(s => s.name === 'Done' || s.name === 'DONE');
        if (doneStatus) return doneStatus.id;

        const cancelStatus = this.state.statuses.find(s => ['Canceled', 'CANCEL', 'Cancel'].includes(s.name));
        if (cancelStatus) return cancelStatus.id;

        return false;
    }

    iconMap(icon) {
        if (!icon) return "fa-circle";
        const mapping = {
            circle: "fa-circle",
            play: "fa-play",
            pause: "fa-pause",
            check: "fa-check",
            times: "fa-times",
            flag: "fa-flag",
        };
        return mapping[icon.toLowerCase().trim()] || "fa-circle";
    }

    colorMap(color) {
        return {
            secondary: "#6C757D", // Light Odoo Grey
            primary: "#00A09D",   // Odoo Teal
            warning: "#E0A900",   // Light Yellow
            danger: "#DC3545",    // Light Red
            success: "#10B981",   // Light Green
        }[color] || "#6C757D";
    }

    async selectStatus(ev) {
        const statusId = Number(ev.currentTarget.dataset.id);
        const status = this.state.statuses.find(s => s.id === statusId);
        if (!status) return;

        this.state.currentStatus = status;
        await this.props.record.update({
            status_id: {
                id: status.id,
                display_name: status.name,
            },
        });
    }
}

export const statusSelectionField = {
    component: StatusSelection,
    supportedTypes: ["many2one"],
};

registry.category("fields").add("status_selection", statusSelectionField);