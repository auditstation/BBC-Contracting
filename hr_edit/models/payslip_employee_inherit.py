# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import format_date

import logging
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)
class HrPayrollStructureInherit(models.Model):
    """Class for the inherited model hr_payroll_structure. Contains fields
        related to the salary structure of the salary advance."""
    _inherit = 'hr.payroll.structure'
    _order = 'id DESC'

class HrPayslipEmployeesInherit(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    # job_code = fields.Many2one('job.codes', copy=False)

    @api.depends('department_id', 'structure_id')
    def _compute_employee_ids(self):
        payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))
        for wizard in self:
            domain = wizard._get_available_contracts_domain()
            if wizard.department_id:
                domain = expression.AND([
                    domain,
                    [('department_id', 'child_of', self.department_id.id)]
                ])
            if wizard.structure_id:
                domain = expression.AND([
                    domain,
                    [('contract_ids.struct_id', 'in', [self.structure_id.id])]
                ])

            leaves = self.env['hr.leave'].sudo().search([]).filtered(
                lambda l: l.date_to.date() >= payslip_run.date_end and l.state == 'validate'

            )
            if leaves:
                domain = expression.AND([
                    domain,
                    [('id', 'not in', leaves.employee_id.ids)]
                ])
            wizard.employee_ids = self.env['hr.employee'].search(domain)


class PayslipEdits(models.Model):
    _inherit = "hr.payslip"

