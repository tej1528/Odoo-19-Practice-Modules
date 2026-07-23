# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, Command
from odoo.exceptions import ValidationError, UserError


class ProjectTask(models.Model):
    _inherit = "project.task"

    status_id = fields.Many2one(
        "project.task.status",
        string="Task Status",
        tracking=True,
    )

    approval_state = fields.Selection(
        [
            ("none", "Not Requested"),
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Approval Status",
        default="none",
        copy=False,
        tracking=True,
    )

    approval_requested_by = fields.Many2one(
        "res.users",
        string="Requested By",
        copy=False,
        tracking=True,
        readonly=True,
    )

    approved_by = fields.Many2one(
        "res.users",
        string="Approved By",
        copy=False,
        tracking=True,
        readonly=True,
    )

    rejection_reason = fields.Text(
        string="Rejection Reason",
        copy=False,
        tracking=True,
        readonly=True,
    )

    approval_required = fields.Boolean(
        related="stage_id.approval_required",
        readonly=True,
    )

    can_approve = fields.Boolean(
        compute="_compute_can_approve",
    )

    @api.depends("stage_id.approval_manager_ids")
    def _compute_can_approve(self):
        current_user = self.env.user
        for task in self:
            task.can_approve = current_user in task.stage_id.approval_manager_ids

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

    @api.model
    def get_statuses(self, stage_id=False):
        if stage_id:
            stage = self.env["project.task.type"].browse(stage_id)
            statuses = (
                stage.allowed_status_ids.sorted("sequence")
                if stage.exists() and stage.allowed_status_ids
                else self.env["project.task.status"].search([], order="sequence")
            )
        else:
            statuses = self.env["project.task.status"].search([], order="sequence")

        return [
            {
                "id": s.id,
                "name": s.name,
                "icon": s.icon,
                "icon_color": s.icon_color,
            }
            for s in statuses
        ]

    def write(self, vals):
        if "stage_id" in vals:
            new_stage = self.env["project.task.type"].browse(vals["stage_id"])
            is_manager = self.env.user.has_group("project.group_project_manager")

            for task in self:
                current_stage = task.stage_id

                if current_stage and current_stage != new_stage:
                    # Check 1: Approval Required Validation
                    current_approval_state = vals.get("approval_state", task.approval_state)
                    if current_stage.approval_required and current_approval_state != "approved":
                        raise ValidationError(_(
                            "Current stage '%s' requires manager approval.\n\n"
                            "Please request approval and get it approved before changing stage."
                        ) % current_stage.display_name)

                    # Check 2: Allowed Next Stage Validation
                    if not (current_stage.allow_manager_bypass and is_manager):
                        allowed = current_stage.allowed_next_stage_ids
                        if allowed and new_stage not in allowed:
                            raise ValidationError(
                                _("You cannot move the task from '%s' to '%s'. Allowed stages are: %s")
                                % (
                                    current_stage.display_name,
                                    new_stage.display_name,
                                    ", ".join(allowed.mapped("display_name")),
                                )
                            )

                # Stage according Default Assignee 
                if new_stage.default_user_id:
                    vals["user_ids"] = [Command.set([new_stage.default_user_id.id])]

                # Stage -> Statuses
                allowed_statuses = new_stage.allowed_status_ids.sorted("sequence")
                if not allowed_statuses:
                    allowed_statuses = self.env["project.task.status"].search([], order="sequence")

                active_status_id = vals.get("status_id", task.status_id.id)
                if not active_status_id or active_status_id not in allowed_statuses.ids:
                    vals["status_id"] = allowed_statuses[0].id if allowed_statuses else False

        return super().write(vals)

    def action_request_for_approval(self):
        self.ensure_one()

        if not self.stage_id.approval_required:
            raise UserError(_("Approval is not required for this stage."))

        if not self.stage_id.approval_manager_ids:
            raise UserError(_("No approval managers are configured for this stage."))

        if self.approval_state == "pending":
            raise UserError(_("Approval request is already pending for this task."))

        self.write({
            "approval_state": "pending",
            "approval_requested_by": self.env.user.id,
            "rejection_reason": False,
        })

        template = self.env.ref(
            "project_task_status_management3.email_template_task_approval_request",
            raise_if_not_found=False,
        )

        if template:
            partner_ids = self.stage_id.approval_manager_ids.mapped("partner_id").ids

            self.with_context(
                approval_request_only_managers=True,
            ).message_post_with_source(
                source_ref=template,
                render_values={
                    "base_url": self.get_base_url(),
                    "hide_button": False,
                },
                subtype_xmlid="mail.mt_comment",
                partner_ids=partner_ids,
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Request Sent"),
                "message": _("Approval request has been submitted successfully!"),
                "type": "success",
                "sticky": False,
                "next": {
                    "type": "ir.actions.client",
                    "tag": "soft_reload",
                },
            },
        }

    def action_approve_task(self):
        self.ensure_one()

        if self.env.user not in self.stage_id.approval_manager_ids:
            raise UserError(_("Only configured approval managers can approve this task."))

        if self.approval_state != "pending":
            raise UserError(_("This task is not waiting for approval."))

        current_stage = self.stage_id
        target_stage = current_stage.allowed_next_stage_ids.sorted("sequence")[:1]

        if not target_stage:
            target_stage = self.env["project.task.type"].search([
                ("id", "!=", current_stage.id),
                ("sequence", ">=", current_stage.sequence),
            ], order="sequence", limit=1)

        vals = {
            "approval_state": "approved",
            "approved_by": self.env.user.id,
            "rejection_reason": False,
        }

        if target_stage:
            vals["stage_id"] = target_stage.id

        self.write(vals)

        template = self.env.ref(
            "project_task_status_management3.email_template_task_approved",
            raise_if_not_found=False,
        )

        if template and self.approval_requested_by.partner_id:
            partner_ids = [self.approval_requested_by.partner_id.id]

            self.with_context(
                approval_request_only_managers=True,
            ).message_post_with_source(
                source_ref=template,
                render_values={
                    "base_url": self.get_base_url(),
                    "hide_button": False,
                },
                subtype_xmlid="mail.mt_comment",
                partner_ids=partner_ids,
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Approved"),
                "message": _("Task approved successfully and moved to stage '%s'!") % self.stage_id.name,
                "type": "success",
                "sticky": False,
                "next": {
                    "type": "ir.actions.client",
                    "tag": "soft_reload",
                },
            },
        }
    
    def action_open_reject_wizard(self):
        self.ensure_one()

        if self.env.user not in self.stage_id.approval_manager_ids:
            raise UserError(_("Only configured approval managers can reject this task."))

        if self.approval_state != "pending":
            raise UserError(_("This task is not waiting for approval."))

        return {
            "name": _("Reject Task"),
            "type": "ir.actions.act_window",
            "res_model": "task.reject.wizard",
            "view_mode": "form",
            "view_id": self.env.ref(
                "project_task_status_management3.view_task_reject_wizard_form"
            ).id,
            "target": "new",
            "context": {
                "default_task_id": self.id,
            },
        }