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
            raise UserError(_("Only configured approval managers can reject this task."))

        if task.approval_state != "pending":
            raise UserError(_("This task is not waiting for approval."))

        # 1. Update Task State
        task.write({
            "approval_state": "rejected",
            "approved_by": self.env.user.id,
            "rejection_reason": self.reason,
        })

        # 2. Chatter Entry 
        task.message_post(
            body=_(
                "Task REJECTED\n"
                "Rejected By: %s\n"
                "Reason: %s"
            ) % (
                self.env.user.name,
                self.reason,
            ),
            message_type="notification", # Change type to notification
            subtype_xmlid="mail.mt_note", # Change subtype to mt_note so no automatic email is sent!
        )

        # 3. Send Single Email Template to Requester
        if task.approval_requested_by and task.approval_requested_by.email:
            template = self.env.ref(
                "project_task_status_management3.email_template_task_rejected",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(
                    task.id,
                    force_send=True,
                    email_values={
                        "email_to": task.approval_requested_by.email.strip(),
                        "res_id": 0,  # Chatter સાથે link નહિ થાય
                        "model": False,
                    },
                )

        # 4. Fast close wizard and soft reload main form view
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