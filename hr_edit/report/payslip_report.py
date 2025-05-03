# -*- coding: utf-8 -*-
from collections import defaultdict
from odoo import models, fields, api, _, exceptions, Command
from dateutil.relativedelta import relativedelta
import time
from datetime import date, datetime, timedelta
import calendar
import logging
from odoo.exceptions import UserError, ValidationError
import base64
import tempfile

_logger = logging.getLogger(__name__)


class PayslipXlsx(models.AbstractModel):
    _name = 'report.hr_edit.print_payslip_report_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, payslips):
        # Create a worksheet
        sheet = workbook.add_worksheet('Payslip(xlsx)')
        bold = workbook.add_format({'bold': True})
        bold_center_underline = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#FFFF00',
            'bottom': 1  # Adds underline (bottom border)
        })
        special = workbook.add_format({
            'bold': True,
            'bg_color': '#D9D9D9',
            'align': 'center',
            'valign': 'vcenter',
            'bottom': 1,  # Adds underline (bottom border)
            'left': 1,  # Adds left border
            'right': 1,  # Adds right border
            'top': 1,  # Adds top border
        })
        grey_background = workbook.add_format(
            {'bg_color': '#D9D9D9', 'bold': True, 'bottom': 1})
        brown_background = workbook.add_format({'bg_color': '#C4BD97', 'valign': 'vcenter', })
        center = workbook.add_format({'valign': 'vcenter', })
        right = workbook.add_format({'valign': 'vright'})
        # Set column widths for better readability
        sheet.set_column(0, 9, 30)

        # Write the company header and payroll period
        # Merge cells A1 to C1 and apply the format
        emp = payslips[0].employee_id
        branch = 'B.B.C. BUILDING CONTRACTING L.L.C. ( DUBAI BRANCH)' if emp.branch == 'dubai' or \
                                                                         emp.on_company_sponsorship == 'no' else 'B.B. C BLDG.CONT L L C'
        mol = 'MOL ID: 698173' if emp.branch == 'dubai' or \
                                  emp.on_company_sponsorship == 'no' else 'MOL ID: 565128'
        sheet.merge_range('C1:E1', branch, bold_center_underline)
        sheet.merge_range('C2:E2', mol, bold_center_underline)
        sheet.merge_range('C3:E3',f'PAYROLL FOR THE MONTH OF {payslips[0].date_to.strftime("%B %Y")}', bold_center_underline)

        # Header for employee information
        sheet.merge_range('A6:A7', 'Sl.No', grey_background)
        sheet.merge_range('B6:B7', 'NAME OF THE EMPLOYEE', grey_background)
        sheet.merge_range('C6:C7', 'WORK PERMIT NO (8 DIGIT NO)', grey_background)
        sheet.merge_range('D6:D7', 'PERSONAL NO (14 DIGIT NO)', grey_background)
        sheet.merge_range('E6:E7', 'BANK NAME/AGENT NAME', grey_background)
        sheet.merge_range('F6:F7', 'IBAN/FAB 16 DIGIT NO', grey_background)
        sheet.merge_range('G6:G7', 'NO OF DAYS ABSENT', grey_background)
        sheet.merge_range('H6:J6', "Employee's Net Salary", special)
        sheet.write(6, 7, 'Fixed Portion', special)
        sheet.write(6, 8, 'Variable Portion', special)
        sheet.write(6, 9, 'Total Payment', special)

        # Sample data for the report (you can adapt this to loop through the actual payslip data)
        row = 7  # Starting row for data

        for idx, payslip in enumerate(payslips):
            total = payslip.line_ids[-1].total if payslip.line_ids else 0
            fix = float(self.env['ir.config_parameter'].sudo().get_param(
                'hr_edit.fixed_portion')) or 500
            fixed = fix
            if total < fixed:
                total = total
                var = 0
                fixed = total
            else:
                total = total
                var = total - fixed
                fixed = fix
            # var = payslip.line_ids[-1].total - 500 if payslip.line_ids[-1].total - 500 > 0 else payslip.line_ids[-1].total
            absence = payslip.count_unpaid if payslip.struct_id.id == self.env.ref('hr_edit.staff_structure_bbc').id else payslip.absense_days
            
            sheet.write(row, 0, idx + 1, brown_background)  # Sl.No
            sheet.write(row, 1, payslip.employee_id.name, right)  # Employee Name
            sheet.write(row, 2, payslip.employee_id.permit_no or '', center)  # Work Permit No
            sheet.write(row, 3, payslip.employee_id.mol_no or '', center)  # Personal No
            sheet.write(row, 4, payslip.employee_id.routing_no or '', center)  # Bank Name
            sheet.write(row, 5, payslip.employee_id.iban or '', center)  # IBAN
            sheet.write(row, 6, absence or 0, center)  # Days Absent
            # sheet.write(row, 7, payslip.net_salary or 0.0)  # Net Salary
            sheet.write(row, 7, fixed, center)  # Fixed Portion
            sheet.write(row, 8, var or 0.0, center)  # Variable Portion
            sheet.write(row, 9, total or 0.0, center)  # Total Payment
            row += 1
