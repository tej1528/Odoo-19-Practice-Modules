# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import UserError


class TaskRejectWizard(models.TransientModel):
    _name = "task.reject.wizard"
    _description = "Task Reject Wizard"

    task_id = fields.Many2one(
        "project.task",
        string="Task",
        required=True,
        readonly=True,
    )

    reason = fields.Text(
        string="Rejection Reason",
        required=True,
    )

    def action_reject(self):
        self.ensure_one()

        task = self.task_id

        if self.env.user not in task.stage_id.approval_manager_ids:
            raise UserError(
                _("Only configured approval managers can reject this task.")
            )

        if task.approval_state != "pending":
            raise UserError(
                _("This task is not waiting for approval.")
            )

        # Update task
        task.write({
            "approval_state": "rejected",
            "approved_by": self.env.user.id,
            "rejection_reason": self.reason,
        })

        # Post one chatter message + send one email
        template = self.env.ref(
            "project_task_status_management3.email_template_task_rejected",
            raise_if_not_found=False,
        )

        if template and task.approval_requested_by.partner_id:
            partner_ids = [task.approval_requested_by.partner_id.id]

            task.with_context(
                approval_request_only_managers=True,
            ).message_post_with_source(
                source_ref=template,
                render_values={
                    "base_url": task.get_base_url(),
                    "hide_button": False,
                },
                subtype_xmlid="mail.mt_comment",
                partner_ids=partner_ids,
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Task Rejected"),
                "message": _("Task approval request has been rejected."),
                "type": "warning",
                "sticky": False,
                "next": {
                    "type": "ir.actions.client",
                    "tag": "soft_reload",
                },
            },
        }