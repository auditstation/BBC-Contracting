# -*- coding: utf-8 -*-
import math
from collections import defaultdict

from odoo import models, fields, api, _, exceptions
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
import time
from datetime import date, datetime, timedelta
import calendar
from dateutil.parser import parse
import logging
import pytz
import requests
from odoo import http
from odoo.http import request
import calendar

from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError

import math
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


def get_days_without_sundays(start_date, end_date, without_day):
    if start_date > end_date:
        raise ValueError("Start date must be before or equal to end date")

    for i in without_day:
        days_excluding_sundays = []
        current_date = start_date
        while current_date <= end_date:

            if current_date.weekday() != i - 1:
                days_excluding_sundays.append(current_date)
            current_date += timedelta(days=1)

    return days_excluding_sundays


def diff_hour(h1, h2, m3, m4):
    res = ((((h1 - h2) * 60 + m3 - m4)) / 60)
    return res


def get_days(date_to):
    res = calendar.monthrange(date_to.year, date_to.month)[1]
    return res


def diff_month_2(d1, d2):
    return ((d1.year - d2.year) * 12 + d1.month - d2.month) + 1


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month

def get_all_days_in_range(from_date, to_date):
    # Convert input strings to datetime objects if needed
    if isinstance(from_date, str):
        from_date = datetime.strptime(from_date, '%Y-%m-%d')
    if isinstance(to_date, str):
        to_date = datetime.strptime(to_date, '%Y-%m-%d')

    # Initialize list to hold all dates
    all_days = []

    # Loop through each day in the range
    current_date = from_date
    while current_date <= to_date:
        all_days.append(current_date.day)
        current_date += timedelta(days=1)

    return all_days
def get_sundays(year, month):
    # Create a calendar object for the month and year
    cal = calendar.Calendar()

    # Get all the days for the specified month
    sundays = [day for day in cal.itermonthdays2(year, month) if day[0] != 0 and day[1] == calendar.SUNDAY]

    return [day[0] for day in sundays]
class PayslipEdit(models.Model):
    _inherit = "hr.payslip"

    sal_adv = fields.Float(string="Salary Advance", compute='_compute_sal_adv')
    have_sal_adv = fields.Boolean(compute='_compute_sal_adv')
    sal_adv_id = fields.Binary(compute='_compute_sal_adv')


    count_unpaid = fields.Float(string="Days of leave", compute='_compute_count_unpaid')
    absent_amount = fields.Float('loses days', compute='_compute_absent_amount')
    emirates_ded = fields.Boolean('Emirates Deduction', compute='_compute_emirates_ded')
    equip_ded = fields.Boolean('Equipments Deduction', compute='_compute_equip_ded')
    other_dec = fields.Float('Other Deduction')
    other_bonus = fields.Float('Other Bonus')
    job_code = fields.Many2one('job.codes', invisible=0,
                               copy=False,
                               help='Specify the job code.')
    count_work_in_holiday = fields.Float(string="Days of leave", compute='_compute_count_work_in_holiday')
    # Helper
    helper_hour = fields.Float('Helper Hour', compute='_compute_helper_hour')
    non_absent_hour = fields.Float('Absence Hour', compute='_compute_non_absent_hour')
    operator_absent_hour = fields.Float('Absence Hour', compute='_compute_operator_absent_hour')
    safety_fines = fields.Float('Safety fines')
    rush_coat = fields.Float(compute='_compute_helper_hour')
    # others = fields.Float('Others')
    gas_ded = fields.Float('GAS')
    # Mason Field
    two_day_ded_mason = fields.Float(compute='_compute_mason')
    wall_tiles = fields.Float(compute='_compute_mason')
    parquet_tiles = fields.Float(compute='_compute_mason')
    floor_tiles = fields.Float(compute='_compute_mason')
    skirting = fields.Float(compute='_compute_mason')
    layout_tiles = fields.Float(compute='_compute_mason')
    layout_block = fields.Float(compute='_compute_mason')
    mosaic = fields.Float(compute='_compute_mason')
    threshold = fields.Float(compute='_compute_mason')
    point_hour = fields.Float(compute='_compute_mason')
    external_plaster_hour = fields.Float(compute='_compute_mason')
    internal_plaster_hour = fields.Float(compute='_compute_mason')
    internal_angles_hour = fields.Float(compute='_compute_mason')
    external_angles_hour = fields.Float(compute='_compute_mason')
    hollow_hour = fields.Float(compute='_compute_mason')
    aac_sob_hour = fields.Float(compute='_compute_mason')
    point_s = fields.Float(compute='_compute_mason')
    point_external = fields.Float(compute='_compute_mason')
    # Hold
    hold_amount_ded = fields.Float('Hold', compute='_compute_hold')
    hold_amount_add = fields.Float('Hold', compute='_compute_hold',readonly=False)
    # ticket_price = fields.Float(compute='_compute_hold')
    time_off_id = fields.Binary(compute='_compute_hold')
    plaster_bonus = fields.Float()
    allotted_bonus = fields.Float()
    hour_holiday = fields.Float(compute='_compute_hour_holiday')
    days = fields.Integer(compute="_compute_days")
    amount = fields.Float(compute="_compute_amount")
    absense_days = fields.Float(compute='_compute_mason')
    last_hold = fields.Float(compute='_compute_last_hold',readonly=False,store=True)
    paid_hold = fields.Boolean()
    
    @api.depends('line_ids.total')
    def _compute_last_hold(self):
        line_values = (self._origin)._get_line_values(['HOLDB'])
        for payslip in self:
            payslip.last_hold = line_values['HOLDB'][payslip._origin.id]['total']


    def action_open_payslip_2(self):
        if self.env.context.get('default_payslip_run_id'):
            domain=[('last_hold', '!=', 0),('state','not in',['paid','cancel','done']),'|',('payslip_run_id','=',False),('payslip_run_id','=',self.env.context.get('default_payslip_run_id'))]
        else:
            domain=[('last_hold', '!=', 0),('state','not in',['paid','cancel','done'])]
        return {
            'name': 'Payslip',
            'domain': domain,
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'view_id':self.env.ref('hr_edit.open_payslip_view_2').id,
            'view_mode': 'tree',
            'limit': 80,
        }
    def get_month_name(self, month_number):
        return calendar.month_name[int(month_number)]
    @api.depends('employee_id')
    def _compute_days(self):
        for rec in self:
            if rec.date_to and rec.date_from:
                # rec.days = (rec.date_to - rec.date_from).days
                rec.days = len([i for i in rec.env['production.line'].sudo().search([
                    ('employee_id', "=", rec.employee_id.id),
                    ('start_date', '>=', rec.date_from),
                    ('start_date', '<=', rec.date_to),
                    ('absence', 'not in', ['1', '2'])
                ]).filtered(lambda l: l.start_date.weekday() != 6 and not l.leave)])
            else:
                rec.days = 0

    def _compute_amount(self):
        for rec in self:
            if rec.line_ids:
                rec.amount = rec.line_ids[-1].total
            else:
                rec.amount = 0

    @api.depends('employee_id')
    def _compute_hour_holiday(self):
        hour = 0
        for payslip in self:
            public_holiday = self.env['resource.calendar.leaves'].search([
                '|', ('company_id', 'in', payslip.employee_id.mapped('company_id').ids),
                ('company_id', '=', False),
                ('resource_id', '=', False),
                ('date_from', '>=', payslip.date_from),
                ('date_to', '<=', payslip.date_to),
            ], order='date_from')
            for i in public_holiday:
                all_leave = self.env['hr.leave'].sudo().search(
                    [('employee_ids', 'in', [i.id for i in payslip.employee_id]), ('state', '=', 'validate'), ]
                ).filtered(lambda lev: (
                                               lev.date_from.date() <= i.date_from.date() and lev.date_to.date() >= i.date_from.date() and lev.date_to.date().month == i.date_to.month) or
                                       (
                                               lev.date_from.date() >= i.date_from.date() and lev.date_to.date() >= i.date_to.date() and lev.date_from.date().month == i.date_from.month) or
                                       (lev.request_date_from >= i.date_from.date() and lev.request_date_to <= i.date_to.date()))

                if all_leave:
                    hour += 0
                else:
                    hour += 8
            payslip.hour_holiday = hour

    @api.depends('employee_id')
    def _compute_hold(self):
        for payslip in self:
           
            all_leave = self.env['hr.leave'].sudo().search(
                [('employee_ids', 'in', [i.id for i in payslip.employee_id]), ('state', '=', 'validate')])
            
            all_leave_hold = all_leave.filtered(lambda
                                                    l: l.hold != 0 and l.payslip_state == 'blocked' and (
                    l.request_date_from >= payslip.date_from and l.request_date_from.month == payslip.date_from.month))
            
            all_leave_hold_add = all_leave.filtered(lambda l: l.hold != 0 and l.payslip_state == 'normal' and l.request_date_to < payslip.date_to)
           
            hold_amount_ded = sum(
                [rec.hold for rec in all_leave_hold]) or 0
            hold_amount_add = sum(
                [rec.hold for rec in all_leave_hold_add ]) or 0
            # ticket_price = sum([rec.ticket_price for rec in all_leave.filtered(lambda l: l.ticket_price != 0 and l.payslip_state == 'blocked')]) or 0
            payslip.hold_amount_ded = hold_amount_ded
            payslip.hold_amount_add = hold_amount_add
            # payslip.ticket_price = ticket_price
            all_leave_hold_time_off_ids = all_leave.filtered(lambda
                                                    l: l.hold != 0 and (l.payslip_state == 'blocked' and (
                    l.request_date_from >= payslip.date_from and l.request_date_from.month == payslip.date_from.month) or l.payslip_state == 'normal' and l.request_date_to < payslip.date_to)   )
            payslip.time_off_id = all_leave_hold_time_off_ids.ids


    def get_missing_days_of_week(self, calendar_id):
        calendar = self.env['resource.calendar'].browse(calendar_id)
        working_days = {int(attendance.dayofweek) for attendance in calendar.attendance_ids}
        all_days = set(range(7))
        missing_days = all_days - working_days
        day_names = [1, 2, 3, 4, 5, 6, 7]
        missing_day_names = [day_names[day] for day in missing_days]

        return missing_day_names

    @api.depends('employee_id')
    def _compute_mason(self):
        for pay in self:
            two_day_ded_mason = float(self.env['ir.config_parameter'].sudo().get_param(
                'hr_edit.two_day_ded_wall_tiles')) or 10
            active_production_wall_tiles = 0.0
            active_production_parquet_tiles = 0.0
            active_production_floor_tiles = 0.0
            active_production_skirting = 0.0
            active_production_layout_tiles = 0.0
            active_production_threshold = 0.0
            active_production_point_hour = 0.0
            active_production_external_plaster_hour = 0.0
            active_production_internal_plaster_hour = 0.0
            active_production_internal_angles_hour = 0.0
            active_production_external_angles_hour = 0.0
            active_production_hollow_hour = 0.0
            active_production_aac_sob_hour = 0.0
            active_production_point_s = 0.0
            active_production_point_external = 0.0
            active_production_layout_block = 0.0
            active_production_mosaic = 0.0
            absense_days = 0.0
            production_mason = pay.env['production.line'].sudo().search([
                ('employee_id', "=", pay.employee_id.id),
                ('start_date', '>=', pay.date_from),
                ('start_date', '<=', pay.date_to),
                
            ]).filtered(lambda l: l.start_date.weekday() != 6 and not l.leave)
            active_production_wall_tiles = sum(
                [rec.wall_tiles for rec in production_mason.filtered(lambda l: not l.absence and l.wall_tiles != 0)])
            active_production_parquet_tiles = sum(
                [rec.parquet_tiles for rec in
                 production_mason.filtered(lambda l: not l.absence and l.parquet_tiles != 0)])
            active_production_floor_tiles = sum(
                [rec.floor_tiles for rec in
                 production_mason.filtered(lambda l: not l.absence and l.floor_tiles != 0)])
            active_production_skirting = sum(
                [rec.skirting for rec in
                 production_mason.filtered(lambda l: not l.absence and l.skirting != 0)])
            active_production_layout_tiles = sum(
                [rec.layout_tiles for rec in
                 production_mason.filtered(lambda l: not l.absence and l.layout_tiles != 0)])
            active_production_threshold = sum(
                [rec.hreshold for rec in
                 production_mason.filtered(lambda l: not l.absence and l.hreshold != 0)])
            active_production_point_hour = sum(
                [rec.point_hour for rec in
                 production_mason.filtered(lambda l: not l.absence and l.point_hour != 0)])
            active_production_external_plaster_hour = sum(
                [rec.external_plaster_hour for rec in
                 production_mason.filtered(lambda l: not l.absence and l.external_plaster_hour != 0)])
            active_production_internal_plaster_hour = sum(
                [rec.internal_plaster_hour for rec in
                 production_mason.filtered(lambda l: not l.absence and l.internal_plaster_hour != 0)])
            active_production_internal_angles_hour = sum(
                [rec.internal_angles_hour for rec in
                 production_mason.filtered(lambda l: not l.absence and l.internal_angles_hour != 0)])
            active_production_external_angles_hour = sum(
                [rec.external_angles_hour for rec in
                 production_mason.filtered(lambda l: not l.absence and l.external_angles_hour != 0)])
            active_production_hollow_hour = sum(
                [rec.hollow_hour for rec in
                 production_mason.filtered(lambda l: not l.absence and l.hollow_hour != 0)])
            active_production_aac_sob_hour = sum(
                [rec.aac_sob_hour for rec in
                 production_mason.filtered(lambda l: not l.absence and l.aac_sob_hour != 0)])
            active_production_point_s = sum(
                [rec.point_s for rec in
                 production_mason.filtered(lambda l: not l.absence and l.point_s != 0)])
            active_production_point_external = sum(
                [rec.point_external for rec in
                 production_mason.filtered(lambda l: not l.absence and l.point_external != 0)])
            active_production_layout_block = sum(
                [rec.layout_hour for rec in
                 production_mason.filtered(lambda l: not l.absence and l.layout_hour != 0)])
            active_production_mosaic = sum(
                [rec.mosaic for rec in
                 production_mason.filtered(lambda l: not l.absence and l.mosaic != 0)])

            absense_days = len(production_mason.filtered(lambda l: l.absence == '2'))
            pay.absense_days =  absense_days 
            pay.wall_tiles = active_production_wall_tiles
            pay.parquet_tiles = active_production_parquet_tiles
            pay.floor_tiles = active_production_floor_tiles
            pay.skirting = active_production_skirting
            pay.layout_tiles = active_production_layout_tiles
            pay.threshold = active_production_threshold
            pay.point_hour = active_production_point_hour
            pay.external_plaster_hour = active_production_external_plaster_hour
            pay.internal_plaster_hour = active_production_internal_plaster_hour
            pay.internal_angles_hour = active_production_internal_angles_hour
            pay.external_angles_hour = active_production_external_angles_hour
            pay.hollow_hour = active_production_hollow_hour
            pay.aac_sob_hour = active_production_aac_sob_hour
            pay.point_s = active_production_point_s
            pay.point_external = active_production_point_external
            pay.layout_block = active_production_layout_block
            pay.mosaic = active_production_mosaic
            
            pay.two_day_ded_mason = two_day_ded_mason * absense_days

    def _compute_count_work_in_holiday(self):
        count_work_in_holiday = 0
        for rec in self:
            data = rec.get_leave_interval(rec.date_from, rec.date_to, rec.employee_id)
            count_work_in_holiday = rec.get_number_day(data['calender']) + 1
            rec.count_work_in_holiday = count_work_in_holiday if len(data['leave']) == 0 and len(data['calender']) !=0 else 0

    def get_number_day(self, data):
        number = 0
        for i in data:
            number += (i.date_to - i.date_from).days
        return number

    def get_leave_interval(self, date_from, date_to, employee_ids):
        # Validated hr.leave create a resource.calendar.leaves
        calendar_leaves = self.env['resource.calendar.leaves'].search([
            '|', ('company_id', 'in', employee_ids.mapped('company_id').ids),
            ('company_id', '=', False),
            '|', ('resource_id', 'in', employee_ids.mapped('resource_id').ids),
            ('resource_id', '=', False),
            ('date_from', '<=', date_to),
            ('date_to', '>=', date_from),
        ], order='date_from')

        leaves = defaultdict(list)
        list_a = []
        list_b = []
        for leave in calendar_leaves:
            # for employee in employee_ids:
            if (not leave.company_id or leave.company_id == employee_ids.company_id) and \
                    (not leave.resource_id or leave.resource_id == employee_ids.resource_id) and \
                    (not leave.calendar_id or leave.calendar_id == employee_ids.resource_calendar_id):
                leaves[employee_ids.id].append(leave)
                list_a.append(leave)

        # Get validated time off
        leaves_query = self.env['hr.leave'].search([
            ('employee_id', 'in', employee_ids.ids),
            ('state', 'in', ['validate']),
            ('date_from', '<=', date_to),
            ('date_to', '>=', date_from)
        ])
        for leave in leaves_query:
            leaves[leave.employee_id.id].append(leave)
            list_b.append(leave)

        return {'calender': list_a, 'leave': list_b}
    
    def action_payslip_paid(self):
        res = super(PayslipEdit, self).action_payslip_paid()

        for m in self.env['leave.settl'].sudo().search([('state','!=','paid')]):
            for j in m.non_payslip_ids.search([('id','in',[i.id for i in self])]):
                m.non_payslip_ids = [(3,j.id)]
        return res
        

    @api.onchange('employee_id')
    def onchange_code(self):
        if self.employee_id:
            self.job_code = self.env['job.codes'].sudo().search([('employee_id', '=', self.employee_id.id)]).id

    @api.onchange('job_code')
    def onchange_employee(self):
        if self.job_code:
            self.employee_id = self.env['job.codes'].sudo().search([('id', '=', self.job_code.id)]).employee_id.id

    @api.depends('employee_id')
    def _compute_sal_adv(self):
        for payslip in self:
            sal = self.env['installment.line'].sudo().search(
                [('employee_id', '=', payslip.employee_id.id), ('date', '>=', payslip.date_from),
                 ('date', '<=', payslip.date_to), ('paid', '=', False), ('amount', '!=', 0)])
            sall = 0
            have_sal_adv = False
            sal_adv_id = sal.ids
            if sal:
                have_sal_adv = True
                for s in sal:
                    sall += s.amount

            payslip.sal_adv = sall
            payslip.have_sal_adv = have_sal_adv
            payslip.sal_adv_id = sal_adv_id

    @api.depends('employee_id')
    def _compute_helper_hour(self):
        for payslip in self:
            active_production_helper_hour = 0.0
            active_production_rush_coat = 0.0
            production_mason = payslip.env['production.line'].sudo().search([
                ('employee_id', "=", payslip.employee_id.id),
                ('start_date', '>=', payslip.date_from),
                ('start_date', '<=', payslip.date_to),
                
            ]).filtered(lambda l: l.start_date.weekday() != 6 and not l.leave)
            active_production_helper_hour = sum(
                [rec.hours for rec in production_mason.filtered(lambda l: not l.absence and l.hours != 0)])
            active_production_rush_coat = sum(
                [rec.rush_coat for rec in production_mason.filtered(lambda l: not l.absence and l.rush_coat != 0)])

            payslip.helper_hour = active_production_helper_hour
            payslip.rush_coat = active_production_rush_coat

    @api.depends('employee_id')
    def _compute_non_absent_hour(self):
        has_emp_absence = 0
        non_absence_bonus = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.non_absence_bonus')) or 100

        for payslip in self:
            has_emp_absence += len([i for i in self.env['production.line'].sudo().search(
                [('employee_id', '=', payslip.employee_id.id), ('start_date', '>=', payslip.date_from),
                 ('start_date', '<=', payslip.date_to), ('absence', 'in', ['1', '2'])]).filtered(
                lambda l: l.leave == '' and l.start_date.weekday() != 6)])
            hour = 0
            _logger.info(f'sadasdads{has_emp_absence}')
            if has_emp_absence > 0:
                hour += 0
            else:
                count = self.env['hr.leave'].sudo().search(
                    [('employee_ids', 'in', [i.id for i in payslip.employee_id]), ('state', '=', 'validate')]).filtered(
                    lambda l: (l.request_date_from >= payslip.date_from and l.request_date_to <= payslip.date_to) or
                              (
                                      l.date_from.date() <= payslip.date_from and l.date_to.date() >= payslip.date_from and l.date_to.date().month == payslip.date_to.month) or (
                                      l.date_from.date() >= payslip.date_from and l.date_to.date() >= payslip.date_to and l.date_from.date().month == payslip.date_from.month)
                )
                if not count:
                    missing_days = self.get_missing_days_of_week(payslip.employee_id.resource_calendar_id.id)
                    without_days = get_days_without_sundays(payslip.date_from, payslip.date_to, missing_days)

                    if len([i for i in  self.env['production.line'].sudo().search(
                            [('employee_id', '=', payslip.employee_id.id), ('start_date', '>=', payslip.date_from),
                             ('start_date', '<=', payslip.date_to),
                             ('absence', 'not in', ['1', '2'])]).filtered(lambda l: l.start_date.weekday() != 6 and not l.leave)]) == len(without_days):

                        if self.env['resource.calendar.leaves'].search_count([
                            '|', ('company_id', 'in', payslip.employee_id.mapped('company_id').ids),
                            ('company_id', '=', False),
                            ('resource_id', '=', False),
                            ('date_from', '>=', payslip.date_from),
                            ('date_to', '<=', payslip.date_to),
                        ]) >= 0:
                            hour += non_absence_bonus

            payslip.non_absent_hour = hour

    @api.depends('employee_id')
    def _compute_operator_absent_hour(self):
        least1 = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.least1')) or 90
        least2 = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.least2')) or 75
        least3 = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.least3')) or 50
        operator_bonus = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.operator_bonus')) or 150
        receive_some = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.receive_some')) or 100
        receive_less = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.receive_less')) or 7
        for payslip in self:
            hour = 0
            # operator_employee = self.env['production.line'].sudo().search(
            #     [('employee_id', '=', payslip.employee_id.id), ('leave', '=', ''), ('absence', 'not in', ['1', '2']),
            #      ('start_date', '>=', payslip.date_from),
            #      ('start_date', '<=', payslip.date_to)]).filtered(lambda l: l.start_date.weekday() != 6).employee_id
            all_days_operator = len([i for i in self.env['production.line'].sudo().search(
                [('employee_id.job_id', '=', self.env.ref('hr_edit.operation').id),
                 ('employee_id', '=', payslip.employee_id.id),('absence', 'not in', ['1', '2']),
                 ('start_date', '>=', payslip.date_from),
                 ('start_date', '<=', payslip.date_to)]).filtered(lambda l:l.leave == '' and l.start_date.weekday() != 6)])

            missing_days = self.get_missing_days_of_week(payslip.employee_id.resource_calendar_id.id)
            without_days = get_days_without_sundays(payslip.date_from, payslip.date_to, missing_days)
            pubic_holiday = self.env['resource.calendar.leaves'].search_count([
                '|', ('company_id', 'in', payslip.employee_id.mapped('company_id').ids),
                ('company_id', '=', False),
                ('resource_id', '=', False),
                ('date_from', '>=', payslip.date_from),
                ('date_to', '<=', payslip.date_to),
            ])
            _logger.info(f'sdasdasdd{all_days_operator,(len(without_days) + pubic_holiday)}')
            if all_days_operator / (len(without_days) + pubic_holiday) >= least1 / 100:
                hour += operator_bonus
            elif all_days_operator / (len(without_days) + pubic_holiday) >= least2 / 100:
                hour += receive_some
            elif all_days_operator / (len(without_days) + pubic_holiday) >= least3 / 100:
                hour += receive_less
            payslip.operator_absent_hour = hour

    @api.depends('employee_id')
    def _compute_count_unpaid(self):
        for payslip in self:
            leaves_in_no = 0
            unpaid = self.env['hr.leave'].sudo().search_count(
                [('holiday_status_id', '=', self.env.ref('hr_holidays.holiday_status_unpaid').id),
                 ('employee_ids', 'in', [i.id for i in payslip.employee_id]), ('state', '=', 'validate'),
                 ('request_date_from', '>=', payslip.date_from),
                 ('request_date_to', '<=', payslip.date_to)])
            unpaida = self.env['hr.leave'].sudo().search(
                [('holiday_status_id', '=', self.env.ref('hr_holidays.holiday_status_unpaid').id),
                 ('employee_ids', 'in', [i.id for i in payslip.employee_id]), ('state', '=', 'validate'), ])
            for lev in unpaida:
                # and lev.date_to.date() <= payslip.date_to
                if lev.date_from.date() >= payslip.date_from and lev.date_to.date() >= payslip.date_to and lev.date_from.date().month == payslip.date_from.month:
                    leaves_in_no += len(get_all_days_in_range(lev.date_from.date(), payslip.date_to))
                elif lev.date_from.date() <= payslip.date_from and lev.date_to.date() >= payslip.date_from and lev.date_to.date().month == payslip.date_to.month:
                    leaves_in_no += len(get_all_days_in_range(payslip.date_from, lev.date_to.date()))

            count_unpaid = leaves_in_no
            if unpaid > 0:
                count_unpaid = unpaid + leaves_in_no
            payslip.count_unpaid = count_unpaid

    @api.depends('employee_id')
    def _compute_absent_amount(self):
        absent_amount = 0
        for payslip in self:
            days = get_days(payslip.date_to)
            absent_amount = days
        payslip.absent_amount = absent_amount

    @api.depends('employee_id')
    def _compute_emirates_ded(self):
        for payslip in self:
            if payslip.employee_id.country_id.id == self.env.ref('base.ae').id:
                payslip.emirates_ded = True
            else:
                payslip.emirates_ded = False

    @api.depends('employee_id')
    def _compute_equip_ded(self):
        for payslip in self:
            assets = self.env['maintenance.equipment'].sudo().search_count(
                [('employee_id', '=', payslip.employee_id.id),
                 ('dismissed_date', '=', False),
                 ('category_id', '=', self.env.ref('hr_edit.maintenance_equipment_category_3').id),
                 ])
            if assets > 0:
                payslip.equip_ded = True
            else:
                payslip.equip_ded = False

    def action_payslip_done(self):
        call = self._action_effect_salary_advance()
        call_2 = self._action_effect_hold()
        if call:
            if call['error']:
                raise ValidationError(call['msg'])
        if call_2:
            if call_2['error']:
                raise ValidationError(call_2['msg'])
        
        return super(PayslipEdit, self).action_payslip_done()

    def _action_effect_hold(self):
        if self.hold_amount_add !=0 and self.last_hold and self.paid_hold and self.last_hold <= self.hold_amount_add:
            self.line_ids.filtered(lambda l: l.code in ['HOLDB']).total = self.last_hold
            self.line_ids.filtered(lambda l: l.code in ['NET']).total = self.line_ids.filtered(
                    lambda l: l.code in ['NET']).total - self.last_hold
            self._action_effect_leave()
            return {'error': False}
        elif self.hold_amount_add == 0 and self.paid_hold:
            return {'msg': _('Please Check Hold Amount'), 'error': True}
        elif self.hold_amount_add == self.last_hold and not self.paid_hold:
            self._action_effect_leave()
            return {'error': False}
        elif self.hold_amount_add == 0 and  not self.paid_hold:
            
            return {'error': False}

        else:
            return {'msg': _('Please Check Hold Amount'), 'error': True}

    

    
    def _action_effect_leave(self):
        for rec in self.env['hr.leave'].sudo().search([('id', 'in', self.time_off_id)]):
            if rec.payslip_state == 'blocked':
                rec.payslip_state = 'normal'
            elif rec.payslip_state == 'normal' and rec.hold == self.last_hold:
                rec.payslip_state = 'done' 
                for j in self.env['leave.settl'].sudo().search([('leave_id','=',rec.id)]):
                    j.hold = 0
                    j.leave_id = 0              
            elif rec.payslip_state == 'normal' and rec.hold != self.last_hold:
                rec.payslip_state = 'normal'
                rec.hold = rec.hold - self.last_hold
            else:
                rec.payslip_state = 'done'
    
    def _action_effect_salary_advance(self):
        for rec in self.line_ids.filtered(lambda l: l.code in ['salm', 'sal', 'salh']):
            if not rec.delay and not rec.paid and not rec.exempt and rec.amount > 0:
                return {'msg': _('Must be choose for salary advance'), 'error': True}
         
            for sal in self.env['installment.line'].sudo().search([('id', 'in', self.sal_adv_id)]):
                sal.paid = rec.paid
                if rec.exempt:
                    sal.company_exempt()
                if rec.delay:
                    sal.delay_condition = rec.delay
                    sal.delay_period = rec.delay_period
                    sal.action_compute_installment()
            if rec.delay or rec.exempt:
                rec.quantity = 0
                # self.line_ids.filtered(lambda l: l.code in ['TH', 'TM', 'NetStaff']).amount = self.line_ids.filtered(
                #     lambda l: l.code in ['TH', 'TM', 'NetStaff']).amount - rec.amount
                self.line_ids.filtered(lambda l: l.code in ['NET']).amount = self.line_ids.filtered(
                    lambda l: l.code in ['NET']).amount - rec.amount
                # self.line_ids.filtered(lambda l: l.code in ['TH', 'TM', 'NetStaff']).total = self.line_ids.filtered(
                #     lambda l: l.code in ['TH', 'TM', 'NetStaff']).total - rec.amount
              
            return {'error': False}

    def calc_report_data(self):
        for rec in self:
            records = []
            last_month_day = calendar.monthrange(rec.date_from.year, rec.date_from.month)[1]
            sunday = get_sundays(rec.date_from.year, rec.date_from.month)
            holiday = self.get_holiday_day(rec.date_from, rec.date_to)
            for i in range(1, last_month_day + 1):
                record = self.env['production.line'].sudo().search([('start_date', '>=', rec.date_from),
                                                                    ('start_date', '<=', rec.date_to),
                                                                    ('employee_id', '=', rec.employee_id.id)]).filtered(
                    lambda l: l.start_date.day == i)

                records.append({
                    'i': i,
                    'rec': record,
                    'sunday': True if i in sunday else False,
                    'holiday': True if i in holiday else False,
                })
        return records

    def print_payslip_report_helper(self):
        return self.env.ref('hr_edit.report_helper_payslip_pdf').report_action(self)

    def print_payslip_report_mason(self):
        return self.env.ref('hr_edit.report_mason_payslip_pdf').report_action(self)
    def print_payslip_report_xlsx(self):
        return self.env.ref('hr_edit.payslip_report_xls').report_action(self)

    def get_holiday_day(self, date_from, date_to):
        public_holiday = self.env['resource.calendar.leaves'].search([
            '|', ('company_id', 'in', self.employee_id.mapped('company_id').ids),
            ('company_id', '=', False),
            ('resource_id', '=', False),
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to),
        ], order='date_from')

        lis = [get_all_days_in_range(day.date_from, day.date_to) for day in public_holiday]
        return [item for sublist in lis for item in sublist]
