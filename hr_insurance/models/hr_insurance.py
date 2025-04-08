# -- coding: utf-8 --
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author:  Anjhana A K(<https://www.cybrosys.com>)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class HrInsurance(models.Model):
    """created a new model for employee insurance"""
    _name = 'hr.insurance'
    _description = 'HR Insurance'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True, help="Employee")
    company_name = fields.Char('Insurance Company Name')
    plan = fields.Char('Plan',required=True)

    date_from = fields.Date(string='Date From',

                            help="Start date")
    date_to = fields.Date(string='Date To', help="Expiry date",required=True)
    state = fields.Selection([('active', 'Active'),
                              ('expired', 'Expired'), ],
                             default='active', string="State",
                             compute='get_status')
    file_insurance = fields.Binary('Medical Insurance Card')
    file_insurance_name = fields.Char('Medical Insurance Card')

    def get_status(self):
        """this function is get and set state"""
        current_date = fields.date.today()
        for rec in self:
            if rec.date_to <= current_date:
                rec.state = 'expired'
            else:
                rec.state = 'active'
