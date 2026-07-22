# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    allowed_next_stage_ids = fields.Many2many(
        comodel_name="project.task.type",
        relation="project_task_type_next_stage_rel",
        column1="src_stage_id",
        column2="dest_stage_id",
        string="Allowed Next Stages",
        help="Select the stages that users can move to from this stage.",
    )

    allowed_status_ids = fields.Many2many(
        comodel_name="project.task.status",
        relation="project_task_type_status_rel",
        column1="stage_id",
        column2="status_id",
        string="Allowed Statuses",
    )

    default_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Default User",
    )

    allow_manager_bypass = fields.Boolean(
        string="Ignore Workflow",
        default=False,
        help="If enabled, Project Managers can move tasks from this stage to any stage.",
    )

    approval_required = fields.Boolean(
    string="Approval Required",
)

    approval_manager_ids = fields.Many2many(
        "res.users",
        "project_task_stage_approval_user_rel",
        "stage_id",
        "user_id",
        string="Approval Managers",
        required=True,
    )
    
    @api.onchange("approval_manager_ids")
    def _onchange_approval_manager_ids(self):
        group = self.env.ref(
            "project_task_status_management3.group_project_approval_manager",
            raise_if_not_found=False,
        )
        if not group:
            return

        return {
            "domain": {
                "approval_manager_ids": [("id", "in", group.users.ids)]
            }
        }
    @api.constrains("allowed_next_stage_ids")
    def _check_same_stage(self):
        for stage in self:
            if stage in stage.allowed_next_stage_ids:
                raise ValidationError(
                    _("A stage cannot be selected as its own next stage.")
                )