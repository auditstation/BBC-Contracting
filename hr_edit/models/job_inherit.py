# -*- coding: utf-8 -*-
from odoo import fields, models, api


class EmployeeInherit(models.Model):
    _inherit = 'hr.job'

    lock = fields.Boolean('Lock')


class DocumentInherit(models.Model):
    _inherit = 'hr.employee.document'

    job_code = fields.Many2one('job.codes', invisible=1,
                               copy=False,
                               help='Specify the job code.')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'employee_ref_id' in vals:
                vals['job_code'] = self.env['job.codes'].sudo().search([('employee_id', '=', vals['employee_ref_id'])]).id
            elif 'job_code' in vals: 
                vals['employee_ref_id'] = self.env['job.codes'].sudo().search([('id', '=', vals['job_code'])]).employee_id.id
        return super().create(vals_list)
    
    @api.onchange('employee_ref_id')
    def onchange_code(self):
        if self.employee_ref_id:
            self.job_code = self.env['job.codes'].sudo().search([('employee_id', '=', self.employee_ref_id.id)]).id

    @api.onchange('job_code')
    def onchange_employee(self):
        if self.job_code:
            self.employee_ref_id = self.env['job.codes'].sudo().search([('id', '=', self.job_code.id)]).employee_id.id

    def action_download_attachments_zip(self):
        attachments =[]
        for rec in self:
            for i in rec.doc_attachment_ids:
                attachments.append(i)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for attach in attachments:
                file_content = base64.b64decode(attach.datas)
                filename = attach.name or 'file.bin'
                zip_file.writestr(filename, file_content)

        zip_buffer.seek(0)
        # Create a download URL by uploading the zip to ir.attachment
        zip_attachment = self.env['ir.attachment'].create({
            'name': f"{'attachments'}.zip",
            'type': 'binary',
            'datas': base64.b64encode(zip_buffer.read()),
            'res_model': self._name,
            'res_id': self[0].id,
            'mimetype': 'application/zip',
        })
        # Use action to redirect to the file URL
        download_url = f"/web/content/{zip_attachment.id}?download=true"
        return {
            "type": "ir.actions.act_url",
            "url": download_url,
            "target": "self",
        }


class BankInherit(models.Model):
    _inherit = "res.partner.bank"
    iban = fields.Char('IBAN')
    routing_no = fields.Char('Routing No')
