# -*- coding: utf-8 -*-
from datetime import datetime,timedelta
from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError
import logging
from dateutil.relativedelta import relativedelta
import calendar
_logger = logging.getLogger(__name__)


def get_previous_sundays_until(limit_date,day):
    # Get today's date
    today = day

    # Check if today is Saturday
    if today.weekday() == 5:  # 5 corresponds to Saturday


        # Initialize a list to hold all previous Sundays
        previous_sundays = []

        # Start by looking for Sundays in the current month and go backwards
        current_year = today.year
        current_month = today.month

        while True:
            # Get the last day of the current month
            _, last_day = calendar.monthrange(current_year, current_month)

            # Iterate through the days of the current month (from the last day backward)
            for day in range(last_day, 0, -1):
                try:
                    import datetime
                    date = datetime.date(current_year, current_month, day)
                except ValueError:
                    # Skip invalid dates just in case
                    continue

                # Only check dates before today for the current month
                if current_month == today.month and date >= today:
                    continue

                # Check if the day is a Sunday
                if date.weekday() == 6:  # 6 corresponds to Sunday
                    # Stop if the date is before the limit date
                    if date < limit_date:
                        return previous_sundays
                    previous_sundays.append(date)

            # Move to the previous month
            if current_month == 1:  # If January, go to December of the previous year
                current_month = 12
                current_year -= 1
            else:
                current_month -= 1

            # Break the loop if the last date of the month is before the limit date
            if datetime.date(current_year, current_month, 1) < limit_date:
                break

        return previous_sundays

    else:

        return []

class OverTime(models.Model):
    _name = 'over.time'
    _rec_name = 'job_code'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _job_field_domain(self):
        return [
            ('job_id', 'in',
             [self.env.ref('hr_edit.prep').id,
              self.env.ref('hr_edit.plaster').id,
              self.env.ref('hr_edit.operation').id,
              self.env.ref('hr_edit.rush').id,
              self.env.ref('hr_edit.block').id,
              self.env.ref('hr_edit.helper').id,
              self.env.ref('hr_edit.tile_m').id,
              self.env.ref('hr_edit.tile_h').id,
              ]
             )
        ]

    job_code = fields.Many2one('job.codes', string='Job code', domain=_job_field_domain)
    employee_id = fields.Many2one('hr.employee', string='Employee', domain=_job_field_domain)
    designation = fields.Many2one(related='employee_id.job_id')
    absence_next_day = fields.Selection([('no','No'),('yes','Yes')],default='no',readonly=True)
    aac_sob_hour = fields.Float('AAC Block', group_operator='sum')
    hollow_hour = fields.Float('HOLLOW Block', group_operator='sum')
    layout_hour = fields.Float('LAYOUT Block', group_operator='sum')
    internal_plaster_hour = fields.Float('INTERNAL PLASTER', group_operator='sum')
    external_plaster_hour = fields.Float('EXTERNAL PLASTER', group_operator='sum')
    internal_angles_hour = fields.Float('INTERNAL ANGLES', group_operator='sum')
    external_angles_hour = fields.Float('EXTERNAL ANGLES', group_operator='sum')
    point_hour = fields.Float('POINT', group_operator='sum')
    point_s = fields.Float('POINT S', group_operator='sum')
    point_external = fields.Float('POINT External', group_operator='sum')
    floor_tiles = fields.Float('FLOOR TILES', group_operator='sum')
    parquet_tiles = fields.Float('PARQUET TILES', group_operator='sum')
    wall_tiles = fields.Float('WALL TILES', group_operator='sum')
    mosaic = fields.Float('MOSAIC', group_operator='sum')
    hreshold = fields.Float('HRESHOLD', group_operator='sum')
    layout_tiles = fields.Float('Layout tiles', group_operator='sum')
    skirting = fields.Float('SKIRTING', group_operator='sum')
    hours_m = fields.Float('Mason HOUR', group_operator='sum')
    hours_h = fields.Float('HELPER HOUR', group_operator='sum')
    hours_o = fields.Float('OPERATOR HOUR', group_operator='sum')
    rush_coat = fields.Float('Rush Coat',group_operator='sum')
    external_rush = fields.Float('External Rush',group_operator='sum')
    production_line = fields.Many2one('production.line')
    paid = fields.Selection([('unpaid','Unpaid'),('paid','Paid')])
    date = fields.Date('Date')
    total = fields.Float('Total')
    work_id = fields.Many2one('work.location','Work Location')

    def create_over_time(self):
        aac_sob_hour = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.aac_sob_hour')) or 1.7
        hollow_hour = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.hollow_hour')) or 1.7
        layout_hour = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.layout_hour')) or 1.7
        internal_plaster_hour = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.internal_plaster_hour')) or 1.7
        external_plaster_hour = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.external_plaster_hour')) or 1.7
        internal_angles_hour = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.internal_angles_hour')) or 1.7
        external_angles_hour = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.external_angles_hour')) or 1.7
        point_hour = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.point_hour')) or 1.7
        point_s = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.point_s')) or 1.7
        point_external = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.point_external')) or 1.7
        floor_tiles = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.floor_tiles')) or 1.7
        parquet_tiles = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.parquet_tiles')) or 1.7
        wall_tiles = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.wall_tiles')) or 1.7
        mosaic = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.mosaic')) or 1.7
        hreshold = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.hreshold')) or 1.7
        layout_tiles = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.layout_tiles')) or 1.7
        skirting = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.skirting')) or 1.7
        hours_m = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.hours_m')) or 1.7
        hours_h = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.hours_h')) or 1.7
        hours_o = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.hours_o')) or 1.7
        rush_coat = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.rush_coat')) or 1.7
        external_rush = float(self.env['ir.config_parameter'].sudo().get_param(
            'hr_edit.external_rush')) or 1.7
        



        # if fields.Date.today() == 5 :
        six_months_ago = fields.Date.today() - timedelta(days=3 * 30)
        previous_sundays = get_previous_sundays_until(six_months_ago,fields.Date.today())
        for day in range(1, fields.Date.today().day + 1):
            from datetime import date
            date = date(datetime.today().year,datetime.today().month, day)
            if date.weekday() == 6:
                previous_sundays.append(date)
        production_sunday = self.env['production.line'].sudo().search([
            ('absence', 'not in', ['1', '2']),
            ('state_paid', '=', False),
            
        ]).filtered(lambda l: l.leave =='' and l.start_date and l.start_date.weekday() == 6 and l.start_date < fields.Date.today() and not l.state_paid)
        over_time_list=[i for i in self.env['over.time'].sudo().search([('production_line','in',[i.id for i in production_sunday])])]
        over_list = [i.production_line for i in over_time_list]
        
        create_production = [x for x in production_sunday if x not in over_list] if len (over_list) > 0 else production_sunday
        
        for rec in over_time_list:
            prd=self.env['production.line'].sudo().search([('id','=',rec.production_line.id)])
            yes=0
            if self.env['production.line'].sudo().search([('employee_id','=',prd.employee_id.id),('absence', 'in', ['1', '2'])]).filtered(lambda l: l.leave =='' and l.start_date and l.start_date == prd.start_date+relativedelta(days=1)):
                yes+=1
                
            rec.sudo().write({
                'employee_id': rec.employee_id.id,
                'job_code': rec.job_code.id,
                'designation': rec.employee_id.job_id.id,
                'aac_sob_hour': prd.aac_sob_hour * aac_sob_hour if yes == 0 else prd.aac_sob_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).acc_block,
                'hollow_hour': prd.hollow_hour * hollow_hour if yes == 0 else prd.hollow_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).hollow_block,
                'layout_hour': prd.layout_hour * layout_hour if yes == 0 else prd.layout_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).layout_block,
                'internal_plaster_hour': prd.internal_plaster_hour * internal_plaster_hour if yes == 0 else prd.internal_plaster_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).internal_plaster,
                'external_plaster_hour': prd.external_plaster_hour * external_plaster_hour if yes == 0 else prd.external_plaster_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).external_plaster,
                'internal_angles_hour': prd.internal_angles_hour * internal_angles_hour if yes == 0 else prd.internal_angles_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).internal_angles,
                'external_angles_hour': prd.external_angles_hour * external_angles_hour if yes == 0 else prd.external_angles_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).external_angles,
                'point_hour': prd.point_hour * point_hour if yes == 0 else prd.point_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).point_hour,
                'point_s': prd.point_s * point_s if yes == 0  else prd.point_s * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).point_s,
                'point_external': prd.point_external * point_external if yes == 0  else prd.point_external * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).point_external,
                'floor_tiles': prd.floor_tiles * floor_tiles if yes == 0  else prd.floor_tiles  * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).floor_tiles,
                'parquet_tiles': prd.parquet_tiles * parquet_tiles if yes == 0  else prd.parquet_tiles * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).parquet_tiles,
                'wall_tiles': prd.wall_tiles * wall_tiles if yes == 0  else prd.wall_tiles * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).wall_tiles,
                'mosaic': prd.mosaic * mosaic if yes == 0 else prd.mosaic * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).mosaic,
                'hreshold': prd.hreshold * hreshold if yes == 0  else prd.hreshold * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).threshold,
                'layout_tiles': prd.layout_tiles * layout_tiles if yes == 0 else prd.layout_tiles * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).layout_tiles,
                'skirting': prd.skirting * skirting if yes == 0 else prd.skirting  * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).skirting,
                # 'hours_m': prd.hours_m * hours_m if rec.absence_next_day == 'no' else rec.hours_m,
                # 'hours_h': rec.hours_h * hours_h if rec.absence_next_day == 'no' else rec.hours_h,
                # 'hours_o': rec.hours_o * hours_o if rec.absence_next_day == 'no' else rec.hours_o,
                'rush_coat': prd.rush_coat * rush_coat if yes == 0  else prd.rush_coat * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).rush_coat,
                'external_rush': prd.external_rush * external_rush if yes == 0  else prd.external_rush * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).external_rush,
                'work_id':rec.work_id.id,
                'absence_next_day':'yes' if yes != 0 else 'no',
            })
            if rec.employee_id.job_id.id in [self.env.ref('hr_edit.helper').id,self.env.ref('hr_edit.tile_h').id,self.env.ref('hr_edit.rush').id]:
                rec.hours_h = prd.hours * hours_h if yes == 0  else prd.hours * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).hourly_wage
            elif rec.employee_id.job_id.id in [self.env.ref('hr_edit.block').id,self.env.ref('hr_edit.plaster').id,self.env.ref('hr_edit.tile_m').id,self.env.ref('hr_edit.prep').id]:
                rec.hours_m = prd.hours * hours_m if yes == 0  else prd.hours  * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).hourly_wage
            elif rec.employee_id.job_id.id == self.env.ref('hr_edit.operation').id:
                rec.hours_o = prd.hours * hours_o if yes == 0 else prd.hours  * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).hourly_wage
           
            rec.total=rec.aac_sob_hour + rec.hollow_hour +rec.layout_hour+rec.internal_plaster_hour+rec.external_plaster_hour+rec.internal_angles_hour+rec.external_angles_hour+rec.point_hour+rec.point_s+rec.point_external+rec.floor_tiles+rec.parquet_tiles+rec.wall_tiles+rec.mosaic+rec.hreshold+rec.layout_tiles+rec.skirting+rec.hours_m+rec.hours_h+rec.hours_o+rec.rush_coat+rec.external_rush
        for rec in create_production:
            yes=0
            if self.env['production.line'].sudo().search([('employee_id','=',rec.employee_id.id),('absence', 'in', ['1', '2'])]).filtered(lambda l: l.leave =='' and l.start_date and l.start_date == rec.start_date+relativedelta(days=1)):
                yes+=1
            new=self.env['over.time'].sudo().create({
                'production_line':rec.id,
                'date':rec.start_date,
                'absence_next_day':'yes' if yes != 0 else 'no',
                'employee_id':rec.employee_id.id,
                'job_code':rec.job_code.id,
                'designation':rec.employee_id.job_id.id,
                'aac_sob_hour':rec.aac_sob_hour * aac_sob_hour if yes == 0 else rec.aac_sob_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).acc_block,
                'hollow_hour':rec.hollow_hour * hollow_hour if yes == 0 else rec.hollow_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).hollow_block,
                'layout_hour':rec.layout_hour * layout_hour if yes == 0 else rec.layout_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).layout_block,
                'internal_plaster_hour':rec.internal_plaster_hour * internal_plaster_hour if yes == 0 else rec.internal_plaster_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).internal_plaster,
                'external_plaster_hour':rec.external_plaster_hour * external_plaster_hour if yes == 0 else rec.external_plaster_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).external_plaster,
                'internal_angles_hour':rec.internal_angles_hour * internal_angles_hour if yes == 0 else rec.internal_angles_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).internal_angles,
                'external_angles_hour':rec.external_angles_hour * external_angles_hour if yes == 0 else rec.external_angles_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).external_angles,
                'point_hour':rec.point_hour * point_hour if yes == 0 else rec.point_hour * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).point_hour,
                'point_s':rec.point_s * point_s if yes == 0 else rec.point_s * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).point_s,
                'point_external':rec.point_external * point_external if yes == 0 else rec.point_external * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).point_external,
                'floor_tiles':rec.floor_tiles * floor_tiles if yes == 0 else rec.floor_tiles  * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).floor_tiles,
                'parquet_tiles':rec.parquet_tiles * parquet_tiles if yes == 0 else rec.parquet_tiles * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).parquet_tiles,
                'wall_tiles':rec.wall_tiles * wall_tiles if yes == 0 else rec.wall_tiles * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).wall_tiles,
                'mosaic':rec.mosaic * mosaic if yes == 0 else rec.mosaic  * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).mosaic,
                'hreshold':rec.hreshold * hreshold if yes == 0 else rec.hreshold * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).threshold,
                'layout_tiles':rec.layout_tiles * layout_tiles if yes == 0 else rec.layout_tiles * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).layout_tiles,
                'skirting':rec.skirting * skirting if yes == 0 else rec.skirting  * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).skirting,
                # 'hours_m':rec.hours * hours_m if yes != 0 else rec.hours,
                # 'hours_h':rec.hours * hours_h if yes != 0 else rec.hours,
                # 'hours_o':rec.hours * hours_o if yes != 0 else rec.hours,
                'rush_coat':rec.rush_coat * rush_coat if yes == 0 else rec.rush_coat * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).rush_coat,
                'external_rush':rec.external_rush * external_rush if yes == 0 else rec.external_rush * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).external_rush,
                'work_id':rec.work_location_id.id
            })
            if new.employee_id.job_id.id in [self.env.ref('hr_edit.helper').id,self.env.ref('hr_edit.tile_h').id,self.env.ref('hr_edit.rush').id]:
                new.hours_h = rec.hours * hours_h if yes == 0 else rec.hours * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).hourly_wage
            elif new.employee_id.job_id.id in [self.env.ref('hr_edit.block').id,self.env.ref('hr_edit.plaster').id,self.env.ref('hr_edit.tile_m').id,self.env.ref('hr_edit.prep').id]:
                new.hours_m = rec.hours * hours_m if yes == 0 else rec.hours * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).hourly_wage
            elif new.employee_id.job_id.id == self.env.ref('hr_edit.operation').id:
                new.hours_o = rec.hours * hours_o if yes == 0 else rec.hours * rec.employee_id.contract_ids.filtered(lambda l: l.state not in ['draft', 'cancel']).hourly_wage
            new.total=new.aac_sob_hour + new.hollow_hour +new.layout_hour+new.internal_plaster_hour+new.external_plaster_hour+new.internal_angles_hour+new.external_angles_hour+new.point_hour+new.point_s+new.point_external+new.floor_tiles+new.parquet_tiles+new.wall_tiles+new.mosaic+new.hreshold+new.layout_tiles+new.skirting+new.hours_m+new.hours_h+new.hours_o+new.rush_coat+new.external_rush


    @api.onchange('paid')
    def change_state(self):
        for rec in self:
            if rec.paid =='paid':
                rec.production_line.state_paid = True
