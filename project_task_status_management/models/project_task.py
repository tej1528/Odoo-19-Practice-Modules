from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = "project.task"

    def write(self, vals):
        # stage chnge na thay tyaare dayrek return 
        if "stage_id" not in vals:
            return super().write(vals)

        new_stage = self.env["project.task.type"].browse(vals["stage_id"])

        for task in self:
            # current stage na hoi or same satage 
            if not task.stage_id or task.stage_id == new_stage:
                continue

            allowed_stages = task.stage_id.allowed_next_stage_ids

            # translation config na karel hoi tyare(empty)
            if not allowed_stages:
                raise ValidationError(
                    _("No transition is configured for stage '%s'.", task.stage_id.display_name)
                )

            # translation allow na hoi tayare 
            if new_stage not in allowed_stages:
                raise ValidationError(
                    _("You cannot move the task from '%s' to '%s'.", task.stage_id.display_name, new_stage.display_name)
                )

        return super().write(vals)