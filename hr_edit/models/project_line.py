# -*- coding: utf-8 -*-
from datetime import datetime, date
from odoo import models, api, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProjectLine(models.Model):
    _name = "project.line"
    _description = "Project line"
    _rec_name = "date"

    training = fields.Selection([('yes', 'YES'), ('no', 'NO'), ('banned', 'BANNED')], default='no', required=True)
    project_line = fields.Many2one('saftey.induction')
    job_code = fields.Many2one('job.codes')
    employee_id = fields.Many2one('hr.employee')
    designation = fields.Char('des')
    project = fields.Many2one('work.location')
    date = fields.Date('Date', default=fields.Date.today())
    put_change = fields.Boolean()
    current_project = fields.Many2one('work.location', compute='_compute_current_project',
                                      search='_search_current_project')

    def _search_current_project(self, operator, value):
        records = self.env['project.line'].sudo().search([]).filtered(
            lambda l: l.current_project and str(value) in l.current_project.name.lower())
        return [('id', 'in', records.ids)]

    def _compute_current_project(self):
        for rec in self:
            current = self.env['work.allocation'].sudo().search(
                [('employee_id', '=', rec.employee_id.id), ('date', '=', date.today())], limit=1)
            if current:
                rec.current_project = current.current_project.id
            else:
                rec.current_project = False

    @api.onchange('put_change', 'training')
    def _onchange_data(self):
        new_training = self.training
        record = self.project_line.mapped('all_project')
        for rec in record:
            if rec.put_change:
                lin = self.sudo().search([('id', '=', rec.id)])
                lin.write({'training': new_training, 'put_change': False})
