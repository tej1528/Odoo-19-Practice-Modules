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

        const statuses = await this.orm.call("project.task", "get_statuses", [stageId]);
        this.state.statuses = statuses;

        const value = this.props.record.data.status_id;
        const id = value ? (value.id || value.resId || value[0]) : false;

        const selected = id ? statuses.find(s => s.id === id) : null;

        if (selected) {
            this.state.currentStatus = selected;
        } else {
            // set first status
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

    get statuses() {
        return this.state.statuses;
    }

    get currentStatus() {
        return this.state.currentStatus;
    }

    get statusName() {
        return this.currentStatus ? this.currentStatus.name : "Select Status";
    }

    // Font Awesome icon mapping
    iconMap(icon) {
        if (!icon) return "fa-circle";
        const cleanIcon = icon.toLowerCase().trim();
        const mapping = {
            circle: "fa-circle",
            play: "fa-play",
            pause: "fa-pause",
            check: "fa-check",
            times: "fa-times",
            flag: "fa-flag",
            exclamation: "fa-exclamation-circle"
        };
        return mapping[cleanIcon] || "fa-circle";
    }

    colorMap(color) {
        return {
            secondary: "#6c757d",
            primary: "#0d6efd",
            warning: "#b27b00",     
            danger: "#dc3545",
            success: "#198754",
        }[color] || "#6c757d";
    }

    bgColorMap(color) {
        return {
            secondary: "#f1f2f4", // Light grey
            primary: "#e2efff",   // Light blue
            warning: "#fff2df",   // Light orange
            danger: "#fce8e6",    // Light red
            success: "#e2f6ed",   // Light green
        }[color] || "#f1f2f4";
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