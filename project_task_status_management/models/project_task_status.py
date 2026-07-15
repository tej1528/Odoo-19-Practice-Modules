# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectTaskStatus(models.Model):
    _name = "project.task.status"
    _description = "Project Task Status"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    icon = fields.Selection(
        [
            ("circle", "Circle"),
            ("play", "Play"),
            ("pause", "Pause"),
            ("check", "Check"),
            ("times", "Times"),
            ("flag", "Flag"),
        ],
        default="circle",
        required=True,
    )

    icon_color = fields.Selection(
        [
            ("secondary", "Grey"),
            ("primary", "Blue"),
            ("warning", "Yellow"),
            ("danger", "Red"),
            ("success", "Green"),
        ],
        default="secondary",
        required=True,
    )