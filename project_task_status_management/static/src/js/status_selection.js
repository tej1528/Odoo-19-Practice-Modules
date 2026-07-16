/** @odoo-module **/

import { Component, onWillStart, onPatched, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class StatusSelection extends Component {
    static template = "project_task_status_management.StatusSelection";

    static props = {
        ...standardFieldProps,
    };

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
            if (this.stageId !== this.lastStageId) {
                await this.loadStatuses();
            }
        });
    }

    //-----------------------------------------------------------------------
    // Getters
    //-----------------------------------------------------------------------

    get stageId() {
        const stage = this.props.record.data.stage_id;
        return stage?.id || stage?.resId || stage?.[0] || false;
    }

    get statusId() {
        const value = this.props.record.data.status_id;
        return value?.id || value?.resId || value?.[0] || false;
    }

    get statuses() {
        return this.state.statuses;
    }

    get currentStatus() {
        return this.state.currentStatus;
    }

    //-----------------------------------------------------------------------
    // Load Stage Statuses
    //-----------------------------------------------------------------------

    async loadStatuses() {

        if (!this.stageId) {
            this.lastStageId = false;
            this.state.statuses = [];
            this.state.currentStatus = null;
            return;
        }

        this.lastStageId = this.stageId;

        const statuses = await this.orm.call(
            "project.task",
            "get_statuses",
            [this.stageId]
        );

        this.state.statuses = statuses;

        let current = statuses.find(
            (status) => status.id === this.statusId
        );

        if (!current && statuses.length) {
            current = statuses[0];

            await this.props.record.update({
                status_id: {
                    id: current.id,
                    display_name: current.name,
                },
            });
        }

        this.state.currentStatus = current || null;
    }

    //-----------------------------------------------------------------------
    // UI Helpers
    //-----------------------------------------------------------------------

    getLabel() {
        return this.currentStatus
            ? this.currentStatus.name
            : "Select Status";
    }

    iconClass(icon) {
        const icons = {
            circle: "fa fa-circle",
            play: "fa fa-play",
            pause: "fa fa-pause",
            check: "fa fa-check",
            times: "fa fa-times",
            flag: "fa fa-flag",
        };

        return icons[icon] || "fa fa-circle";
    }

    colorClass(color) {

        const colors = {
            secondary: "text-secondary",
            primary: "text-primary",
            warning: "text-warning",
            danger: "text-danger",
            success: "text-success",
        };

        return colors[color] || "text-secondary";
    }

    bgColorMap(color) {
        return {
            secondary: "#f1f2f4",
            primary: "#e7f1ff",
            warning: "#fff4dd",
            danger: "#fdeaea",
            success: "#e9f7ef",
        }[color] || "#f1f2f4";
    }
    async selectStatus(ev) {
        const statusId = Number(ev.currentTarget.dataset.id);

        const status = this.state.statuses.find(
            (status) => status.id === statusId
        );

        if (!status) {
            return;
        }

        this.state.currentStatus = status;

        await this.props.record.update({
            status_id: {
                id: status.id,
                display_name: status.name,
            },
        });
    }
    //-----------------------------------------------------------------------
    // Change Status
    //-----------------------------------------------------------------------

    // async updateStatus(status) {

    //     this.state.currentStatus = status;

    //     await this.props.record.update({
    //         status_id: {
    //             id: status.id,
    //             display_name: status.name,
    //         },
    //     });
    // }
}

export const statusSelectionField = {
    component: StatusSelection,
    supportedTypes: ["many2one"],
};

registry.category("fields").add(
    "status_selection",
    statusSelectionField
);