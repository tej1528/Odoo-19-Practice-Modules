# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, Command
from odoo.exceptions import ValidationError

class ProjectTask(models.Model):
    _inherit = "project.task"

    status_id = fields.Many2one(
        "project.task.status",
        string="Task Status",
        tracking=True,
    )

    @api.constrains("stage_id", "status_id")
    def _check_allowed_status(self):
        for task in self:
            if task.stage_id and task.status_id and task.stage_id.allowed_status_ids:
                if task.status_id not in task.stage_id.allowed_status_ids:
                    raise ValidationError(
                        _("Status '%s' is not allowed in stage '%s'.")
                        % (task.status_id.display_name, task.stage_id.display_name)
                    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("stage_id"):
                stage = self.env["project.task.type"].browse(vals["stage_id"])
                
                if stage.default_user_id and not vals.get("user_ids"):
                    vals["user_ids"] = [Command.set([stage.default_user_id.id])]

                if not vals.get("status_id"):
                    allowed_statuses = stage.allowed_status_ids.sorted("sequence")
                    if not allowed_statuses:
                        allowed_statuses = self.env["project.task.status"].search([], order="sequence")
                    
                    if allowed_statuses:
                        vals["status_id"] = allowed_statuses[0].id

        return super().create(vals_list)

    def write(self, vals):
        if "stage_id" in vals:
            new_stage = self.env["project.task.type"].browse(vals["stage_id"])
            is_manager = self.env.user.has_group("project.group_project_manager")

            for task in self:
                current_stage = task.stage_id
                if current_stage and current_stage != new_stage:
                    if not (current_stage.allow_manager_bypass and is_manager):
                        allowed = current_stage.allowed_next_stage_ids
                        if allowed and new_stage not in allowed:
                            raise ValidationError(
                                _("You cannot move the task from '%s' to '%s'.")
                                % (current_stage.display_name, new_stage.display_name)
                            )

                if new_stage.default_user_id:
                    vals["user_ids"] = [Command.set([new_stage.default_user_id.id])]

                allowed_statuses = new_stage.allowed_status_ids.sorted("sequence")
                if not allowed_statuses:
                    allowed_statuses = self.env["project.task.status"].search([], order="sequence")
                
                active_status_id = vals.get("status_id", task.status_id.id)
                if not active_status_id or active_status_id not in allowed_statuses.ids:
                    vals["status_id"] = allowed_statuses[0].id if allowed_statuses else False
                    
        return super().write(vals)

    @api.model
    def get_statuses(self, stage_id=False):
        if stage_id:
            stage = self.env["project.task.type"].browse(stage_id)
            statuses = stage.allowed_status_ids.sorted("sequence") if stage.exists() and stage.allowed_status_ids else self.env["project.task.status"].search([], order="sequence")
        else:
            statuses = self.env["project.task.status"].search([], order="sequence")

        return [{
            "id": s.id,
            "name": s.name,
            "icon": s.icon,
            "icon_color": s.icon_color,
        } for s in statuses]