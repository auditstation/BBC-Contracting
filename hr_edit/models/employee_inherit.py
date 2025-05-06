# -*- coding: utf-8 -*-
from odoo import api, _, fields, models, tools
from datetime import datetime, timedelta, date
import logging
import calendar
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for i in res:
            if i.partner_id and self.env.context.get('import_file') and i.partner_id.employee_ids:
                i.partner_id.employee_ids[0].bank_account_id = i.id
        return res
class EmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    job_code = fields.Char(tracking=True)

    first_name = fields.Char(required=True)
    middle_name = fields.Char(required=False)
    last_name = fields.Char(required=True)
    relationship = fields.Char()
    joining_date_first = fields.Date(string='Joining Date')
    joining_contract = fields.Date(string='Contract Date', compute='_compute_joining_date_first')
    first_wage = fields.Float(string="First Wage", compute='_compute_joining_date_first')
    on_company_sponsorship = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no')
    branch = fields.Selection([('dubai', 'Dubai'), ('sharjah', 'Sharjah')])
    sponsor_name = fields.Char()
    nos_name = fields.Char('nos_name')
    has_nos = fields.Binary(string="NOC from sponsor")
    sponsor_trade_name = fields.Char('sponsor_name')
    has_sponsor = fields.Binary(string="Sponsor Trade License ")
    bank_name = fields.Char('Bank Name', compute="_compute_account")
    iban = fields.Char('IBAN', compute="_compute_account")
    routing_no = fields.Char('Routing No', compute="_compute_account")
    job_title_visa = fields.Char(string='Job Title as per visa', translate=True)
    adv_count = fields.Integer(
        string="Advance Count",
        help="Number of Advance associated with the employee",
        compute='_compute_adv_count')
    location_id = fields.Many2one('work.location', compute='_compute_location_id')
    type_work = fields.Selection([('staff', 'Staff'),
                                  ('staff_for', 'Staff-Foreman'),
                                  ('labor_a', 'Labor A'),
                                  ('labor_n', 'Labor N'),
                                  ], default='staff')
    
    # passport_id = fields.Char('Passport No', groups="hr.group_hr_user", tracking=True, compute="_compute_numberS",
    #                           readonly=True,store=True)
    visa_no = fields.Char('Visa No', groups="hr.group_hr_user", compute="_compute_number", compute_sudo=True,tracking=True, readonly=True)
    visa_expire = fields.Date('Visa Expiration Date', groups="hr.group_hr_user", compute="_compute_number", compute_sudo=True,
                              tracking=True, readonly=True)
    equipment_non_count = fields.Integer('Count', compute='_compute_equipment_non_count')
    passport_expire = fields.Date('Passport Expiration Date', groups="hr.group_hr_user",
                                  tracking=True, readonly=True)
    mol_no = fields.Char('MOL No', groups="hr.group_hr_user", compute_sudo=True, compute="_compute_number", tracking=True, readonly=True)
    mol_expire = fields.Date('MOL Expiration Date',  compute_sudo=True,groups="hr.group_hr_user", compute="_compute_number", tracking=True,
                             readonly=True)
    med_no = fields.Char('Medical Fitness  No',  compute_sudo=True,groups="hr.group_hr_user", compute="_compute_number", tracking=True,
                         readonly=True)
    med_expire = fields.Date('Medical Fitness Expiration Date',  compute_sudo=True,groups="hr.group_hr_user", compute="_compute_number",
                             tracking=True, readonly=True)
    eid_no = fields.Char('Emirates ID No',  compute_sudo=True,groups="hr.group_hr_user", compute="_compute_number", tracking=True,
                         readonly=True)
    eid_expire = fields.Date('Emirates ID Expiration Date', compute_sudo=True, groups="hr.group_hr_user", compute="_compute_number",
                             tracking=True, readonly=True)
    uid_no = fields.Char('UID No',  compute_sudo=True,groups="hr.group_hr_user", tracking=True, readonly=True)
    uid_expire = fields.Date('UID Expiration Date', groups="hr.group_hr_user", compute="_compute_number", tracking=True,
                             readonly=True)
    drive_no = fields.Char('Drive License  No',  compute_sudo=True,groups="hr.group_hr_user", compute="_compute_number", tracking=True,
                           readonly=True)
    drive_expire = fields.Date('Drive License Expiration Date',  compute_sudo=True,groups="hr.group_hr_user", compute="_compute_number",
                               tracking=True,
                               readonly=True)
    permit_no = fields.Char('Work Permit No', groups="hr.group_hr_user",  compute_sudo=True,compute="_compute_number", tracking=True)
    work_permit_expiration_date = fields.Date('Work Permit Expiration Date', groups="hr.group_hr_user",
                                              compute="_compute_number", compute_sudo=True, tracking=True,store=True,readonly=False)
    last_wage = fields.Char(compute="_compute_wage")
    last_date = fields.Char(compute="_compute_wage")
    arabic_name = fields.Char('Arabic Name')
    next_schedule_date = fields.Date()
    number_allocation = fields.Float()
    get_first = fields.Boolean()

    def create_launch_allocation(self,period,active,msg,get_first=False):
        if period != 0  and self.joining_date_first and self.type_work:
            self.get_first = get_first
            allocation = self.env['hr.leave.allocation'].sudo().create({
                        "name": self.name,
                        "date_from": date(date.today().year, date.today().month, 1),
                        "holiday_type": "employee",
                        "employee_id": self.id,
                        "number_of_days": float(period),
                        "holiday_status_id": self.env.ref("hr_edit.annual_leave").id,
                        "allocation_type": "regular",
                        "notes":msg,
                        "state": "confirm"
                    })
            if active:
                allocation.sudo().write({'state': 'validate'})
            if not active:
                allocation.sudo().write({'state': 'refuse'})
                allocation.sudo().write({'active': active})
                
    def start_up_data(self):
        for rec in self:
            allocation_period = {'staff': 7.5, 'staff_for': 45, 'labor_a': 45, 'labor_n': 60}.get(rec.type_work, 0)
            complete_period = {'staff':90,'staff_for': 540, 'labor_a': 540, 'labor_n': 720}.get(rec.type_work, 0)
            msg_leave = _('Allocation after %s period from last leave (%s)') % (
                        complete_period / 12 / 30, rec.next_schedule_date)
            msg_first = _('First Allocation after %s/year period from joining date(%s)') % (
                    complete_period / 12 / 30, rec.joining_date_first)
            msg_rem = _('Rem Allocation')
            if not rec.get_first:
                rec.create_launch_allocation(period=allocation_period + rec.number_allocation,active=True,msg=msg_first,get_first=True)
            else:
                rec.create_launch_allocation(period=allocation_period,active=False,msg=msg_first,get_first=True)
                rec.create_launch_allocation(period=rec.number_allocation,active=True,msg=msg_rem)
            if rec.next_schedule_date and rec.next_schedule_date <= date.today() and rec.type_work != 'staff':
                rec.create_launch_allocation(period=allocation_period,active=True,msg=msg_leave)
                   
    def _search_work_permit(self, operator, value):
        domain = [('work_permit_expiration_date', operator, value)]
        records = self.env['hr.employee'].sudo().search([domain]).filtered(
            lambda l: l.work_permit_expiration_date)
        return [('id', 'in', records.ids)]

    def toggle_active(self):
        
        if not self.active:
            
            self.env['job.codes'].sudo().search([('employee_id', '=', self.id),('active', '=', False)]).active=True
        return super().toggle_active()

    @api.onchange('on_company_sponsorship')
    def change_branch(self):
        for rec in self:
            if rec.on_company_sponsorship =='no':
                rec.branch = False

    def _compute_wage(self):
        for rec in self:
            last_wage = self.env['hr.payslip'].sudo().search([('employee_id','=',rec.id),('state','=','paid')])
            if last_wage:
                rec.last_wage = last_wage[-1].paid_date.strftime("%B") + '-' +str(last_wage[-1].paid_date.year)
            else:
                rec.last_wage =False if not rec.last_wage else rec.last_wage
            last_date =self.env['hr.leave'].sudo().search(
                        [('employee_ids', 'in', [i.id for i in rec]),
                         ('state', '=', 'validate')]).filtered(
                    lambda x: x.request_date_from.month == fields.Date.today().month and x.request_date_from.year == fields.Date.today().year)

            if last_date:
                rec.last_date = last_date.sort()[0].request_date_from +relativedelta(days=-1) if len(last_date) > 1 else last_date.request_date_from +relativedelta(days=-1)
            else:
                rec.last_date = False if not rec.last_date else rec.last_date

    def _compute_location_id(self):
        for rec in self:
            location_current = self.env['work.allocation'].sudo().search(
                [('employee_id', '=', rec.id), ('date', '=', date.today())], limit=1)

            rec.location_id = location_current.current_project.id if location_current else False

    @api.depends('bank_account_id')
    def _compute_account(self):
        for rec in self:
            if rec.bank_account_id:
                rec.iban = rec.bank_account_id.iban
                rec.routing_no = rec.bank_account_id.routing_no
                rec.bank_name = rec.bank_account_id.bank_id.name
            else:
                rec.iban = ''
                rec.routing_no = ''
                rec.bank_name = rec.bank_account_id.bank_id.name

    @api.depends('equipment_ids')
    def _compute_equipment_count(self):
        for employee in self:
            employee.equipment_count = len(employee.equipment_ids.filtered(lambda l: l.state == 'active')) or 0

    @api.depends('equipment_ids')
    def _compute_equipment_non_count(self):
        for employee in self:
            employee.equipment_non_count = len(employee.equipment_ids.filtered(lambda l: l.state != 'active')) or 0
    

    def _compute_number(self):
        
        for rec in self:
            doc_passport = self.env['hr.employee.document'].sudo().search([('employee_ref_id', '=', rec.id), (
                'document_type_id', '=', self.env.ref('oh_employee_documents_expiry.document_type_02').id)],
                                                                          order="create_date desc", limit=1)
            doc_visa = self.env['hr.employee.document'].sudo().search([('employee_ref_id', '=', rec.id), (
                'document_type_id', '=', self.env.ref('oh_employee_documents_expiry.document_type_04').id)],
                                                                      order="create_date desc", limit=1)
            doc_mol = self.env['hr.employee.document'].sudo().search([('employee_ref_id', '=', rec.id), (
                'document_type_id', '=', self.env.ref('oh_employee_documents_expiry.document_type_05').id)],
                                                                     order="create_date desc", limit=1)
            doc_med = self.env['hr.employee.document'].sudo().search([('employee_ref_id', '=', rec.id), (
                'document_type_id', '=', self.env.ref('oh_employee_documents_expiry.document_type_06').id)],
                                                                     order="create_date desc", limit=1)
            doc_eid = self.env['hr.employee.document'].sudo().search([('employee_ref_id', '=', rec.id), (
                'document_type_id', '=', self.env.ref('oh_employee_documents_expiry.document_type_07').id)],
                                                                     order="create_date desc", limit=1)
            doc_uid = self.env['hr.employee.document'].sudo().search([('employee_ref_id', '=', rec.id), (
                'document_type_id', '=', self.env.ref('oh_employee_documents_expiry.document_type_08').id)],
                                                                     order="create_date desc", limit=1)
            doc_drive = self.env['hr.employee.document'].sudo().search([('employee_ref_id', '=', rec.id), (
                'document_type_id', '=', self.env.ref('oh_employee_documents_expiry.document_type_01').id)],
                                                                       order="create_date desc", limit=1)
            doc_premit = self.env['hr.employee.document'].sudo().search([('employee_ref_id', '=', rec.id), (
                'document_type_id', '=', self.env.ref('oh_employee_documents_expiry.document_type_09').id)],
                                                                        order="create_date desc", limit=1)

            if len(doc_passport) != 0:
                rec.passport_id = doc_passport.name
                rec.passport_expire = doc_passport.expiry_date
            else:
                rec.passport_id = False 
                rec.passport_expire = False 

            if len(doc_visa) != 0:
                rec.visa_no = doc_visa.name
                rec.visa_expire = doc_visa.expiry_date
            else:
                rec.visa_no = False 
                rec.visa_expire = False 
            if len(doc_mol) != 0:
                rec.mol_no = doc_mol.name
                rec.mol_expire = doc_mol.expiry_date
            else:
                rec.mol_no = False 
                rec.mol_expire = False 
            if len(doc_med) != 0:
                rec.med_no = doc_med.name
                rec.med_expire = doc_med.expiry_date
            else:
                rec.med_no =  False 
                rec.med_expire =  False 

            if len(doc_eid) != 0:
                rec.eid_no = doc_eid.name
                rec.eid_expire = doc_eid.expiry_date
            else:
                rec.eid_no = False 
                rec.eid_expire = False 

            if len(doc_uid) != 0:
                rec.uid_no = doc_uid.name
                rec.uid_expire = doc_uid.expiry_date
            else:
                rec.uid_no = False 
                rec.uid_expire = False 
            if len(doc_drive) != 0:
                rec.drive_no = doc_drive.name
                rec.drive_expire = doc_drive.expiry_date
            else:
                rec.drive_no =  False 
                rec.drive_expire = False 
            if len(doc_premit) != 0:
                rec.permit_no = doc_premit.name
                rec.work_permit_expiration_date = doc_premit.expiry_date
            else:
                rec.permit_no = False 
                rec.work_permit_expiration_date =  False 

    def _compute_adv_count(self):
        """Compute the number of Advance associated with the employee."""
        for rec in self:
            self.adv_count = self.env['salary.advance'].search_count(
                [('employee_id', '=', rec.id)])

    def action_adv_view(self):
        """ Opens a view to list all documents related to the current
         employee."""
        self.ensure_one()
        return {
            'name': _('Advance'),
            'domain': [('employee_id', '=', self.id)],
            'res_model': 'salary.advance',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'help': _('''<p class="oe_view_nocontent_create">
                               Click to Create for New Advance
                            </p>'''),
            'limit': 80,
            'context': "{'default_employee_id': %s}" % self.id
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('first_name'):
                mid =' '+vals.get('middle_name')+' ' if 'middle_name' in vals and type(vals.get('middle_name')) == type('') else ' '
                vals['name'] = vals.get('first_name') + '' + str(mid) + '' + vals.get('last_name')
        employees = super().create(vals_list)
        employees.sudo().create_job_code_history()
        employees.sudo().generate_random_barcode()
        employees.sudo().create_work_allocation_new_employee()
        return employees

    def create_job_code_history(self):
        for i in self:
            self.env['job.codes'].sudo().create({
                'employee_id': i.id,
                'code': i.job_code,
                'job_id': i.job_id.id,
            })
            self.env['job.history'].sudo().create({
                'employee_id': i.id,
                'start_date': datetime.now(),
                'state': 'current',
                'current_value': i.job_code,
                'current_dis': i.job_title})

    def write(self,vals_list):
        res = super(EmployeeInherit, self).write(vals_list)

        if 'job_id' in vals_list and self.active:
            if self.job_id.id not in [self.env.ref('hr_edit.prep').id,
                                 self.env.ref('hr_edit.plaster').id,
                                 self.env.ref('hr_edit.operation').id,
                                 self.env.ref('hr_edit.rush').id,
                                 self.env.ref('hr_edit.block').id,
                                 self.env.ref('hr_edit.helper').id,
                                 self.env.ref('hr_edit.tile_m').id,
                                 self.env.ref('hr_edit.tile_h').id,
                                 ]:
                if self.env['work.allocation'].sudo().search([('employee_id', '=', self.id),('date', '=', self.write_date.date())]):
                   self.env['work.allocation'].sudo().search([('employee_id', '=', self.id),('date', '=', self.write_date.date())]).unlink()

            if not self.env['work.allocation'].sudo().search([('employee_id', '=', self.id),('date', '=', self.write_date.date())]):

                self.sudo().create_work_allocation_new_employee()
        elif 'job_id' in vals_list and 'active' in vals_list and vals_list['active'] == True:
            if self.job_id.id not in [self.env.ref('hr_edit.prep').id,
                                 self.env.ref('hr_edit.plaster').id,
                                 self.env.ref('hr_edit.operation').id,
                                 self.env.ref('hr_edit.rush').id,
                                 self.env.ref('hr_edit.block').id,
                                 self.env.ref('hr_edit.helper').id,
                                 self.env.ref('hr_edit.tile_m').id,
                                 self.env.ref('hr_edit.tile_h').id,
                                 ]:
                if self.env['work.allocation'].sudo().search([('employee_id', '=', self.id),('date', '=', self.write_date.date())]):
                   self.env['work.allocation'].sudo().search([('employee_id', '=', self.id),('date', '=', self.write_date.date())]).unlink()

            if not self.env['work.allocation'].sudo().search([('employee_id', '=', self.id),('date', '=', self.write_date.date())]):
                
                self.sudo().create_work_allocation_new_employee()
        elif 'active' in vals_list and vals_list['active'] == True:
            if self.job_id.id not in [self.env.ref('hr_edit.prep').id,
                                 self.env.ref('hr_edit.plaster').id,
                                 self.env.ref('hr_edit.operation').id,
                                 self.env.ref('hr_edit.rush').id,
                                 self.env.ref('hr_edit.block').id,
                                 self.env.ref('hr_edit.helper').id,
                                 self.env.ref('hr_edit.tile_m').id,
                                 self.env.ref('hr_edit.tile_h').id,
                                 ]:
                if self.env['work.allocation'].sudo().search([('employee_id', '=', self.id),('date', '=', self.write_date.date())]):
                   self.env['work.allocation'].sudo().search([('employee_id', '=', self.id),('date', '=', self.write_date.date())]).unlink()

            if not self.env['work.allocation'].sudo().search([('employee_id', '=', self.id),('date', '=', self.write_date.date())]):
                
                self.sudo().create_work_allocation_new_employee()
        

        return res
        

    def create_work_allocation_new_employee(self):
        
        for rec in self:
            if rec.job_id.id in [self.env.ref('hr_edit.prep').id,
                                 self.env.ref('hr_edit.plaster').id,
                                 self.env.ref('hr_edit.operation').id,
                                 self.env.ref('hr_edit.rush').id,
                                 self.env.ref('hr_edit.block').id,
                                 self.env.ref('hr_edit.helper').id,
                                 self.env.ref('hr_edit.tile_m').id,
                                 self.env.ref('hr_edit.tile_h').id,
                                 ]:
                vals = {'job_code': self.env['job.codes'].sudo().search([('employee_id', '=', rec.id)]).id,
                        'employee_id': rec.id,
                        'designation': rec.job_id.id,
                        'current_project': False,

                        'date': date.today(),
                        }
                self.env['work.allocation'].sudo().create(vals)

    @api.onchange('job_code', 'job_title')
    def take_code(self):

        if self.job_code and self._origin.id:

            emp_edit = self.env['job.codes'].sudo().search([('employee_id', '=', self._origin.id)])
            if emp_edit:
                for rec in emp_edit:
                    rec.code = self.job_code
                    rec.job_id = self.job_id.id
            if not emp_edit and self._origin.job_code != 'False':
                self.env['job.codes'].sudo().create({
                    'employee_id': self._origin.id,
                    'code': self.job_code,
                    'job_id': self._origin.job_id.id,
                })

            employee_id = self.env['hr.employee'].search([('id', '=', self._origin.id)])
            start_date = False
            if self.job_code != '':
                job = self.env['job.history'].sudo().search(
                    [('current_value', '=', self._origin.job_code), ('employee_id', '=', self._origin.id)],
                    order="create_date desc", limit=1)
                if len(job) != 0:
                    job.updated_date = datetime.now() if (datetime.now() - timedelta(
                        days=1)).date() < job.start_date else datetime.now() - timedelta(days=1)
                    job.state = 'expiry'

            elif self.job_title != '':
                job = self.env['job.history'].sudo().search(
                    [('current_dis', '=', self._origin.job_code), ('employee_id', '=', self._origin.id)],
                    order="create_date desc", limit=1)
                if len(job) != 0:
                    job.updated_date = datetime.now() if (datetime.now() - timedelta(
                        days=1)).date() < job.start_date else datetime.now() - timedelta(days=1)
                    job.state = 'expiry'

            elif self.job_code != '' and self.job_title != '':
                job = self.env['job.history'].sudo().search(
                    [('current_dis', '=', self._origin.job_code), ('current_value', '=', self._origin.job_code),
                     ('employee_id', '=', self._origin.id)], order="create_date desc", limit=1)
                if len(job) != 0:
                    job.updated_date = datetime.now() if (datetime.now() - timedelta(
                        days=1)).date() < job.start_date else datetime.now() - timedelta(days=1)
                    job.state = 'expiry'

            vals = {
                'employee_id': self._origin.id,
                'employee_name': employee_id.name,
                'updated_date': False,
                'start_date': datetime.now(),
                'state': 'current',
                'changed_field': 'Job Code',
                'current_value': self.job_code,
                'old_val': self._origin.job_code,
                'current_dis': self.job_title,
                'old_dis': self._origin.job_title,

            }
            self.env['job.history'].sudo().create(vals)

    def job_details(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('hr.group_hr_manager'):
            return {
                'name': _("job History"),
                'view_mode': 'tree',
                'res_model': 'job.history',
                'type': 'ir.actions.act_window',
                # 'target': 'new',
                # 'domain': [('employee_id', '=', self.id)],
            }
        elif self.id == self.env.user.employee_id.id:
            return {
                'name': _("job History"),
                'view_mode': 'tree',
                'res_model': 'job.history',
                'type': 'ir.actions.act_window',
                # 'target': 'new',
            }
        else:
            raise UserError('You cannot access this field!!!!')

    @api.onchange('first_name', 'middle_name', 'last_name')
    def _onchange_name(self):
        if self.first_name and self.last_name:
            mid = ' ' + self.middle_name+ ' ' if self.middle_name else ' '
            self.name = self.first_name + str(mid)  + self.last_name

    # @api.depends('contract_ids')
    # def _compute_joining_date(self):
    #     """Compute the joining date of the employee based on their contract
    #      information."""
    #     for employee in self:
    #         employee.joining_date = min(
    #             employee.contract_id.mapped('date_start')) \
    #             if employee.contract_id else False
    @api.depends('contract_ids')
    def _compute_joining_date_first(self):
        
        for rec in self:
            all_valiad_contract = rec.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel'])
            first_contract = sorted(all_valiad_contract, key=lambda x: x.id, reverse=True)
           
            if first_contract:
                rec.joining_contract = first_contract[0].date_start
                rec.first_wage = first_contract[0].wage
            else:
                rec.joining_contract = False
                rec.first_wage = False

    @api.onchange('location_id')
    def _onchange_location(self):
        employee_id = self.env['hr.employee'].search([('id', '=', self._origin.id)])
        vals = {
            'employee_id': self._origin.id,
            'employee_name': employee_id.name,
            'updated_date': datetime.now(),
            'changed_field': 'Location',
            'current_value': self.location_id.name,
            'old_val': self._origin.location_id.name,

        }
        self.env['location.history'].sudo().create(vals)

    def location_details(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('hr.group_hr_manager'):
            return {
                'name': _("Location History"),
                'view_mode': 'tree',
                'res_model': 'location.history',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'domain': [('employee_id', '=', self.id)],
            }
        elif self.id == self.env.user.employee_id.id:
            return {
                'name': _("Location History"),
                'view_mode': 'tree',
                'res_model': 'location.history',
                'type': 'ir.actions.act_window',
                'target': 'new',
            }
        else:
            raise UserError('You cannot access this field!!!!')

    def find_allocation(self, employee,leave_type,allocation_period):
        search_allocation = self.env['hr.leave.allocation'].sudo().search(
                    [("holiday_status_id", "=", leave_type.id),
                     ('employee_id', '=', employee.id), 
                     ('number_of_days', '=', float(allocation_period)),]).filtered(lambda l:l.create_date.month == date.today().month)
        return True if search_allocation else False
    def create_for_staff(self, employee, leave_type, allocation_period,annual_leave,allocation_max):
        for emp in employee:
            period = emp.contract_ids.filtered(lambda l: l.testing_period != 0)
            month = period[0].testing_period * 30
            
            
            if emp.joining_date_first and emp.joining_date_first + timedelta(
                    days=month) < date.today() and not self.check_max_allocation(emp, annual_leave, allocation_max) and not self.find_allocation(emp,leave_type,allocation_period):
                allocation = self.env['hr.leave.allocation'].sudo().create({
                    "name": emp.name,
                    "date_from": date(date.today().year, date.today().month, 1),
                    # "date_to": date(date.today().year, 12, calendar.monthrange(date.today().year, date.today().month)[1]),
                    "holiday_type": "employee",
                    "employee_id": emp.id,
                    "number_of_days": float(allocation_period),
                    "holiday_status_id": leave_type.id,
                    "allocation_type": "regular",
                    "state": "confirm"
                })
                allocation.sudo().write({'state': 'validate'})
                first_period = allocation_period * month / 30 
                msg = _('First Allocation after %s/year period from joining date(%s)') % (
                    first_period / 12, emp.joining_date_first)
                first_allocation = self.env['hr.leave.allocation'].sudo().with_context(active_test=False).search(
                    [("holiday_status_id", "=", leave_type.id),
                     ('employee_id', '=', emp.id), 
                     ('notes', '=', msg)])
                        
                if not first_allocation and not emp.get_first:
                    allocation = self.env['hr.leave.allocation'].sudo().create({
                        "name": emp.name,
                        "date_from": date(date.today().year, date.today().month, 1),
                        # "date_to": date(date.today().year, 12,
                        #                 calendar.monthrange(date.today().year, date.today().month)[1]),
                        "holiday_type": "employee",
                        "employee_id": emp.id,
                        "number_of_days": float(first_period),
                        "holiday_status_id": leave_type.id,
                        "allocation_type": "regular",
                        "state": "confirm",
                        "notes": msg
                    })
                    allocation.sudo().write({'state': 'validate'})
                    emp.get_first = True

    def create_for_staff_foreman_and_labor_a(self, employee, leave_type, allocation_period,annual_leave,allocation_max):
        complete_staff_foreman_period = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.complete_staff_foreman_period')) * 12
        filter_employee = employee.filtered(lambda l: l.joining_date_first and l.joining_date_first + relativedelta(months=int(complete_staff_foreman_period)) < date.today())
        first_period_staff_foreman = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.first_period_staff_foreman'))
        max_days = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.limit_number_of_day_staff_foreman'))
        
        for emp in filter_employee:
            
            if not self.check_max_allocation(emp, annual_leave, allocation_max):
                mag = _('First Allocation after %s/year period from joining date(%s)') % (
                    complete_staff_foreman_period / 12, emp.joining_date_first)
                first_allocation = self.env['hr.leave.allocation'].sudo().with_context(active_test=False).search(
                    [("holiday_status_id", "=", leave_type.id),
                     ('employee_id', '=', emp.id),
                     ('notes', '=', mag)])
                if not first_allocation and not emp.get_first:
                    allocation = self.env['hr.leave.allocation'].sudo().create({
                        "name": emp.name,
                        "date_from": date(date.today().year, date.today().month, 1),
                        # "date_to": date(date.today().year, 12,
                        #                 calendar.monthrange(date.today().year, date.today().month)[1]),
                        "holiday_type": "employee",
                        "employee_id": emp.id,
                        "number_of_days": float(first_period_staff_foreman),
                        "holiday_status_id": leave_type.id,
                        "allocation_type": "regular",
                        "state": "confirm",
                        "notes": mag
                    })
                    allocation.sudo().write({'state': 'validate'})
                    emp.get_first = True
                leaves = self.env['hr.leave'].sudo().search([]).filtered(
                    lambda l: l.employee_id.id == emp.id
                              and l.date_from.date().month == date.today().month
                              and l.state == 'validate'
                )
                long_leaves = self.env['hr.leave'].sudo().search([], order='date_to').filtered(
                    lambda l: l.employee_id.id == emp.id
                              and l.state == 'validate'
                )
                
                if not leaves and (not long_leaves or date.today() >= emp.next_schedule_date) and not self.find_allocation(emp,leave_type,allocation_period):
                    allocation = self.env['hr.leave.allocation'].sudo().create({
                        "name": emp.name,
                        "date_from": date(date.today().year, date.today().month, 1),
                        # "date_to": date(date.today().year, 12,
                        #                 calendar.monthrange(date.today().year, date.today().month)[1]),
                        "holiday_type": "employee",
                        "employee_id": emp.id,
                        "number_of_days": float(allocation_period),
                        "holiday_status_id": leave_type.id,
                        "allocation_type": "regular",
                        "state": "confirm"
                    })
                    allocation.sudo().write({'state': 'validate'})
                
                
                if long_leaves and long_leaves[-1].date_to.date() + relativedelta(months=int(complete_staff_foreman_period)) < date.today() and emp.next_schedule_date and (emp.next_schedule_date.year == date.today().year and emp.next_schedule_date.month == date.today().month):
                    mag = _('Allocation after %s period from last leave (%s)') % (
                        complete_staff_foreman_period / 12, long_leaves[-1].date_to.date())
                    # last_leave_allocation = self.env['hr.leave.allocation'].sudo().search(
                    #     [("holiday_status_id", "=", leave_type.id),
                    #      ('employee_id', '=', emp.id), ('number_of_days', '=', first_period_staff_foreman),
                    #      ('state', '=', 'validate'), ('notes', '=', mag)])
                    
                    allocation = self.env['hr.leave.allocation'].sudo().create({
                        "name": emp.name,
                        "date_from": date(date.today().year, date.today().month, 1),
                        # "date_to": date(date.today().year, 12,
                        #                 calendar.monthrange(date.today().year, date.today().month)[1]),
                        "holiday_type": "employee",
                        "employee_id": emp.id,
                        "number_of_days": float(first_period_staff_foreman),
                        "holiday_status_id": leave_type.id,
                        "allocation_type": "regular",
                        "state": "confirm",
                        "notes": mag
                    })
                    allocation.sudo().write({'state': 'validate'})
    
    def create_for_labor_n(self, employee, leave_type, allocation_period,annual_leave,allocation_max):
        complete_labor_n_period = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.complete_labor_n_period')) * 12
        filter_employee = employee.filtered(lambda l: l.joining_date_first and l.joining_date_first + relativedelta(months=int(complete_labor_n_period)) < date.today())
        first_period_labor_n = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.first_period_labor_n'))
        max_days = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.limit_number_of_day_staff_foreman'))
        for emp in filter_employee:
            if not self.check_max_allocation(emp, annual_leave, allocation_max):
                mag = _('First Allocation after %s/year period from joining date(%s)') % (
                    complete_labor_n_period / 12, emp.joining_date_first)
                first_allocation = self.env['hr.leave.allocation'].sudo().with_context(active_test=False).search(
                    [("holiday_status_id", "=", leave_type.id),
                     ('employee_id', '=', emp.id),
                     ('notes', '=', mag)])
                if not first_allocation and not emp.get_first:
                    allocation = self.env['hr.leave.allocation'].sudo().create({
                        "name": emp.name,
                        "date_from": date(date.today().year, date.today().month, 1),
                        # "date_to": date(date.today().year, 12,
                        #                 calendar.monthrange(date.today().year, date.today().month)[1]),
                        "holiday_type": "employee",
                        "employee_id": emp.id,
                        "number_of_days": float(first_period_labor_n),
                        "holiday_status_id": leave_type.id,
                        "allocation_type": "regular",
                        "state": "confirm",
                        "notes": mag
                    })
                    allocation.sudo().write({'state': 'validate'})
                    emp.get_first = True
                leaves = self.env['hr.leave'].sudo().search([]).filtered(
                    lambda l: l.employee_id.id == emp.id
                              and l.date_from.date().month == date.today().month
                              and l.state == 'validate'
                )
                long_leaves = self.env['hr.leave'].sudo().search([], order='date_to').filtered(
                    lambda l: l.employee_id.id == emp.id
                              and l.state == 'validate'
                )
    
                if not leaves and (not long_leaves or date.today() >= emp.next_schedule_date) and not self.find_allocation(emp,leave_type,allocation_period):
                    if not self.check_max_allocation(emp, annual_leave, allocation_max):
                        allocation = self.env['hr.leave.allocation'].sudo().create({
                            "name": emp.name,
                            "date_from": date(date.today().year, date.today().month, 1),
                            # "date_to": date(date.today().year, 12,
                            #                 calendar.monthrange(date.today().year, date.today().month)[1]),
                            "holiday_type": "employee",
                            "employee_id": emp.id,
                            "number_of_days": float(allocation_period),
                            "holiday_status_id": leave_type.id,
                            "allocation_type": "regular",
                            "state": "confirm"
                        })
                        allocation.sudo().write({'state': 'validate'})
    
                if long_leaves and long_leaves[-1].date_to.date() + relativedelta(months=int(complete_labor_n_period)) < date.today() and emp.next_schedule_date and (emp.next_schedule_date.year == date.today().year and emp.next_schedule_date.month == date.today().month):
                    mag = _('Allocation after %s period from last leave (%s)') % (
                        complete_labor_n_period / 12, long_leaves[-1].date_to.date())
                    # last_leave_allocation = self.env['hr.leave.allocation'].sudo().search(
                    #     [("holiday_status_id", "=", leave_type.id),
                    #      ('employee_id', '=', emp.id), ('number_of_days', '=', first_period_labor_n),
                    #      ('state', '=', 'validate'), ('notes', '=', mag)])
                    # if not last_leave_allocation:
                    allocation = self.env['hr.leave.allocation'].sudo().create({
                        "name": emp.name,
                        "date_from": date(date.today().year, date.today().month, 1),
                        # "date_to": date(date.today().year, 12,
                        #                 calendar.monthrange(date.today().year, date.today().month)[1]),
                        "holiday_type": "employee",
                        "employee_id": emp.id,
                        "number_of_days": float(first_period_labor_n),
                        "holiday_status_id": leave_type.id,
                        "allocation_type": "regular",
                        "state": "confirm",
                        "notes": mag
                    })
                    allocation.sudo().write({'state': 'validate'})
    def check_max_allocation(self, employees, annual_leave, allocation_max):
        all_alloc = 0
        for emp in employees:
            all_alloc = sum([alloc.number_of_days for alloc in self.env['hr.leave.allocation'].sudo().search(
                [("holiday_status_id", "=", annual_leave.id),
                 ('employee_id', '=', emp.id),
                 ('state', '=', 'validate')])])

        return True if all_alloc >= allocation_max else False

    def create_leave_annual(self):
        employees_evrey_month = self.env['hr.employee'].sudo().search(
            []).filtered(lambda l: l.contracts_count != 0 and l.joining_date_first and l.contract_ids.filtered(
                lambda l: l.testing_period != 0))
        _logger.info("........employees_evrey_month:{}".format(employees_evrey_month))
        # month = employees.contract_ids.filtered(lambda l: l.testing_period != 0)
        annual_leave = self.env.ref("hr_edit.annual_leave")
        allocation_max = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.allocation_max'))
        
        
        # month = month[0].testing_period * 30
        # employees_evrey_month = employees.filtered(
        #     lambda l: l.joining_date_first and )

        allocation_period = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.allocation_period'))
        self.create_for_staff(employee=employees_evrey_month.filtered(lambda l: l.type_work == 'staff'),
                              leave_type=annual_leave, allocation_period=allocation_period,allocation_max=allocation_max,annual_leave=annual_leave)
        self.create_for_staff_foreman_and_labor_a(
            employee=employees_evrey_month.filtered(lambda l: l.type_work in ['staff_for', 'labor_a']),
            leave_type=annual_leave, allocation_period=allocation_period,allocation_max=allocation_max,annual_leave=annual_leave)
        

        self.create_for_labor_n(employee=employees_evrey_month.filtered(lambda l: l.type_work == 'labor_n'),               leave_type=annual_leave,allocation_period=allocation_period,
                                allocation_max=allocation_max,annual_leave=annual_leave)

class EmployeeWizardInherit(models.TransientModel):
    _inherit="hr.departure.wizard"

    def action_register_departure(self):
        res = super(EmployeeWizardInherit,self).action_register_departure()
        self.env['job.codes'].sudo().search([('employee_id', '=', self.employee_id.id)]).active=False

        return res

class ResumeLine(models.Model):
    _inherit = 'hr.resume.line'

    file_cer = fields.Binary('Education Certificate')
