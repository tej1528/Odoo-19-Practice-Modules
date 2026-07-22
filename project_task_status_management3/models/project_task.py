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

        # Update Approval State
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
            base_url = self.get_base_url()

            # 1. Chatter Entry (No Followers notified)
            body_chatter = template.with_context(
                base_url=base_url,
                hide_button=True,
            )._render_field("body_html", self.ids)[self.id]

            self.with_context(
                mail_notify_author=False,
                mail_post_autofollow=False,
                mail_create_nosubscribe=True,
                mail_auto_subscribe_no_notify=True,
            ).message_post(
                body=body_chatter,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
                partner_ids=[], 
            )

            # 2. Extract Manager Emails in Python
            managers = self.stage_id.approval_manager_ids.filtered(lambda u: u.email)
            email_to_list = ",".join(managers.mapped("email"))

            # 3. Send direct email ONLY to managers
            if email_to_list:
                template.with_context(
                    base_url=base_url,
                    hide_button=False,
                ).send_mail(
                    self.id,
                    force_send=True,
                    email_values={
                        "email_to": email_to_list,
                        "recipient_ids": [],
                        "partner_ids": [],
                    },
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
        target_stage = False

        # Find allowed next stages
        allowed_stages = current_stage.allowed_next_stage_ids.sorted("sequence")

        if not allowed_stages:
            allowed_stages = self.env["project.task.type"].search([
                ("id", "!=", current_stage.id),
                ("sequence", ">=", current_stage.sequence)
            ], order="sequence asc")

        if allowed_stages:
            in_progress_stage = allowed_stages.filtered(
                lambda s: "in progress" in (s.name or "").lower() or "progress" in (s.name or "").lower()
            )
            
            if in_progress_stage:
                target_stage = in_progress_stage[0]
            else:
                target_stage = allowed_stages[0]

        # Update Status and Approval State
        write_values = {
            "approval_state": "approved",
            "approved_by": self.env.user.id,
            "rejection_reason": False,
        }

        if target_stage:
            write_values["stage_id"] = target_stage.id

        self.write(write_values)

        # Chatter msg & Email Notification back to Requester
        requester_email = self.approval_requested_by.email
        if requester_email:
            template = self.env.ref(
                "project_task_status_management3.email_template_task_approved",
                raise_if_not_found=False,
            )
            if template:
                base_url = self.get_base_url()
                
                # Chatter msg without btn
                body_chatter = template.with_context(
                    base_url=base_url, hide_button=True
                )._render_field("body_html", self.ids)[self.id]

                self.with_context(
                    mail_notify_author=False,
                    mail_post_autofollow=False
                ).message_post(
                    body=body_chatter,
                    message_type="comment",
                    subtype_xmlid="mail.mt_comment",
                )

                # Send mail strictly to Requester
                template.with_context(
                    base_url=base_url,
                    hide_button=False,
                ).send_mail(
                    self.id,
                    force_send=True,
                    email_values={
                        "email_to": requester_email, # Direct email setting
                        "partner_ids": [],
                        "recipient_ids": [],
                    },
                )

        # Client Response
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
            "res_id": False,
            "context": {
                "default_task_id": self.id,
            },
        }