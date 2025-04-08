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


class PayslipLineEdit(models.Model):
    _inherit = "hr.payslip.line"
    delay = fields.Boolean()
    paid = fields.Boolean()
    exempt = fields.Boolean()
    delay_period = fields.Selection([
                                     ('1', '1-month delay'),
                                     ('2', '2-month delay'),
                                     ('3', '3-month delay'),
                                     ('4', '4-month delay'),
                                     ('5', '5-month delay'),
                                     ],
                                    default='1')
