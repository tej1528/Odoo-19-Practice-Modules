# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, Command
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = "project.task"

    status_id = fields.Many2one(
        comodel_name="project.task.status",
        string="Task Status",
        tracking=True,
    )

    approval_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        string="Approval State",
        tracking=True,
    )
    rejection_reason = fields.Text(string="Rejection Reason", tracking=True)
    pending_stage_id = fields.Many2one("project.task.type", string="Pending Stage Target")
    
    is_approval_manager = fields.Boolean(compute="_compute_is_approval_manager")

    @api.depends("stage_id", "stage_id.approved_user_id")
    def _compute_is_approval_manager(self):
        current_user = self.env.user
        for task in self:
            manager = task.stage_id.approved_user_id
            task.is_approval_manager = bool(manager and (current_user == manager or current_user._is_admin()))

    def _get_ordered_statuses_for_stage(self, stage):
        if not stage or not stage.allowed_status_ids:
            return self.env["project.task.status"].search([])

        self.env.cr.execute(
            """
            SELECT status_id 
            FROM project_task_type_status_rel 
            WHERE stage_id = %s
            """,
            [stage.id]
        )
        inserted_ids = [row[0] for row in self.env.cr.fetchall()]
        statuses = stage.allowed_status_ids
        return sorted(statuses, key=lambda s: inserted_ids.index(s.id) if s.id in inserted_ids else 999)

    @api.constrains("stage_id", "status_id")
    def _check_allowed_status(self):
        for task in self:
            if task.stage_id and task.status_id and task.stage_id.allowed_status_ids:
                if task.status_id not in task.stage_id.allowed_status_ids:
                    raise ValidationError(
                        _("Status '%s' is not allowed in stage '%s'.")
                        % (task.status_id.display_name, task.stage_id.display_name)
                    )

    @api.onchange("stage_id")
    def _onchange_stage_id_set_default_user(self):
        if self.stage_id and self.stage_id.default_user_id:
            self.user_ids = [Command.set([self.stage_id.default_user_id.id])]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("stage_id"):
                stage = self.env["project.task.type"].browse(vals["stage_id"])
                
                if stage.default_user_id:
                    vals["user_ids"] = [Command.set([stage.default_user_id.id])]

                if not vals.get("status_id"):
                    ordered_statuses = self._get_ordered_statuses_for_stage(stage)
                    if ordered_statuses:
                        vals["status_id"] = ordered_statuses[0].id

        return super().create(vals_list)

    def write(self, vals):
        if "stage_id" in vals:
            new_stage = self.env["project.task.type"].browse(vals["stage_id"])
            is_manager = self.env.user.has_group("project.group_project_manager")

            for task in self:
                current_stage = task.stage_id

                if current_stage and current_stage != new_stage:
                    if current_stage.approved_user_id and task.approval_state != "approved":
                        manager = current_stage.approved_user_id
                        
                        if self.env.user != manager:
                            # stop Stage 
                            vals.pop("stage_id", None)
                            
                            # State Pending Approval 
                            task.write({
                                "approval_state": "pending",
                                "pending_stage_id": new_stage.id,
                                "rejection_reason": False,
                            })
                            
                            body_msg = _(
                                "Approval Request Sent! Waiting for manager %s to approve moving task from %s to %s."
                            ) % (manager.name, current_stage.display_name, new_stage.display_name)
                            
                            task.message_post(
                                body=body_msg,
                                subtype_xmlid="mail.mt_note",
                            )

                            task._send_approval_request_mail(manager)
                            return super().write(vals)

                    # Manager Bypass and Allowed Stage Validation
                    if not (current_stage.allow_manager_bypass and is_manager):
                        allowed = current_stage.allowed_next_stage_ids
                        if allowed and new_stage not in allowed:
                            raise ValidationError(
                                _("You cannot move the task from '%s' to '%s'.")
                                % (current_stage.display_name, new_stage.display_name)
                            )

                # default user assign
                if new_stage.default_user_id:
                    vals["user_ids"] = [Command.set([new_stage.default_user_id.id])]

                ordered_statuses = self._get_ordered_statuses_for_stage(new_stage)
                active_status_id = vals.get("status_id", task.status_id.id)
                
                if new_stage.allowed_status_ids:
                    if not active_status_id or active_status_id not in new_stage.allowed_status_ids.ids:
                        vals["status_id"] = ordered_statuses[0].id if ordered_statuses else False

                # After moving to the new stage, reset the state and stage ID for fresh approval at the second stage.
                vals["approval_state"] = "draft"
                vals["pending_stage_id"] = False

        return super().write(vals)

    def _send_approval_request_mail(self, manager):
        self.ensure_one()
        if not manager.email:
            self.message_post(body=_("Could not send email. Manager '%s' does not have an email address configured.") % manager.name)
            return

        template = self.env.ref("project_task_status_management.email_template_task_approval_request", raise_if_not_found=False)
        if template:
            template.send_mail(
                self.id, 
                force_send=True, 
                email_values={
                    "email_to": manager.email,
                }
            )

    def action_approve_task(self):
        for task in self:
            if task.pending_stage_id:
                target_stage = task.pending_stage_id
                
                ordered_statuses = self._get_ordered_statuses_for_stage(target_stage)
                
                vals_to_write = {
                    "stage_id": target_stage.id,
                    "approval_state": "approved",
                    "pending_stage_id": False,
                    "rejection_reason": False,
                }

                if target_stage.allowed_status_ids and ordered_statuses:
                    vals_to_write["status_id"] = ordered_statuses[0].id

                if target_stage.default_user_id:
                    vals_to_write["user_ids"] = [Command.set([target_stage.default_user_id.id])]

                task.write(vals_to_write)
                
                task.message_post(
                    body=_("Task approval request has been Approved by %s.") % self.env.user.name,
                    subtype_xmlid="mail.mt_note",
                )

    def action_reject_task_wizard(self):
        return {
            "name": _("Reject Task Approval"),
            "type": "ir.actions.act_window",
            "res_model": "project.task.reject.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_task_id": self.id},
        }

    @api.model
    def get_statuses(self, stage_id):
        stage = self.env["project.task.type"].browse(stage_id)
        ordered_statuses = self._get_ordered_statuses_for_stage(stage)
        return [
            {
                "id": status.id,
                "name": status.name,
                "icon": status.icon,
                "icon_color": status.icon_color,
            }
            for status in ordered_statuses
        ]