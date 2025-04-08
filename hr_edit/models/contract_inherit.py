# -*- coding: utf-8 -*-
from odoo import api, _, fields, models, tools
import logging

_logger = logging.getLogger(__name__)


class ContractInherit(models.Model):
    _inherit = 'hr.contract'
    acc_block = fields.Monetary('AAC/SOB Block', tracking=True)
    hollow_block = fields.Monetary('Hollow block', tracking=True)
    layout_block = fields.Monetary('Layout block', tracking=True)
    internal_angles = fields.Monetary('Internal Angles', tracking=True)
    external_angles = fields.Monetary('External angles', tracking=True)
    internal_plaster = fields.Monetary('Internal Plaster', tracking=True)
    external_plaster = fields.Monetary('External Plaster', tracking=True)
    floor_tiles = fields.Monetary('Floor Tiles', tracking=True)
    parquet_tiles = fields.Monetary('Parquet Tiles', tracking=True)
    wall_tiles = fields.Monetary('Wall Tiles', tracking=True)
    mosaic = fields.Monetary('Mosaic', tracking=True)
    threshold = fields.Monetary('Threshold', tracking=True)
    layout_tiles = fields.Monetary('Layout tiles', tracking=True)
    skirting = fields.Monetary('Skirting', tracking=True)
    housing = fields.Monetary('Housing', tracking=True)
    point_s = fields.Monetary('POINT S', tracking=True)
    point_hour = fields.Monetary('POINT', tracking=True)
    point_external = fields.Monetary('POINT EXTERNAL', tracking=True)
    rush_coat = fields.Monetary(tracking=True)
    external_rush = fields.Monetary('External Rush',tracking=True)
    transportation = fields.Monetary('Transportation', tracking=True)
    other_allowances = fields.Monetary('Other Allowances', tracking=True)
    bonus = fields.Monetary('Bonus', tracking=True)
    testing_period = fields.Integer('Probation period',default=3)
    contract_salary = fields.Float('Contract salary')
    struct_id = fields.Many2one('hr.payroll.structure')
    domain_struct = fields.Binary(compute='_compute_domain_struct')
    @api.depends('date_start','structure_type_id')
    def _compute_domain_struct(self):
        for rec in self:
            if rec.structure_type_id:
                rec.domain_struct = rec.structure_type_id.struct_ids.ids
            else:
                rec.domain_struct = False

