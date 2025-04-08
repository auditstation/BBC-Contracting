# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, api, fields, _
from odoo.exceptions import UserError


class LocationHistory(models.Model):
    _name = 'location.history'
    _description = "Location history"

    employee_id = fields.Char(string='Employee Id', help="Employee")
    employee_name = fields.Char(string='Employee Name', help="Name")
    updated_date = fields.Date(string='Updated On', help="Location Updated Date")
    changed_field = fields.Char(string='Changed Field', help="Updated Field's")
    current_value = fields.Char(string='Current Location', help="Updated Value of Location")
    old_val = fields.Char(string='Old Location')


class JobHistory(models.Model):
    _name = 'job.history'
    _description = "Job history"
    _rec_name = "employee_name"

    employee_id = fields.Many2one('hr.employee')
    employee_name = fields.Char(string='Employee Name')
    designation_name = fields.Char(string='Employee designation')
    updated_date = fields.Date(string='End date')
    start_date = fields.Date(string='start Date')
    changed_field = fields.Char(string='Changed Field')
    current_value = fields.Char(string='Current job code')
    old_val = fields.Char(string='Old job code')
    current_dis = fields.Char(string='Current designation')
    old_dis = fields.Char(string='Old designation')
    state = fields.Selection([('expiry', 'Expired'), ('current', 'Current')])
    user_id = fields.Many2one('res.users', 'Changed by', default=lambda self: self.env.user)
