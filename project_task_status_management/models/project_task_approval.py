from odoo import _, api, fields, models


class ProjectTaskApproval(models.Model):
    _name = "project.task.approval"
    _description = "Project Task Approval"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: _("New"),
    )

    task_id = fields.Many2one(
        "project.task",
        string="Task",
        required=True,
        ondelete="cascade",
        tracking=True,
    )

    requested_by = fields.Many2one(
        "res.users",
        string="Requested By",
        required=True,
        default=lambda self: self.env.user,
        readonly=True,
        tracking=True,
    )

    approver_id = fields.Many2one(
        "res.users",
        string="Approver",
        required=True,
        tracking=True,
    )

    current_stage_id = fields.Many2one(
        "project.task.type",
        string="Current Stage",
        required=True,
        readonly=True,
        tracking=True,
    )

    requested_stage_id = fields.Many2one(
        "project.task.type",
        string="Requested Stage",
        required=True,
        readonly=True,
        tracking=True,
    )

    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Status",
        default="pending",
        readonly=True,
        tracking=True,
    )

    rejection_reason = fields.Text(
        string="Rejection Reason",
        readonly=True,
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "project.task.approval"
                ) or _("New")
        return super().create(vals_list)