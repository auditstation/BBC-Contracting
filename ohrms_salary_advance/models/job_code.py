import logging

from datetime import datetime
import time
from odoo import exceptions
from odoo.exceptions import UserError
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class JobCode(models.Model):
    _name = 'job.codes'
    _description = 'Job code'
    _rec_name = 'code'
    employee_id = fields.Many2one('hr.employee',ondelete="cascade")
    job_id = fields.Many2one('hr.job')
    code = fields.Char()
    active = fields.Boolean(default=True)
