# -*- coding: utf-8 -*-
from datetime import date
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import logging

_logger = logging.getLogger(__name__)


class EmployeeTransfer(models.Model):
    _name = 'employee.transfer'
    _description = 'Employee Transfer'
    _order = "id desc,date desc,date_update desc"

    def _default_employee(self):
        emp_ids = self.env['hr.employee'].search([
            ('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    name = fields.Char(string='Name', help='Give a name to the Transfer',readonly=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Employee',
        required=True,
        help='Select the employee you are going to transfer')
    job_code = fields.Many2one('job.codes', string='Job code')

    date = fields.Date(string='Create Date', default=fields.Date.today(), readonly=True)
    date_update = fields.Date(string='Transfer Date', default=fields.Date.today() + relativedelta(days=1), help="Date")
    work_id = fields.Many2one('work.location', string='New Project',
                              help="Transferring Location",
                              copy=False, required=True)
    foreman_new = fields.Many2many(related='work_id.foreman', string='New Project Foreman Name')
    from_work_id = fields.Many2one('work.location', string='Current Project',
                                   copy=False, compute='_compute_from_work_id')
    foreman_current = fields.Many2many(related='from_work_id.foreman', string='Current Project Foreman Name')
    state = fields.Selection(
        [('draft', 'New'), ('cancel', 'Cancelled'), ('transfer', 'Transferred'),
         ],
        string='Status', readonly=True, copy=False, default='draft',
        help=" * The 'Draft' status is used when a transfer is created and unconfirmed Transfer.\n"
             " * The 'Transferred' status is used when the user confirm the transfer. It stays in the open status till the other location receive the employee.\n"

             " * The 'Cancelled' status is used when user cancel Transfer.")
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.company,
                                 help="Company")
    note = fields.Text(string='Internal Notes',
                       help="Specify notes for the transfer if any")

    responsible = fields.Many2one('hr.employee', string='Responsible',
                                  default=_default_employee, readonly=True,
                                  help="Responsible person for the transfer")
    safety = fields.Char('Safety Induction', compute='_compute_safety')
    country_id = fields.Many2one(related='employee_id.country_id', string='Nationality')
    passport_id = fields.Char(related='employee_id.passport_id', string='Passport Number')
    eid_num = fields.Char("Emirates ID", compute='_compute_eid_num')
    job_position = fields.Many2one(related='employee_id.job_id')
    active_company_bbc = fields.Text(compute='_compute_active_company_bbc')
    lock_date = fields.Boolean(compute='_compute_lock_date')

    def _compute_lock_date(self):
        for rec in self:
            lock_date = False
            lock_data_after = float(self.env['ir.config_parameter'].sudo().get_param(
                'hr_edit.lock_data_after')) or 2
            if rec.date_update + timedelta(days=int(lock_data_after)) <= date.today():
                lock_date = True
            rec.lock_date = lock_date

    @api.depends('employee_id')
    def _compute_active_company_bbc(self):
        for rec in self:
            if rec.employee_id and rec.employee_id.on_company_sponsorship == 'yes':
                active_company_bbc = rec.employee_id.branch
            elif rec.employee_id and rec.employee_id.on_company_sponsorship == 'no':
                active_company_bbc = rec.employee_id.sponsor_name
            else:
                active_company_bbc = ''
            rec.active_company_bbc = active_company_bbc

    @api.onchange('employee_id')
    def _compute_eid_num(self):
        for record in self:
            if record.employee_id:
                doc = self.env['hr.employee.document'].sudo().search([('employee_ref_id', '=', record.employee_id.id),
                                                                      ('document_type_id', '=',
                                                                       self.env.ref(
                                                                           'oh_employee_documents_expiry.document_type_07').id)],
                                                                     order='id desc',
                                                                     limit=1)
                record.eid_num = doc.name if len(doc) != 0 else ''
            else:
                record.eid_num = ''

    @api.onchange('employee_id')
    def onchange_code(self):
        for rec in self:
            if rec.employee_id:
                rec.job_code = self.env['job.codes'].sudo().search([('employee_id', '=', rec.employee_id.id)]).id

    @api.onchange('job_code')
    def onchange_employee(self):
        if self.job_code:
            self.employee_id = self.env['job.codes'].sudo().search([('id', '=', self.job_code.id)]).employee_id.id

    @api.depends('employee_id')
    def _compute_from_work_id(self):
        for rec in self:
            if rec.employee_id and rec.date_update:
                location_current = self.env['work.allocation'].sudo().search(
                    [('employee_id', '=', rec.employee_id.id), ('date', '=', rec.date)], limit=1)

                rec.from_work_id = location_current.current_project.id
            else:
                rec.from_work_id = False

    @api.depends('work_id')
    def _compute_safety(self):
        for rec in self:
            if rec.work_id and rec.date_update:
                location_current = self.env['project.line'].sudo().search(
                    [('employee_id', '=', rec.employee_id.id), ('project', '=', rec.work_id.id)], limit=1).training

                rec.safety = str(location_current).upper() if location_current else 'NO'
            else:
                rec.safety = 'NO'

    def create_allocation(self):
        self.env['work.allocation'].sudo().create({'job_code': self.job_code.id,
                                                   'employee_id': self.employee_id.id,
                                                   'designation': self.employee_id.job_id.id,
                                                   'current_project': self.work_id.id,
                                                   'date': self.date_update,
                                                   })

    def transfer(self):
        for rec in self:
            if not rec.work_id:
                raise UserError(_(
                    'You should select the location.'))
            if rec.work_id == rec.from_work_id:
                raise UserError(_(
                    'You cannot transfer to the same location.'))
            rec.state = 'transfer'
            old_val = rec.employee_id.location_id.name
            rec.employee_id.location_id = rec.work_id.id
            rec.change_location(old_val)
            if rec.work_id.state != 'active':
                raise UserError(_(
                    'You cannot transfer to the location not in active state.'))
            if rec.safety == 'BANNED':
                raise UserError(_(
                    'You cannot transfer this employee (Banned from this location).'))
            if self.env['work.allocation'].sudo().search([('date','=',rec.date_update),('employee_id','=',rec.employee_id.id)]):
                  raise UserError(_(
                    'You cannot transfer this employee , He has allocation in this day.'))
            rec.create_allocation()

    def change_location(self, old_val):
        vals = {
            'employee_id': self.employee_id.id,
            'employee_name': self.employee_id.name,
            'updated_date': datetime.now(),
            'changed_field': 'Location',
            'current_value': self.work_id.name,
            'old_val': old_val,

        }
        self.env['location.history'].sudo().create(vals)

    def cancel_transfer(self):
        for rec in self:
            rec.state = 'cancel'
            allocation = self.env['work.allocation'].sudo().search([('job_code', '=', rec.job_code.id),
                                                                    ('employee_id', '=', rec.employee_id.id),
                                                                    ('designation', '=', rec.employee_id.job_id.id),
                                                                    ('current_project', '=', rec.work_id.id),
                                                                    ('date', '=', rec.date_update),
                                                                    ])
            if allocation:
                allocation.active = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
         
            vals['name'] = "Transfer: " + self.env['hr.employee'].browse(vals['employee_id']).name
        res = super(EmployeeTransfer, self).create([{
            **vals,
        } for vals in vals_list])
        if self.search([('date','=',res.date),('id','!=',res.id),('state','!=','cancel'),
        ('employee_id','=',res.employee_id.id),('date_update','=',res.date_update)]):
            raise UserError(_(
                    'You cannot create more than one trransef in the same date %s for this employee %s .')%(res.date,res.employee_id.name))
            
        return res
