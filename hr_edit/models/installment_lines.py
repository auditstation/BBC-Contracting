# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import relativedelta
import calendar

_logger = logging.getLogger(__name__)


class InstallmentLine(models.Model):
    _name = "installment.line"

    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True,
                       help="Date of the payment")
    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  help="Employee")
    amount = fields.Float(string="Amount", required=True, help="Amount")
    paid = fields.Boolean(string="Paid", help="Indicates whether the "
                                              "installment has been paid.")
    advance_id = fields.Many2one('salary.advance', string="Advance Ref.",
                                 help="Reference to the associated loan.")
    delay_condition = fields.Boolean(string='Delay Payment', default=False)
    desc = fields.Char()
    delay_period = fields.Selection([('0', 'no delay'),
                                     ('1', '1-month delay'),
                                     ('2', '2-month delay'),
                                     ('3', '3-month delay'),
                                     ('4', '4-month delay'),
                                     ('5', '5-month delay'),
                                     ],
                                    default='0')

    @api.onchange('delay_period')
    def onchange_delay_period(self):
        _logger.info("......................22.........................{}///".format(self))
        self.action_compute_installment()

    def action_compute_installment(self):
        date_start = self.date + relativedelta(months=int(self.delay_period))
        last_month_day = calendar.monthrange(date_start.year, date_start.month)[1]
        end_of_month = date_start + relativedelta(day=int(last_month_day))



        lines_paid = self._origin.advance_id.installment_lines.filtered(
            lambda l: l.paid == True or l.delay_period != '0')

        for rec in self._origin.advance_id.installment_lines - self._origin - lines_paid:
            _logger.info(".....................adad.................{}///{}".format(rec, date_start))
            rec.sudo().write({
                'date': end_of_month,

            })
            date_start = date_start + relativedelta(months=1)
            last_month_day = calendar.monthrange(date_start.year, date_start.month)[1]
            end_of_month = date_start + relativedelta(day=int(last_month_day))

        date_start1 = self._origin.advance_id.installment_lines[-1].date + relativedelta(months=int(self.delay_period)) if self._origin.advance_id.installment_lines[-1] == self._origin else self._origin.advance_id.installment_lines[-1].date + relativedelta(months=1)
        last_month_day = calendar.monthrange(date_start1.year, date_start1.month)[1]
        end_of_month = date_start1 + relativedelta(day=int(last_month_day))

        if int(self.delay_period) != 0:
            self.env['installment.line'].sudo().create({
                'date': end_of_month,
                'amount': self._origin.amount,
                'employee_id': self._origin.advance_id.employee_id.id,
                'advance_id': self._origin.advance_id.id})
            self._origin.amount = 0

    @api.onchange('paid')
    def change_deduction(self):
        for rec in self:
            self.env['deduction.line'].sudo().search([('rec_id','=',rec.id)]).paid = 'paid'
            self.env['deduction.line'].sudo().search([('rec_id','=',rec.id)]).unlink()

    @api.onchange('amount')
    def onchange_amount(self):
        self.action_compute_installment_after_change_amount()

    def action_compute_installment_after_change_amount(self):
        lines_paid = self._origin.advance_id.installment_lines.filtered(
            lambda l: l.paid == True or l.delay_condition == True)
        new_amount = (self._origin.advance_id.advance - (
                sum([line.amount for line in lines_paid]) + (self.amount))) / len(
            self._origin.advance_id.installment_lines - self._origin - lines_paid)
       
        for rec in self._origin.advance_id.installment_lines - self._origin - lines_paid:          
            rec._origin.amount = new_amount
            rec.sudo().write({
                'amount': new_amount,
            })


    # def action_compute_installment(self):
    #     date_start = self._origin.date + relativedelta(months=int(self.delay_period))
    #     _logger.info("..................`22222`.................{}///".format(date_start))
    #
    #     # amount = advance.advance / advance.duration
    #     lines_paid = self._origin.advance_id.installment_lines.filtered(lambda l: l.paid == True)
    #     for rec in self._origin.advance_id.installment_lines - self._origin - lines_paid:
    #         _logger.info(".....................adad.................{}///{}".format(rec, date_start))
    #         rec.sudo().write({
    #             'date': date_start,
    #
    #         })
    #         date_start = date_start + relativedelta(months=1)
    #     # advance._compute_total_amount()
    #     _logger.info("......................22.........................{}///".format(self))
    #     return True

    # payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.",
    #                              help="Reference to the associated "
    #                                   "payslip, if any.")
    def company_exempt(self):
        self.paid = True
        self.desc = 'waved/removed by the company'
