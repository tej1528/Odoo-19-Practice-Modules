from odoo import models, fields, api

class HospitalManagement(models.Model):
    _name = 'hospital_management.hospital_management'
    _description = 'Hospital Management'

    name = fields.Char(string="Patient Name")
    value = fields.Integer(string="Value")
    value2 = fields.Float(string="Percentage", compute="_compute_value_pc", store=True)
    description = fields.Text(string="Description")

    @api.depends('value')
    def _compute_value_pc(self):
        for record in self:
            record.value2 = float(record.value) / 100