from odoo import api, fields, tools, models, _
import logging

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    allocation_period = fields.Float(string="allocation period every month /Day",
                                     config_parameter='hr_edit.allocation_period',
                                     default=2.5, help="Number Days for annual Leave type")
    first_period_staff_foreman = fields.Float(string="first allocation for staff-foreman /Day",
                                              config_parameter='hr_edit.first_period_staff_foreman',
                                              default=45)
    complete_staff_foreman_period = fields.Float(string="first period for staff-foreman /Year",
                                                 config_parameter='hr_edit.complete_staff_foreman_period',
                                                 default=1.5)
    complete_labor_n_period = fields.Float(string="first period for Labor N /Year",
                                           config_parameter='hr_edit.complete_labor_n_period',
                                           default=2)
    first_period_labor_n = fields.Float(string="first allocation for staff-foreman /Day",
                                              config_parameter='hr_edit.first_period_labor_n',
                                              default=60)
    limit_number_of_day_staff_foreman = fields.Float(string="max /Days",
                                                     config_parameter='hr_edit.limit_number_of_day_staff_foreman',
                                                     default=30)
    allocation_max = fields.Float(string="max allocation /Days",
                                  config_parameter='hr_edit.allocation_max',
                                  default=60)
    lock_data_after = fields.Integer(config_parameter='hr_edit.lock_data_after', default=2)
    lock_pro_after = fields.Integer(config_parameter='hr_edit.lock_pro_after', default=7)
    two_day_ded_mason = fields.Integer(config_parameter='hr_edit.two_day_ded_mason', default=10)
    non_absence_bonus = fields.Integer(config_parameter='hr_edit.non_absence_bonus', default=100)
    operator_bonus = fields.Integer(config_parameter='hr_edit.operator_bonus', default=150)
    receive_some = fields.Integer(config_parameter='hr_edit.receive_some', default=100)
    receive_less = fields.Integer(config_parameter='hr_edit.receive_less', default=7)
    least1 = fields.Integer(config_parameter='hr_edit.least1', default=90)
    least2 = fields.Integer(config_parameter='hr_edit.least2', default=75)
    least3 = fields.Integer(config_parameter='hr_edit.least3', default=50)
    aac_sob_hour = fields.Float(config_parameter='hr_edit.aac_sob_hour', default=1.7)
    hollow_hour = fields.Float(config_parameter='hr_edit.hollow_hour', default=1.7)
    layout_hour = fields.Float(config_parameter='hr_edit.layout_hour', default=1.7)
    external_plaster_hour = fields.Float(config_parameter='hr_edit.external_plaster_hour', default=1.7)
    internal_angles_hour = fields.Float(config_parameter='hr_edit.internal_angles_hour', default=1.7)
    external_angles_hour = fields.Float(config_parameter='hr_edit.external_angles_hour', default=1.7)
    point_hour = fields.Float(config_parameter='hr_edit.point_hour', default=1.7)
    point_s = fields.Float(config_parameter='hr_edit.point_s', default=1.7)
    point_external = fields.Float(config_parameter='hr_edit.point_external', default=1.7)
    floor_tiles = fields.Float(config_parameter='hr_edit.floor_tiles', default=1.7)
    parquet_tiles = fields.Float(config_parameter='hr_edit.parquet_tiles', default=1.7)
    wall_tiles = fields.Float(config_parameter='hr_edit.wall_tiles', default=1.7)
    mosaic = fields.Float(config_parameter='hr_edit.mosaic', default=1.7)
    layout_tiles = fields.Float(config_parameter='hr_edit.layout_tiles', default=1.7)
    skirting = fields.Float(config_parameter='hr_edit.skirting', default=1.7)
    hours_m = fields.Float(config_parameter='hr_edit.hours_m', default=1.7)
    hours_h = fields.Float(config_parameter='hr_edit.hours_h', default=1.7)
    hours_o = fields.Float(config_parameter='hr_edit.hours_o', default=1.7)
    rush_coat = fields.Float(config_parameter='hr_edit.rush_coat', default=1.7)
    external_rush = fields.Float(config_parameter='hr_edit.external_rush', default=1.7)


