# -*- coding: utf-8 -*-
from odoo import api, _, fields, models, tools
from datetime import datetime, timedelta
import logging
import calendar
from dateutil.relativedelta import relativedelta

from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

class LeaveِAllocationInherit(models.Model):
    _inherit = 'hr.leave.allocation'
    def check_max_allocation(self, employees, annual_leave):
        all_alloc = 0
        allocation_max = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.allocation_max'))
        for emp in employees:
            employee = emp[1] if type(emp) == [] else emp
            all_alloc = sum([alloc.number_of_days for alloc in self.env['hr.leave.allocation'].sudo().search(
                [("holiday_status_id", "=", annual_leave),
                 ('employee_id', '=', employee),
                 ('state', '=', 'validate')])])
            return True if all_alloc >= allocation_max else False
    
    @api.model_create_multi
    def create(self, vals_list):
        """ Override to avoid automatic logging of creation """
        for values in vals_list:
            annual_leave = self.env.ref("hr_edit.annual_leave").id
            
            if 'number_of_days' in values and 'holiday_status_id' in values and values['holiday_status_id'] == annual_leave and 'employee_ids' in values:
                if self.check_max_allocation(values['employee_ids'], annual_leave):
                    raise UserError(_('You have exceeded the number of allowed allocations.'))
        return super(LeaveِAllocationInherit, self.with_context(mail_create_nosubscribe=True)).create(vals_list)
 
    def write(self, values):
        alloc = super(LeaveِAllocationInherit, self).write(values)
        annual_leave = self.env.ref("hr_edit.annual_leave").id
        if self.check_max_allocation(self.employee_ids.ids, annual_leave):
            raise UserError(_('You have exceeded the number of allowed allocations.'))
        return alloc
class LeaveInherit(models.Model):
    _inherit = 'hr.leave'

    passport_num = fields.Char("passport", compute='_compute_passport_num')
    passport_issue_date = fields.Date("passport issue date", compute='_compute_passport_num')
    passport_expire_date = fields.Date("passport expiry date", compute='_compute_passport_num')
    job_code = fields.Many2many('job.codes', string='Job code')
    eid_num = fields.Char("EID", compute='_compute_eid_num')
    eid_issue_date = fields.Date("EID issue date", compute='_compute_eid_num')
    eid_expire_date = fields.Date("EID expiry date", compute='_compute_eid_num')
    uid_num = fields.Char("UID", compute='_compute_uid_num')
    designation = fields.Many2one(related='employee_id.job_id')
    department = fields.Many2one(related='employee_id.department_id')
    resuming_work_date = fields.Date('Resuming Work Date', compute='_compute_resuming_work_date')
    assets = fields.Many2many('maintenance.equipment', 'Assets')
    employee_pur_ticket = fields.Boolean()
    ticket_price = fields.Monetary(group_operator='sum', )
    hold = fields.Monetary(group_operator='sum', )
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, string="Currency")
    paid = fields.Boolean('Paid')
    def _compute_eid_num(self):
        for record in self:
            if record.employee_ids:
                doc = self.env['hr.employee.document'].sudo().search([('employee_ref_id', '=', record.employee_id.id),
                                                                      ('document_type_id', '=',
                                                                       self.env.ref(
                                                                           'oh_employee_documents_expiry.document_type_06').id)],
                                                                     order='id desc',
                                                                     limit=1)
                record.eid_num = doc.name if len(doc) != 0 else ''
                record.eid_issue_date = doc.issue_date if len(doc) != 0 else False
                record.eid_expire_date = doc.expiry_date if len(doc) != 0 else False
            else:
                record.eid_num = ''
                record.eid_issue_date = False
                record.eid_expire_date = False

    def _compute_passport_num(self):
        for record in self:
            if record.employee_ids:
                doc = self.env['hr.employee.document'].sudo().search(
                    [('employee_ref_id', '=', record.employee_id.id),
                     ('document_type_id', '=',
                      self.env.ref(
                          'oh_employee_documents_expiry.document_type_02').id)],
                    order='id desc',
                    limit=1)
                record.passport_num = doc.name if len(doc) != 0 else ''
                record.passport_issue_date = doc.issue_date if len(doc) != 0 else False
                record.passport_expire_date = doc.expiry_date if len(doc) != 0 else False
            else:
                record.passport_num = ''
                record.passport_issue_date = False
                record.passport_expire_date = False

    @api.onchange('employee_ids')
    def onchange_code(self):

        if self.employee_ids :
            import re
            emp = [int(str(i.id).split("_", 1)[1]) for i in self.employee_ids]
            all_jobs = self.env['job.codes'].sudo().search([('employee_id', 'in', emp)])

            self.job_code = [(6, 0, [i.id for i in all_jobs])]
        else:
            self.job_code = [(6, 0, [])]

    @api.onchange('job_code')
    def onchange_employee(self):
        if self.job_code:
            code = [int(str(i.id).split("_", 1)[1]) for i in self.job_code]
            all_employees = self.env['job.codes'].sudo().search([('id', 'in', code)])

            self.employee_ids = [(6, 0, [i.employee_id.id for i in all_employees])]
        else:

            self.employee_ids = [(6, 0, [])]

    def _compute_uid_num(self):
        for record in self:
            if record.employee_ids:
                for rec in record.employee_ids:
                    doc = self.env['hr.employee.document'].sudo().search(
                        [('employee_ref_id', '=', rec.id),
                         ('document_type_id', '=',
                          self.env.ref(
                              'oh_employee_documents_expiry.document_type_07').id)],
                        order='id desc',
                        limit=1)
                    record.uid_num = doc.name if len(doc) != 0 else ''

                else:
                    record.uid_num = ''

    def _compute_resuming_work_date(self):
        for rec in self:
            if rec.request_date_to:

                day_work = rec.request_date_to + relativedelta(days=1)

                all_existing_leaves = self.env['resource.calendar.leaves'].sudo().search(
                    [('resource_id', '=', False)]).filtered(
                    lambda l: l.date_to.date() == day_work
                )

                rec.resuming_work_date = day_work if len(all_existing_leaves) == 0 else all_existing_leaves[
                                                                                            -1].date_to.date() + relativedelta(
                    days=1)


            else:
                rec.resuming_work_date = False
                rec.assets = False

    @api.model_create_multi
    def create(self, vals):
        res = super(LeaveInherit, self).create(vals)
        assets = self.env['maintenance.equipment'].sudo().search(
            [('employee_id', 'in', [i.id for i in res.employee_id]),
             ('dismissed_date', '=', False),
             ])
        res.assets = [(6, 0, [i.id for i in assets])]
        return res

    def action_approve(self):
        res = super(LeaveInherit, self).action_approve()
        max_days = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.limit_number_of_day_staff_foreman'))
        # if self.number_of_days >= max_days:
        allocations = self.env['hr.leave.allocation'].sudo().search([('employee_id', 'in', self.employee_ids.ids), (
            "holiday_status_id", "=", self.holiday_status_id.id), ('state', '=', 'validate')])
        for rec in allocations:
            rec.state = 'refuse'
            rec.active = False
        if self.employee_id.type_work in ['staff_for', 'labor_a']:
            complete_staff_foreman_period = float(self.env['ir.config_parameter'].sudo().get_param(
                'hr_edit.complete_staff_foreman_period')) * 12
            self.employee_id.next_schedule_date = self.date_to.date() + relativedelta(
                months=int(complete_staff_foreman_period))
        elif self.employee_id.type_work == 'labor_n':
            complete_labor_n_period = float(self.env['ir.config_parameter'].sudo().get_param(
                'hr_edit.complete_labor_n_period')) * 12
            self.employee_id.next_schedule_date = self.date_to.date() + relativedelta(
                months=int(complete_labor_n_period))
