# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError
import logging
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class WorkAllocation(models.Model):
    _name = 'work.allocation'
    _description = "Work allocation"
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

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
              ]
             )
        ]

    job_code = fields.Many2one('job.codes', string='Job code', domain=_job_field_domain)
    employee_id = fields.Many2one('hr.employee', string='Employee', domain=_job_field_domain)
    designation = fields.Many2one(related='employee_id.job_id')
    level = fields.Char('Level')
    current_project = fields.Many2one('work.location', 'Current project')
    date = fields.Date('Date', default=fields.Date.today())
    active = fields.Boolean(default=True)
    leave = fields.Char('On leave', readonly=True)
    locked = fields.Boolean(default=False, copy=False, help="Locked list cannot be modified.")

    @api.model_create_multi
    def create(self, vals):
        res = super(WorkAllocation, self).create(vals)
        if res.check_duplicated():
            raise ValidationError(_("You can't create same data that exists before"))
        res.locked = True
        return res

    def check_duplicated(self):
        result = False
        # if self.env['work.allocation'].sudo().search_count(
        #         [('employee_id', '=', self.employee_id.id), ('date', '=', self.date)]) > 1:
        #     result = True
        #     _logger.info(".........................{}".format(self.env['work.allocation'].sudo().search_count(
        #         [('employee_id', '=', self.employee_id.id), ('date', '=', self.date)])))
        return result

    def test(self):
        pass

    def lock(self):
        self.locked = True

    def un_lock(self):
        self.locked = False

    @api.onchange('employee_id')
    def onchange_code(self):
        if self.employee_id:
            self.job_code = self.env['job.codes'].sudo().search([('employee_id', '=', self.employee_id.id)]).id

    @api.onchange('job_code')
    def onchange_employee(self):
        if self.job_code:
            self.employee_id = self.env['job.codes'].sudo().search([('id', '=', self.job_code.id)]).employee_id.id

    def create_allocation(self):
        
        transfer_employee = []

        if self.env['work.allocation'].sudo().search_count([]) == 0:
            for rec in self.env['hr.employee'].sudo().search(self._job_field_domain()):
                if self.env['hr.leave'].sudo().search(
                        [('employee_ids', 'in', [i.id for i in rec]), ('state', '=', 'validate')]).filtered(
                    lambda x: x.request_date_from <= fields.Date.today() and x.request_date_to >= fields.Date.today()):

                    self.env['work.allocation'].sudo().create({
                        'employee_id': rec.id,
                        'job_code': self.env['job.codes'].sudo().search([('employee_id', '=', rec.id)]).id,
                        'designation': rec.job_id.id,
                        'date': fields.Date.today(),
                        'leave': 'ON LEAVE at date %s' % fields.Date.today().strftime("%d/%m/%Y")

                    })


                else:

                    self.env['work.allocation'].sudo().create({
                        'employee_id': rec.id,
                        'job_code': self.env['job.codes'].sudo().search([('employee_id', '=', rec.id)]).id,
                        'designation': rec.job_id.id,
                        'date': fields.Date.today(),

                    })
        else:
            for rec in self.env['employee.transfer'].sudo().search(
                    [('state', '=', 'transfer'), ('date_update', '=', fields.Date.today())]):
                transfer_employee.append(rec.employee_id.id)

            for m in self.env['hr.leave'].sudo().search(
                    [('state', '=', 'validate'), ('request_date_from', '<=', fields.Date.today()),
                     ('request_date_to', '>=', fields.Date.today())]):

                for u in m.employee_ids:
                    transfer_employee.append(u.id)

            all_emp = list(dict.fromkeys(transfer_employee))

            employees_after_leave = [j.employee_ids for j in self.env['hr.leave'].sudo().search(
                [('state', '=', 'validate')]).filtered(
                lambda x: x.request_date_to + relativedelta(days=1) == fields.Date.today())]

            for i in employees_after_leave:
                for j in i:
                    emp = i.sudo().search(self._job_field_domain()).browse(j.id)
                    if self.env['work.allocation'].sudo().search_count(
                            [('employee_id', '=', emp.id), ('date', '=', fields.Date.today())]) == 0:
                        self.env['work.allocation'].sudo().create({
                            'employee_id': emp.id,
                            'job_code': self.env['job.codes'].sudo().search([('employee_id', '=', emp.id)]).id,
                            'designation': emp.job_id.id,
                            'date': fields.Date.today(),

                        })

            employee_leave = [j.employee_ids for j in self.env['hr.leave'].sudo().search(
                [('state', '=', 'validate'), ('request_date_from', '<=', fields.Date.today()),
                 ('request_date_to', '>=', fields.Date.today())])]

            for rec in employee_leave:
                for j in rec:

                    emp = rec.search(self._job_field_domain()).browse(j.id)
                    if self.env['work.allocation'].sudo().search_count(
                            [('employee_id', '=', emp.id), ('date', '=', fields.Date.today())]) == 0:
                        self.env['work.allocation'].sudo().create({
                            'employee_id': j.id,
                            'job_code': self.env['job.codes'].sudo().search([('employee_id', '=', emp.id)]).id,
                            'designation': emp.job_id.id,
                            'date': fields.Date.today(),
                            'leave': 'ON LEAVE at date %s' % fields.Date.today().strftime("%d/%m/%Y")

                        })

            for rec in self.env['work.allocation'].sudo().search([('employee_id', 'not in', all_emp)]).filtered(
                    lambda x: x.date + relativedelta(days=1) == fields.Date.today()):

                if rec.current_project.state == 'active':
                    if self.env['project.line'].sudo().search_count(
                            [('training', '=', 'banned'), ('employee_id', '=', rec.employee_id.id),
                             ('project', '=', rec.id)]) == 0:
                        self.env['work.allocation'].sudo().create({
                            'employee_id': rec.employee_id.id,
                            'job_code': rec.job_code.id,
                            'current_project': rec.current_project.id,
                            'designation': rec.designation.id,
                            'date': rec.date + relativedelta(days=1),
                            'level': rec.level

                        })
                if rec.current_project.state == 'hold':
                    if self.env['project.line'].sudo().search_count(
                            [('training', '=', 'banned'), ('employee_id', '=', rec.employee_id.id),
                             ('project', '=', rec.id)]) == 0:
                        self.env['work.allocation'].sudo().create({
                            'employee_id': rec.employee_id.id,
                            'job_code': rec.job_code.id,
                            'current_project': False,
                            'designation': rec.designation.id,
                            'date': rec.date + relativedelta(days=1),
                            'level': rec.level

                        })
                if not rec.current_project and not rec.leave:
                    self.env['work.allocation'].sudo().create({
                        'employee_id': rec.employee_id.id,
                        'job_code': rec.job_code.id,
                        'current_project': False,
                        'designation': rec.designation.id,
                        'date': rec.date + relativedelta(days=1),
                        'level': rec.level

                    })
