# -*- coding: utf-8 -*-
from datetime import datetime, date
from odoo import models, api, fields, _
from odoo.exceptions import UserError
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProductionLine(models.Model):
    _name = 'production.line'
    _description = "Production line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _job_field_domain(self):
        return [
            ('job_id', 'in',
             [self.env.ref('hr_edit.prep').id,
              self.env.ref('hr_edit.plaster').id,
              self.env.ref('hr_edit.operation').id,
              self.env.ref('hr_edit.block').id,
              self.env.ref('hr_edit.helper').id,
              self.env.ref('hr_edit.tile_m').id,

              ]
             )
        ]

    employee_id = fields.Many2one('hr.employee', domain=_job_field_domain)
    job_code = fields.Many2one('job.codes', string='Job code', domain=_job_field_domain)
    work_location_line_id = fields.Many2one('work.location.line')
    work_location_id = fields.Many2one('work.location')
    start_date = fields.Date('Date')
    # Block Hours
    aac_sob_hour = fields.Float('AAC/SOB', group_operator='sum')
    hollow_hour = fields.Float('HOLLOW', group_operator='sum')
    layout_hour = fields.Float('LAYOUT', group_operator='sum')
    # Plaster Hours
    internal_plaster_hour = fields.Float('INTERNAL PLASTER', group_operator='sum')
    external_plaster_hour = fields.Float('EXTERNAL PLASTER', group_operator='sum')
    # Preparation Hours
    internal_angles_hour = fields.Float('INTERNAL ANGLES', group_operator='sum')
    external_angles_hour = fields.Float('EXTERNAL ANGLES', group_operator='sum')
    point_hour = fields.Float('POINT', group_operator='sum')
    point_s = fields.Float('POINT S', group_operator='sum')
    point_external = fields.Float('POINT External', group_operator='sum')
    # TILE MASON
    floor_tiles = fields.Float('FLOOR TILES', group_operator='sum')
    parquet_tiles = fields.Float('PARQUET TILES', group_operator='sum')
    wall_tiles = fields.Float('WALL TILES', group_operator='sum')
    mosaic = fields.Float('MOSAIC', group_operator='sum')
    hreshold = fields.Float('HRESHOLD', group_operator='sum')
    layout_tiles = fields.Float('Layout tiles', group_operator='sum')
    skirting = fields.Float('SKIRTING', group_operator='sum')
    # Helper
    hours = fields.Float('HOURS', group_operator='sum')
    rush_coat = fields.Float(group_operator='sum')
    category = fields.Selection(
        [('all', 'ALL'), ('block', 'BLOCK'), ('plaster', 'PLASTER'), ('preparation', 'PREPARATION'), ('tile', 'TILE'),
         ('helper', 'HELPER')],
        string='Production Category', default='all')
    lock = fields.Boolean('lock', compute="_check_for_lock")
    absence = fields.Selection([('1', '1D'), ('2', '2D')])
    leave = fields.Char('On leave', compute="_compute_leave",  search='_search_leave')
    reason = fields.Char('Reason')
    # reason_file = fields.Binary()
    attachment_ids = fields.One2many('ir.attachment', 'res_id', string="Attachments")
    supported_attachment_ids = fields.Many2many(
        'ir.attachment', string="Attach File", compute='_compute_supported_attachment_ids',
        inverse='_inverse_supported_attachment_ids')
    state_paid = fields.Boolean('Paid')
    external_rush = fields.Float('External Rush',group_operator='sum')
    color = fields.Boolean()

    def _search_leave(self, operator, value):
        records = self.env['production.line'].sudo().search([]).filtered(
            lambda l: l.leave and str(value) in l.leave)
        return [('id', 'in', records.ids)]

   

    @api.model
    def write(self, vals_list):
        res = super().write(vals_list)

        if 'absence' in vals_list:
            if vals_list['absence'] == '1' and 'reason' not in vals_list:
                raise ValidationError('You should put the reason')

        return res

    @api.depends('attachment_ids')
    def _compute_supported_attachment_ids(self):
        for holiday in self:
            holiday.supported_attachment_ids = holiday.attachment_ids

    def _inverse_supported_attachment_ids(self):
        for holiday in self:
            holiday.attachment_ids = holiday.supported_attachment_ids

    def _check_for_lock(self):
        for rec in self:
            day = (fields.Date.today() - self.create_date.date()).days
            lock_pro_after = float(self.env['ir.config_parameter'].sudo().get_param(
                'hr_edit.lock_pro_after')) or 7
            if not self.env.user.has_group('base.group_erp_manager'):
                if day > lock_pro_after:
                    rec.lock = True
                else:
                    rec.lock = False
            else:
                rec.lock = False
    @api.depends('employee_id')
    def _compute_leave(self):
        for rec in self:
            
            if self.env['hr.leave'].sudo().search(
                    [('employee_ids', 'in', [i.id for i in rec.employee_id]), ('state', '=', 'validate')]).filtered(
                lambda x: x.request_date_from <= rec.start_date and x.request_date_to >= rec.start_date):
                rec.leave = 'ON LEAVE at date %s' % rec.start_date.strftime("%d/%m/%Y")
            else:
                rec.leave = ''

    def check_for_lock(self):
        for rec in self:
            day = (fields.Date.today() - self.create_date.date()).days
            lock_pro_after = float(self.env['ir.config_parameter'].sudo().get_param(
                'hr_edit.lock_pro_after')) or 7
            if not self.env.user.has_group('base.group_erp_manager'):
                if day > lock_pro_after:
                    lock = True
                else:
                    lock = False
            else:
                lock = False

    @api.onchange('employee_id')
    def onchange_code(self):
        if self.employee_id:
            self.job_code = self.env['job.codes'].sudo().search([('employee_id', '=', self.employee_id.id)]).id

    @api.onchange('job_code')
    def onchange_employee(self):
        if self.job_code:
            self.employee_id = self.env['job.codes'].sudo().search([('id', '=', self.job_code.id)]).employee_id.id

    @api.onchange('job_code', 'employee_id','work_location_id')
    def onchange_work_location(self):
        if self.employee_id and self.job_code:
            
                # return {
                #     'warning': {
                #         'title': _('Warning'),
                #         'message': _("This data is exist in your system", ), }, }
            # if self.env['production.line'].sudo().search(
            #         [('employee_id', '=', self.employee_id.id), ('start_date', '=', self.start_date)]):
            #     raise ValidationError('This data is exist in your system')
            domain = [('employee_id', '=', self.employee_id.id), ('date', '=', self.start_date)]
            self.work_location_id = self.env['work.allocation'].sudo().search(domain).current_project.id
            dubl = self.env['production.line'].sudo().search(
                [('employee_id', '=', self.employee_id.id),('work_location_id', '=', self.work_location_id.id),('start_date', '=', self.start_date)])
            if dubl:
                # dubl.color = True
                raise ValidationError('This data is exist in your system')
            if self.env['hr.employee'].sudo().search_count(
                    [('id', '=', self.employee_id.id), ('job_id', '=', self.env.ref('hr_edit.plaster').id)]) == 1:
                self.category = 'plaster'
            if self.env['hr.employee'].sudo().search_count(
                    [('id', '=', self.employee_id.id), ('job_id', '=', self.env.ref('hr_edit.block').id)]) == 1:
                self.category = 'block'

            if self.env['hr.employee'].sudo().search_count(
                    [('id', '=', self.employee_id.id), ('job_id', '=', self.env.ref('hr_edit.prep').id)]) == 1:
                self.category = 'preparation'
            if self.env['hr.employee'].sudo().search_count(
                    [('id', '=', self.employee_id.id), ('job_id', '=', self.env.ref('hr_edit.tile_m').id)]) == 1:
                self.category = 'tile'

            if self.env['hr.employee'].sudo().search_count([('id', '=', self.employee_id.id), (
                    'job_id', 'in', [self.env.ref('hr_edit.helper').id, self.env.ref('hr_edit.operation').id,self.env.ref('hr_edit.rush').id,self.env.ref('hr_edit.tile_h').id])]) == 1:
                self.category = 'helper'
