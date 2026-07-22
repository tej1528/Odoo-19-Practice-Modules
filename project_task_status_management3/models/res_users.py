from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = list(args or [])

        if self.env.context.get("approval_manager_only"):
            group = self.env.ref(
                "project_task_status_management3.group_project_approval_manager",
                raise_if_not_found=False,
            )
            if group:
                args.append(("id", "in", group.user_ids.ids))
            else:
                args.append(("id", "=", 0))

        return super().name_search(
    name,
    args,
    operator,
    limit,
)