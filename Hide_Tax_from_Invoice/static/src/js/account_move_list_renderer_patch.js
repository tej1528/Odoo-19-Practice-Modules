/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { AccountMoveListRenderer } from "@account/views/account_move_list/account_move_list_renderer";

patch(AccountMoveListRenderer.prototype, {

    get optionalFieldGroups() {
        const groups = super.optionalFieldGroups;

        const record = this.props.list.records[0];

        if (!record || !record.data.hide_tax) {
            return groups;
        }

        return groups.map(group => ({
            ...group,
            optionalFields: group.optionalFields.filter(
                field => field.name !== "amount_tax_signed"
            ),
        }));
    },

    getActiveColumns() {
        const columns = super.getActiveColumns();

        const record = this.props.list.records[0];

        if (!record || !record.data.hide_tax) {
            return columns;
        }

        return columns.filter(
            column => column.name !== "amount_tax_signed"
        );
    },

});