# -*- coding: utf-8 -*-
from datetime import datetime, date
from odoo import models, api, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SafteyInduction(models.Model):
    _name = 'saftey.induction'
    _description = "Saftey induction"
    @api.model
    def _job_field_domain(self):
        return [
            ('job_id', 'in',
             [self.env.ref('hr_edit.prep').id,
              self.env.ref('hr_edit.plaster').id,
              self.env.ref('hr_edit.operation').id,
              self.env.ref('hr_edit.rush').id,
              self.env.ref('hr_edit.block').id,
              self.env.ref('hr_edit.helper').id,
              self.env.ref('hr_edit.tile_m').id,
              self.env.ref('hr_edit.tile_h').id,
              self.env.ref('hr_edit.foreman').id,
              self.env.ref('hr_edit.area_manager').id,
              self.env.ref('hr_edit.quantity_surveyor').id,
              self.env.ref('hr_edit.civil_engineer').id,
              ]
             )
        ]

    _inherit = ['mail.thread', 'mail.activity.mixin']
    job_code = fields.Many2many('job.codes', string='Job code', domain=_job_field_domain)
    employee_id = fields.Many2many('hr.employee', string='Employee', domain=_job_field_domain)
    designation = fields.Char('designation')
    current_project = fields.Many2one('work.location', 'Current project')
    date = fields.Date('Date', default=fields.Date.today())
    all_project = fields.Many2many('project.line', 'Projects')
    state = fields.Selection([('active', 'Active'), ('on_leave', 'On leave')])

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        
        for vals in vals_list:
            if 'all_project' in vals:
    
                for rec in vals['all_project']:
                    
            
                    self.env['project.line'].sudo().browse(rec[1]).project_line = res.id
        lines = self.env['project.line'].sudo().search([])
        for i in lines:
            if not i.project_line:
                i.unlink()
        return res

    def write(self, vals):
        res = super().write(vals)

        if 'all_project' in vals:
            for rec in vals['all_project']:
                self.env['project.line'].sudo().browse(rec[1]).project_line = self.id
        lines = self.env['project.line'].sudo().search([])
        for i in lines:
            if not i.project_line:
                i.unlink()
        return res

    @api.onchange('employee_id')
    def onchange_code(self):

        if self.employee_id:
            import re
            emp = [int(str(i.id).split("_", 1)[1]) for i in self.employee_id]
            all_jobs = self.env['job.codes'].sudo().search([('employee_id', 'in', emp)])

            self.job_code = [(6, 0, [i.id for i in all_jobs])]
        else:
            self.job_code = [(6, 0, [])]

    @api.onchange('job_code')
    def onchange_employee(self):
        if self.job_code:
            code = [int(str(i.id).split("_", 1)[1]) for i in self.job_code]
            all_employees = self.env['job.codes'].sudo().search([('id', 'in', code)])

            self.employee_id = [(6, 0, [i.employee_id.id for i in all_employees])]
        else:

            self.employee_id = [(6, 0, [])]

    @api.onchange('job_code', 'employee_id')
    def create_line(self):

        if self.job_code and self.employee_id:
            self.all_project = [(6, 0, [])]

            emp = [int(str(i.id).split("_", 1)[1]) for i in self.employee_id]
            code = [int(str(i.id).split("_", 1)[1]) for i in self.job_code]

            for pro in self.env['work.location'].sudo().search([('state', 'in', ['active', 'hold'])]):

                for rec in emp:

                    if self.env['project.line'].sudo().search_count([('employee_id', '=', rec), (
                    'job_code', '=', self.env['job.codes'].sudo().search([('employee_id', '=', rec)]).id),
                                                                     ('project', '=', pro.id)]) == 0:

                        projects = self.env['project.line'].sudo().create({
                            'job_code': self.env['job.codes'].sudo().search([('employee_id', '=', rec)]).id,
                            'employee_id': rec,
                            'designation': self.env['hr.employee'].sudo().search([('id', '=', rec)]).job_id.name,
                            'project': pro.id,

                        })

                        self.all_project = [(4, projects.id)]
                    else:

                        old_projects = self.env['project.line'].sudo().search(
                            [('employee_id', 'in', emp), ('job_code', 'in', code), ('project', '=', pro.id)])
                        for i in old_projects:
                            self.all_project = [(4, i.id)]


