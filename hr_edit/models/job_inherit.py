# -*- coding: utf-8 -*-
from odoo import fields, models, api


class EmployeeInherit(models.Model):
    _inherit = 'hr.job'

    lock = fields.Boolean('Lock')


class DocumentInherit(models.Model):
    _inherit = 'hr.employee.document'

    job_code = fields.Many2one('job.codes', invisible=1,
                               copy=False,
                               help='Specify the job code.')

    @api.onchange('employee_ref_id')
    def onchange_code(self):
        if self.employee_ref_id:
            self.job_code = self.env['job.codes'].sudo().search([('employee_id', '=', self.employee_ref_id.id)]).id

    @api.onchange('job_code')
    def onchange_employee(self):
        if self.job_code:
            self.employee_ref_id = self.env['job.codes'].sudo().search([('id', '=', self.job_code.id)]).employee_id.id


class BankInherit(models.Model):
    _inherit = "res.partner.bank"
    iban = fields.Char('IBAN')
    routing_no = fields.Char('Routing No')
