# -*- coding: utf-8 -*-
from datetime import datetime, date
from odoo import models, api, fields, _
from odoo.exceptions import UserError
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class WorkLocation(models.Model):
    _name = 'work.location'
    _description = "Work location"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'state,name'

    name = fields.Char()
    foreman = fields.Many2many('hr.employee', 'Foreman')
    state = fields.Selection([('active', 'Active'), ('hold', 'Hold'), ('completed', 'Completed')],
                             string='Project Status', tracking=1, default='active', required=True)
    complete_date = fields.Date(string="Completed Date", tracking=1)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.company,
                                 help="Company")

    @api.onchange('state')
    def _change_state(self):
        for rec in self:
            if rec.state == 'completed':
                rec._origin.complete_date = date.today()

    def get_designations(self):
        """Helper method to get the list of designation IDs."""
        return [
            self.env.ref('hr_edit.prep').id,
            self.env.ref('hr_edit.plaster').id,
            self.env.ref('hr_edit.operation').id,
            self.env.ref('hr_edit.rush').id,
            self.env.ref('hr_edit.block').id,
            self.env.ref('hr_edit.tile_h').id,
            self.env.ref('hr_edit.tile_m').id,
            self.env.ref('hr_edit.helper').id,
        ]

    def get_data_for_report(self, domain=[]):
        """Fetches the report data for the specified domain."""
        worker_data_list = []
        designations = self.get_designations()
        projects = self.env['work.allocation'].sudo().search(domain).mapped('current_project')

        for project in projects:
            workers_count_per_designation = []
            for designation in designations:
                search_domain = [('designation', '=', designation), ('current_project', '=', project.id),('date','=',fields.Date.today())]
                workers_count = self.env['work.allocation'].sudo().search_count(search_domain)
                workers_count_per_designation.append(workers_count)

            worker_data_list.append({
                'project': project.name,
                'workers_count': workers_count_per_designation,
                'total_workers': sum(workers_count_per_designation),
                'foreman': self.get_foreman_names(project),
            })

        return worker_data_list

    def get_foreman_names(self, project):
        """Returns a comma-separated string of foreman names for a project."""
        return ','.join(foreman.name for foreman in project.foreman)

    def get_data_body(self):
        """Generates data for the report body."""
        domain = [('current_project', 'in', self.ids),('date','=',fields.Date.today())]
        return self.get_data_for_report(domain=domain)

    def get_data_total(self):
        """Calculates the total number of workers for each designation and overall."""
        total_workers_per_designation = []
        overall_total = 0
        designations = self.get_designations()

        for designation in designations:
            search_domain = [('current_project', 'in', self.ids),('date','=',fields.Date.today()), ('designation', '=', designation)]
            workers_count = self.env['work.allocation'].sudo().search_count(search_domain)
            overall_total += workers_count
            total_workers_per_designation.append(workers_count)

        total_workers_per_designation.append(overall_total)
        return total_workers_per_designation

    def open_print(self):
        """Action to print the report."""
        records = self if self else self.env['work.location'].sudo().search([])
        return self.env.ref('hr_edit.report_project_workers_pdf').report_action(records)

