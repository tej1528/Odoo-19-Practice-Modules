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

        # 2. Render Template and Post Chatter Msg (Button ) & Send Mail (Button )
        if task.approval_requested_by and task.approval_requested_by.email:
            template = self.env.ref(
                "project_task_status_management3.email_template_task_rejected",
                raise_if_not_found=False,
            )
            if template:
                base_url = task.get_base_url()
                
                # Chatter without btn
                body_chatter = template.with_context(
                    base_url=base_url, 
                    hide_button=True
                )._render_field('body_html', task.ids)[task.id]

                task.with_context(
                    mail_notify_author=False,
                    mail_post_autofollow=False
                ).message_post(
                    body=body_chatter,
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                    partner_ids=[],
                )
                
                # mail btn 
                template.with_context(
                    base_url=base_url, 
                    hide_button=False
                ).send_mail(
                    task.id,
                    force_send=True,
                    email_values={
                        "email_to": task.approval_requested_by.email.strip(),
                        "res_id": task.id,
                        "model": "project.task",
                    },
                )

        # 3. Fast close wizard and soft reload main form view
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