# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class Medical(models.Model):
    _inherit = "insurance"
    company_name = fields.Char('Insurance Company Name')
    plan = fields.Char('Plan')
    card_no = fields.Char('Card No')
    expiry_date = fields.Date('Expiry Date')
