# -*- coding: utf-8 -*-
from datetime import datetime, date
from odoo import models, api, fields, _
from odoo.exceptions import UserError
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WorkLocationLine(models.Model):
    _name = 'work.location.line'
    _description = "Work allocation line"
    _rec_name = "start_date"

    work_location_id = fields.Many2one('work.location')
    start_date = fields.Date('Date')
    category = fields.Selection(
        [('all', 'ALL'), ('block', 'BLOCK'), ('plaster', 'PLASTER'), ('preparation', 'PREPARATION'), ('tile', 'TILE'),
         ('helper', 'HELPER')],
        string='Production Category', default='all', required=True)

    production_ids = fields.Many2many('production.line')
    lock = fields.Boolean('lock', compute="_check_for_lock")

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

    @api.onchange('work_location_id', 'start_date', 'category')
    def create_lines(self):
        if self.work_location_id or self.category:
            # if self.category != 'all':
            #     if self.env['work.location.line'].sudo().search_count(
            #             [('work_location_id', '=', self.work_location_id.id), ('category', '=', self.category),
            #              ('start_date', '=', self.start_date)]) > 0:
            #         raise ValidationError("You can't create same data that exists before")

            domain = [('current_project', '=', self.work_location_id.id), ('date', '=', self.start_date)]
            if self.category == 'block':
                block_category = [i.id for i in self.env['hr.employee'].sudo().search(
                    [('job_id', '=', self.env.ref('hr_edit.block').id)])]
                domain += [('employee_id', 'in', block_category)]

            if self.category == 'plaster':
                plaster_category = [i.id for i in self.env['hr.employee'].sudo().search(
                    [('job_id', '=', self.env.ref('hr_edit.plaster').id)])]
                domain += [('employee_id', 'in', plaster_category)]

            if self.category == 'preparation':
                prep_category = [i.id for i in self.env['hr.employee'].sudo().search(
                    [('job_id', '=', self.env.ref('hr_edit.prep').id)])]
                domain += [('employee_id', 'in', prep_category)]

            if self.category == 'tile':
                tile_category = [i.id for i in self.env['hr.employee'].sudo().search(
                    [('job_id', '=', self.env.ref('hr_edit.tile_m').id)])]
                domain += [('employee_id', 'in', tile_category)]

            if self.category == 'helper':
                helper_category = [i.id for i in self.env['hr.employee'].sudo().search(
                    [('job_id', 'in', [self.env.ref('hr_edit.helper').id, self.env.ref('hr_edit.tile_h').id, self.env.ref('hr_edit.rush').id,self.env.ref('hr_edit.operation').id])])]
                domain += [('employee_id', 'in', helper_category)]

            if self.production_ids:
                self.production_ids = [(6, 0, [])]

            for rec in self.env['work.allocation'].sudo().search(domain):
                if rec.current_project:
                    if self.env['production.line'].sudo().search_count(
                            [('work_location_id', '=', self.work_location_id.id),
                             ('employee_id', '=', rec.employee_id.id), ('start_date', '=', self.start_date)]) == 0:
                        line = self.env['production.line'].sudo().create({
                            'employee_id': int(rec.employee_id),
                            'job_code': self.env['job.codes'].sudo().search(
                                [('employee_id', '=', rec.employee_id.id)]).id,
                            'category': self.category,
                            'work_location_id': self.work_location_id.id,
                            'start_date': self.start_date
                        })
                        self.production_ids = [(4, line.id)]

                    else:
                        for recs in self.env['production.line'].sudo().search(
                                [('work_location_id', '=', self.work_location_id.id),
                                 ('start_date', '=', self.start_date)]):
                            if self.category == 'block':
                                block_category = [i.id for i in self.env['hr.employee'].sudo().search(
                                    [('job_id', '=', self.env.ref('hr_edit.block').id)])]
                                if recs.employee_id.id in block_category:
                                    recs.category = self.category
                                    self.production_ids = [(4, recs.id)]

                            if self.category == 'plaster':
                                plaster_category = [i.id for i in self.env['hr.employee'].sudo().search(
                                    [('job_id', '=', self.env.ref('hr_edit.plaster').id)])]
                                if recs.employee_id.id in plaster_category:
                                    recs.category = self.category
                                    self.production_ids = [(4, recs.id)]
                            if self.category == 'preparation':
                                prep_category = [i.id for i in self.env['hr.employee'].sudo().search(
                                    [('job_id', '=', self.env.ref('hr_edit.prep').id)])]

                                if recs.employee_id.id in prep_category:
                                    recs.category = self.category
                                    self.production_ids = [(4, recs.id)]

                            if self.category == 'tile':
                                tile_category = [i.id for i in self.env['hr.employee'].sudo().search(
                                    [('job_id', '=', self.env.ref('hr_edit.tile_m').id)])]
                                if recs.employee_id.id in tile_category:
                                    recs.category = self.category
                                    self.production_ids = [(4, recs.id)]
                            if self.category == 'helper':
                                helper_category = [i.id for i in self.env['hr.employee'].sudo().search([('job_id', 'in', [self.env.ref('hr_edit.helper').id, self.env.ref('hr_edit.tile_h').id, self.env.ref('hr_edit.rush').id,self.env.ref('hr_edit.operation').id])])]
                
                                if recs.employee_id.id in helper_category:
                                    recs.category = self.category
                                    self.production_ids = [(4, recs.id)]

                            if self.category == 'all':
                                self.production_ids = [(4, recs.id)]
