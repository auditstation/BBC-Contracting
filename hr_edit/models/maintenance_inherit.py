# -*- coding: utf-8 -*-
from odoo import api, _, fields, models, tools
from datetime import datetime, timedelta, date
import logging

_logger = logging.getLogger(__name__)

def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


class MaintenanceInherit(models.Model):
    _inherit = 'maintenance.equipment'
    _description = 'Equipment'

    dismissed_date = fields.Date(tracking=True)
    assign_date = fields.Date(compute='_compute_equipment_assign', tracking=True, store=True, readonly=False, copy=True)
    state = fields.Selection([('active', 'Active'),
                              ('dismissed', 'Dismissed')],
                             required=True, tracking=True, default='active')
    used_period = fields.Float(compute='_compute_used_period')

    @api.onchange('state')
    def _onchange_fields(self):
        for rec in self:
            if rec.state == 'dismissed' and not rec.dismissed_date:
                rec._origin.dismissed_date = fields.Date.today()
            elif rec.state == 'active':
                rec._origin.dismissed_date = False

    @api.depends('dismissed_date', 'assign_date')
    def _compute_used_period(self):
        for rec in self:
            if rec.assign_date and not rec.dismissed_date:
                rec.used_period = diff_month(date.today(), rec.assign_date)
            elif rec.assign_date and rec.dismissed_date:
                rec.used_period = diff_month(rec.dismissed_date, rec.assign_date)
            else:
                rec.used_period = 0
