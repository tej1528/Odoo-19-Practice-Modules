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
        help="If enabled, Project Managers can move tasks from this stage to any stage."
    )

    approved_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Approval Manager",
        help="Manager required to approve before moving task out of this stage.",
    )

    @api.constrains("allowed_next_stage_ids")
    def _check_same_stage(self):
        for stage in self:
            if stage in stage.allowed_next_stage_ids:
                raise ValidationError(
                    _("A stage cannot be selected as its own next stage.")
                )