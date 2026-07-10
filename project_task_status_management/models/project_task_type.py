from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    allowed_next_stage_ids = fields.Many2many(
        comodel_name="project.task.type",
        relation="project_task_type_allowed_stage_rel",
        column1="current_stage_id",
        column2="next_stage_id",
        string="Allowed Next Stages",
        help="Select the stages that users can move to from this stage.",
    )

    @api.constrains("allowed_next_stage_ids")
    def _check_same_stage(self):
        for stage in self:
            if stage in stage.allowed_next_stage_ids:
                raise ValidationError(
                    _("A stage cannot be selected as its own next stage.")
                )