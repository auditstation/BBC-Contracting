# -*- coding: utf-8 -*-
from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)
class LeaveSett(models.Model):
    _name = 'leave.settl'
    employee_id = fields.Many2one('hr.employee', string='Employee')
    job_code = fields.Many2one('job.codes')
    visa = fields.Char()
    mol_no = fields.Char()
    salary = fields.Float()
    nationality = fields.Char(related="employee_id.country_id.name")
    job_id = fields.Char(related="employee_id.job_id.name")
    non_payslip_ids = fields.Many2many('hr.payslip')
    deduction_ids = fields.Many2many('deduction.line')
    state = fields.Selection([('paid', 'Paid'), ('unpaid', 'Unpaid')],default="unpaid")
    group_payslip = fields.Binary(compute='_compute_group_payslip')
    group_detuction = fields.Binary(compute='_compute_group_detuction')
    check = fields.Boolean()

    

    # def compute_check(self):
    #     for rec in self:
    #         rec.change_code()
    #         rec.check = True
    
    @api.depends('employee_id')
    def _compute_group_payslip(self):
        
        for record in self:
            if record.sudo().employee_id:
                cus = [i.id for i in record.employee_id.slip_ids.filtered(lambda x: x.state in['verify','done'])]
                record.group_payslip = cus
            else:
                record.group_payslip = []

    @api.depends('employee_id')
    def _compute_group_detuction(self):
        
        for record in self:
            if record.sudo().employee_id:
                cus = [i.id for i in self.env['deduction.line'].sudo().search([('employee_id','=',record.employee_id.id),('paid','!=','paid')])]
                record.group_detuction = cus
            else:
                record.group_detuction = []


    last_wage = fields.Char(compute="_compute_wage")
    last_date = fields.Char(compute="_compute_wage")
    hold = fields.Float('Amount On Hold')
    cash = fields.Float('cash',readonly=False,compute='_compute_cash',store=True)
    wps = fields.Float('wps',readonly=False,compute='_compute_cash',store=True)
    all_amount = fields.Float('Total before hold',compute='_compute_cash_amount')
    leave_id = fields.Integer('leave id')

    def paid(self):
        for i in self:
            if i.all_amount != i.cash+i.wps+i.hold:
                raise ValidationError('You should balance your amount')
            i.state = 'paid'
            for rec in i.deduction_ids:
                
                if 'Installment' in rec.name:
                    self.env['installment.line'].sudo().browse(rec.rec_id).paid=True
                if 'ticket' in rec.name:
                    self.env['hr.leave'].sudo().browse(rec.rec_id).paid=True

                rec.paid='paid'
    
            for rec in i.non_payslip_ids:
                if rec.state =='verify':
                    rec.action_payslip_done()
              
                rec.action_payslip_paid()
           
    @api.onchange('employee_id')
    def change_code(self):
        for rec in self:
            
            if rec.employee_id:
               
                rec.job_code = rec.env['job.codes'].sudo().search([('employee_id', '=', rec.employee_id.id)]).id
                rec.visa = rec.employee_id.branch
                rec.mol_no = rec.employee_id.mol_no
                rec.non_payslip_ids = [(6,0,[i.id for i in rec.employee_id.slip_ids.filtered(lambda x: x.state in['verify','done'])])]
                rec.salary = rec.employee_id.contract_ids[-1].contract_salary if len(rec.employee_id.contract_ids) > 0 else 0
                
                rec.create_deduction(rec.employee_id)
                all_leave = self.env['hr.leave'].sudo().search(
                    [('employee_ids', 'in', [i.id for i in rec.employee_id]), ('state', '=', 'validate')],order='request_date_to desc')
                
                all_leave_hold = all_leave[0].filtered(lambda
                                                        l: l.hold != 0 and l.payslip_state == 'blocked' ) if len(all_leave) > 0 else []
                
                rec.leave_id = all_leave_hold.id if len(all_leave) > 0 else 0                                      
                rec.hold=sum([rec.hold for rec in all_leave_hold]) or 0
               
    @api.depends('non_payslip_ids','deduction_ids')        
    def _compute_cash_amount(self):
        for rec in self:
            if rec.non_payslip_ids or rec.deduction_ids:
                amount = sum([i.amount for i in self.non_payslip_ids]) - sum([j.amount for j in self.deduction_ids])
                rec.all_amount = amount
               
            else:
                rec.all_amount = 0

    @api.depends('non_payslip_ids','deduction_ids')   
    def _compute_cash(self):
        for rec in self:
            if rec.non_payslip_ids or rec.deduction_ids:
               
                amount = sum([i.amount for i in self.non_payslip_ids]) - sum([j.amount for j in self.deduction_ids])
                # rec.all_amount = amount
                if amount - rec.hold <= 500:
                    rec.cash =  amount - rec.hold
                    rec.wps = 0
                if amount - rec.hold >= 500:
                    rec.cash = 0
                    rec.wps = amount - rec.hold

            else:
                # rec.all_amount=0
                rec.cash = 0
                rec.wps = 0

    # @api.onchange('cash')
    # def change_amount_cash(self):
    #     if self.cash and self.cash != self._origin.all_amount and self._origin.wps!=0:
    #         self.wps=self._origin.cash - self.cash

    @api.onchange('hold','wps','cash','deduction_ids')
    def change_amount_hold(self):
        if self._origin.deduction_ids.ids:
            if len(self.deduction_ids.ids)!= len(self._origin.deduction_ids.ids):
            
            
                if self.env['hr.leave'].sudo().search(
                            [('employee_ids', 'in', [i.id for i in self._origin.employee_id]), ('state', '=', 'validate'),('id','in',[i.rec_id for i in self.env['deduction.line'].sudo().search([('id','in',self.deduction_ids.ids)])])],order='request_date_to desc'):
                        all_leave = self.env['hr.leave'].sudo().search(
                            [('employee_ids', 'in', [i.id for i in self.employee_id]), ('id','in',[i.rec_id for i in self.env['deduction.line'].sudo().search([('id','in',self.deduction_ids.ids)])]),('state', '=', 'validate')],order='request_date_to desc')
                        all_leave_hold = all_leave[0].filtered(lambda
                                                                l: l.hold != 0 and l.payslip_state == 'blocked' ) if len(all_leave) > 0 else []
                        self.leave_id = all_leave_hold.id if len(all_leave) > 0 else 0                                      
                        self.hold=sum([rec.hold for rec in all_leave_hold]) or 0
                
                elif self._origin.leave_id not in [i.rec_id for i in self.env['deduction.line'].sudo().search([('id','in',[i.rec_id for i in self.env['deduction.line'].sudo().search([('id','in',self.deduction_ids.ids)])])])]:
                    self.leave_id = 0
                    self.hold = 0
                    amounts= self.all_amount
                    if amounts >= 500:
                        self.wps = amounts
                        self.cash = 0
                    elif amounts <= 500 :
                        self.cash = amounts 
                        self.wps = 0 
           
        if self.hold and self.hold!=self._origin.hold and self._origin.leave_id!=0:
            
            amounts= self.all_amount - self.hold
            
            if amounts >= 500:
               
                self.wps = (self._origin.wps+ self._origin.hold) - self.hold
               
            elif amounts <= 500:
                if self.hold < (self._origin.cash+ self._origin.hold):
                    self.cash = (self._origin.cash+ self._origin.hold) -self.hold
                else:
                    self.cash = amounts
                    self.wps = 0
               
            self.env['hr.leave'].sudo().browse(self._origin.leave_id).hold = self.hold
        if self.wps and self.wps!= self._origin.wps:
            
            self.cash=(self.all_amount-self.hold) - self.wps if ((self.all_amount-self.hold) - self.wps) > 0 else 0
        if self.cash and self.cash!= self._origin.cash :
            
            
            self.wps=(self.all_amount-self.hold) - self.cash
    
    # @api.onchange('wps')
    # def change_amount_wps(self):
    #     if self.wps and self.wps != self._origin.all_amount  and self._origin.cash!=0:
            
    #         self.cash=(self._origin.all_amount-self._origin.hold) - self.wps


    def create_deduction(self,employee_id):
        self.deduction_ids.unlink()
        for rec in self:
            for i in self.env['installment.line'].sudo().search([('employee_id','in',[i.id for i in employee_id]),('paid','=',False),('amount','>',0)]).filtered(lambda x: x.date > fields.Date.today() and x.date.month != fields.Date.today().month and x.date.year != fields.Date.today().year):
               
                if self.env['deduction.line'].sudo().search_count([('employee_id','in',[i.id for i in employee_id]),('rec_id','=',i.id),('paid','=','unpaid')]) > 0:
                    for j in self.env['deduction.line'].sudo().search([('employee_id','in',[i.id for i in employee_id]),('rec_id','=',i.id),('paid','=','unpaid')]):
                        rec.deduction_ids = [(4, j.id)]
                else:
                    ins=self.env['deduction.line'].sudo().create({
                        'name':'Installment in %s' %i.date.strftime("%Y/%m/%d"),
                        'amount': i.amount,
                        'employee_id':employee_id.id,
                        'rec_id':i.id,
                    })
                    rec.deduction_ids=[(4,ins.id)]
            for i in self.env['hr.leave'].sudo().search([('employee_ids','in',[i.id for i in employee_id]),('state', '=', 'validate'),('paid','=',False),('ticket_price','>',0)]):
                if self.env['deduction.line'].sudo().search_count([('employee_id','in',[i.id for i in employee_id]),('rec_id', '=', i.id), ('paid', '=', 'unpaid')]) > 0:
                    for j in self.env['deduction.line'].sudo().search([('employee_id','in',[i.id for i in employee_id]),('rec_id', '=', i.id), ('paid', '=', 'unpaid')]):
                        rec.deduction_ids = [(4, j.id)]
                else:
                    ticket=self.env['deduction.line'].sudo().create({
                        'name': 'ticket for leave from %s to %s' %(i.request_date_from.strftime("%Y/%m/%d"),i.request_date_to.strftime("%Y/%m/%d")),
                        'amount': i.ticket_price,
                        'employee_id': employee_id.id,
                        'rec_id': i.id,
                    })
                    rec.deduction_ids = [(4, ticket.id)]

    @api.onchange('job_code')
    def onchange_employee(self):
        if self.job_code:
            self.employee_id = self.env['job.codes'].sudo().search([('id', '=', self.job_code.id)]).employee_id.id


    def _compute_wage(self):
        for rec in self:
            last_wage = self.env['hr.payslip'].sudo().search([('employee_id','=',rec.employee_id.id),('state','=','paid')])
            if last_wage:
                rec.last_wage = last_wage[-1].paid_date.strftime("%B") + '-' +str(last_wage[-1].paid_date.year)
            else:
                rec.last_wage =''
            last_date =self.env['hr.leave'].sudo().search(
                        [('employee_ids', 'in', [i.id for i in rec.employee_id]),
                         ('state', '=', 'validate'),('holiday_status_id','=',self.env.ref('hr_edit.annual_leave').id)]).filtered(
                    lambda x: x.request_date_from <= fields.Date.today())

            if last_date:
                rec.last_date = last_date.sort()[0].request_date_from +relativedelta(days=-1) if len(last_date) > 1 else last_date.request_date_from +relativedelta(days=-1)
            else:
                rec.last_date = ''


class Deduction(models.Model):
    _name="deduction.line"
    name=fields.Char('Name')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    amount = fields.Float('amount')
    rec_id = fields.Integer('rec')
    paid = fields.Selection([('paid', 'Paid'), ('unpaid', 'Unpaid')],default="unpaid")
    
    


