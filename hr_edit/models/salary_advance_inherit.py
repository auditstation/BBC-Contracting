# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AdvanceSalaryEdit(models.Model):
    _inherit = "salary.advance"

    first_name = fields.Char(related='employee_id.first_name')
    middle_name = fields.Char(related='employee_id.middle_name')
    last_name = fields.Char(related='employee_id.last_name')
    designation = fields.Many2one(related='employee_id.job_id')
    reporting_to = fields.Many2one(related='employee_id.parent_id', string='Reporting to')
    joining_date = fields.Date(related='employee_id.joining_date_first')
    employee_signature = fields.Binary()
    account_signature = fields.Binary()
    manager_signature = fields.Binary()
    manual_approve = fields.Boolean(default=True)
    delay_condition = fields.Boolean(string='Delay First Payment',
                                     help="Indicate whether the first payment should be delayed using a check "
                                          "box and specify  recovery start date")
    duration = fields.Integer(string="Number of Installments", default=1,
                              tracking=True)
    presumed_payment_date = fields.Date(string="Presumed payment date", compute='_compute_presumed_payment_date',
                                        store=True, tracking=True)

    attachment_ids = fields.Many2many(comodel_name='ir.attachment')
    type = fields.Selection([('loan', 'Loan'),
                             ('adv', 'Advance'),
                             ('fine', 'Fines'),
                             ('assets', 'Other Assets')],
                            default='adv')
    reason_selection = fields.Selection([
        ('gen', 'General Salary Advance'),
        ('loan', 'Loan'),
        ('ticket', 'Ticket'),
        ('medical', 'Medical'),
        ('fines', 'Fines'),
        ('other', 'Other'),
    ], default='gen')
    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'Submitted'),
                              ('in_progress', 'In Progress'),
                              ('under_recover', 'Under Recovery'),
                              ('approve', 'Approved'),
                              ('cancel', 'Cancelled'),
                              ('paid', 'Paid'),
                              ('reject', 'Rejected')], string='Status',
                             default='draft', track_visibility='onchange',
                             help='State of the salary advance.')
    installment_lines = fields.One2many('installment.line', 'advance_id',
                                        string="Installment Line",
                                        help="Details of installment lines "
                                             "associated with the loan.",
                                        index=True)
    total_amount = fields.Float(string="Total Amount", store=True,
                                readonly=True, compute='_compute_total_amount',
                                help="The total amount of the Advance")
    balance_amount = fields.Float(string="Balance Amount", store=True,
                                  compute='_compute_total_amount',
                                  help="""The remaining balance amount of the 
                                      Advance after deducting 
                                      the total paid amount.""")
    total_paid_amount = fields.Float(string="Total Paid Amount", store=True,
                                     compute='_compute_total_amount',
                                     help="The total amount that has been "
                                          "paid towards the Advance.")

    amount_total_words = fields.Char("Amount total in words", compute='_compute_amount_total_words')
    mol_num = fields.Char("mol", compute='_compute_mol_num')
    def _compute_mol_num(self):
        for record in self:
            if record.employee_id:
                doc= self.env['hr.employee.document'].sudo().search([('employee_ref_id', '=', record.employee_id.id),
                                                                ('document_type_id', '=',
                                                                 self.env.ref('oh_employee_documents_expiry.document_type_05').id)], order='id desc',
                                                               limit=1)
                record.mol_num = doc.name if len(doc)!=0 else ''
            else:
                record.mol_num =''

    def _compute_amount_total_words(self):
        for record in self:
            currency = record.currency_id or self.env.company.currency_id
            record.amount_total_words = currency.amount_to_text(record.advance)

    def approve_request_acc_dept(self):
        if not self.employee_id.address_id.id:
            raise UserError('Define home address for the employee. i.e address'
                            ' under private information of the employee.')
        if not self.employee_contract_id:
            raise UserError('Define a contract for the employee')
        salary_advance_search = self.search(
            [('employee_id', '=', self.employee_id.id), ('id', '!=', self.id),
             ('state', '=', 'approve')])
        current_month = datetime.strptime(str(self.date),
                                          '%Y-%m-%d').date().month
        # for each_advance in salary_advance_search:
        #     existing_month = datetime.strptime(str(each_advance.date),
        #                                        '%Y-%m-%d').date().month
            # if current_month == existing_month:
            #     raise UserError('Advance can be requested once in a month')

        if not self.advance:
            raise UserError('You must Enter the Salary Advance amount')
        # line_ids = []
        # debit_sum = 0.0
        # credit_sum = 0.0

        self.state = 'in_progress'
        return True

    @api.depends('employee_id', 'delay_condition', 'duration', 'date')
    def _compute_presumed_payment_date(self):
        for rec in self:
            day = rec.duration * 30
            date = rec.date + timedelta(days=day)
            if rec.delay_condition:
                date = date + relativedelta(months=+1)
            rec.presumed_payment_date = date

    def compute_installment(self, advance_id=False, number_installment=1):
        for advance in self:
            last_month_day = calendar.monthrange(advance.date.year, advance.date.month)[1]
            end_of_month = advance.date + relativedelta(day=int(last_month_day))
            advance.installment_lines.unlink()
            date_start = datetime.strptime(str(end_of_month), '%Y-%m-%d')
            amount = advance.advance / number_installment
            for i in range(1, number_installment + 1):

                self.env['installment.line'].sudo().create({
                    'date': end_of_month,
                    'amount': amount,
                    'employee_id': advance.employee_id.id,
                    'advance_id': advance_id})
                date_start = date_start + relativedelta(months=1)
                last_month_day = calendar.monthrange(date_start.year, date_start.month)[1]
                end_of_month = date_start + relativedelta(day=int(last_month_day))

             
            advance._compute_total_amount()

    @api.onchange('duration')
    def _change_duration(self):
        if self.duration and self.state == 'under_recover':
            duration = self.duration if self._origin.duration != 0 else 1
            new_duration = self.duration
            self.compute_installment(number_installment=duration, advance_id=self._origin.id)
            self.duration = new_duration

    @api.onchange('attachment_ids', 'employee_signature')
    def _change_state(self):
        for rec in self:
            if not rec.manual_approve:
                if rec.attachment_ids or rec.employee_signature:
                    rec.state = 'in_progress'

    def action_submit_to_manager(self):
        """Method of a button. Changing the state of the salary advance."""
        self.state = 'submit'
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            note=_('%(employee)s request salary advance at %(date)s.',
                   employee=self.employee_id.name,
                   date=self.date),
            user_id=self.reporting_to.user_id.id)

    def action_compute_installment(self):
        """This automatically create the installment the employee need to pay to
            company based on payment start date and the no of installments.
            """
        self.compute_installment(number_installment=self.duration, advance_id=self.id)
        self.state = 'under_recover'

        return True

    def action_recompute_installment(self):
        """This automatically create the installment the employee need to pay to
            company based on payment start date and the no of installments.
            """
        lines_paid = self.installment_lines.filtered(lambda l: l.paid == True)
        total_paid = sum(adv.amount for adv in lines_paid)
        duration = len(self.installment_lines - lines_paid)
        for rec in self.installment_lines - lines_paid:
            date = rec.date
            amount = (self.advance - total_paid) / duration
            if amount > 0:
                self.env['installment.line'].sudo().create({
                    'date': date,
                    'amount': amount,
                    'employee_id': self.employee_id.id,
                    'advance_id': self.id})

            rec.unlink()
            self._compute_total_amount()
        return True
    @api.depends('installment_lines.paid')
    def _compute_total_amount(self):
        """ Compute total advance amount,balance amount and total paid amount"""
        total_paid = 0.0
        for adv in self:
            for line in adv.installment_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = adv.advance - total_paid
            adv.total_amount = adv.advance
            adv.balance_amount = balance_amount
            adv.total_paid_amount = total_paid
            if adv.total_paid_amount == adv.total_amount and adv.total_paid_amount !=0:
                adv.state = 'paid'

    def write(self, vals):
        res = super(AdvanceSalaryEdit, self).write(vals)
        if 'installment_lines' in vals:
            total = 0.0
            for line in self.installment_lines:
                total += line.amount
            if total != self.advance:
                raise UserError(
                    _('Please Check you Payment split. advance is:%s, and total payment in installment is:%s') % (
                        self.advance, total))

        return res
