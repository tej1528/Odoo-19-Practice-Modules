# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class ProjectTaskRejectWizard(models.TransientModel):
    _name = "project.task.reject.wizard"
    _description = "Project Task Reject Wizard"

    task_id = fields.Many2one("project.task", string="Task", required=True)
    reason = fields.Text(string="Rejection Reason", required=True)

    def action_confirm_reject(self):
        if not self.reason:
            raise UserError(_("Please enter a reason for rejection."))

        self.task_id.write({
            "approval_state": "rejected",
            "rejection_reason": self.reason,
            "pending_stage_id": False,
        })
        
        # chatter me 
        self.task_id.message_post(
            body=_("Task approval request has been Rejected by %s. Reason: %s") % (self.env.user.name, self.reason),
            subtype_xmlid="mail.mt_comment",
        )
        return {"type": "ir.actions.act_window_close"}