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
        employee_attachments = {}
        for rec in self:
        name = f"{rec.job_code.code}_{rec.employee_ref_id.name}" if rec.job_code and rec.employee_ref_id else (
        rec.job_code.code if rec.job_code else (
        rec.employee_ref_id.name if rec.employee_ref_id else ''))
        employee_attachments[name] = rec.doc_attachment_ids
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for emp_name, attachments in employee_attachments.items():
                for attach in attachments:
                    file_content = base64.b64decode(attach.datas or b'')
                    original_name = attach.name or 'file.bin'
                    # Extract extension
                    _, ext = os.path.splitext(original_name)
                    ext = ext or '.bin'
                    # Clean employee name for filenames (remove slashes, etc.)
                    safe_emp_name = emp_name.replace('/', '_').replace('\\', '_').strip()
                    filename = f"{safe_emp_name}_{attach.name}"
                    # Write to zip
                    zip_file.writestr(filename, file_content)
        # Prepare the file
        zip_buffer.seek(0)
        zip_attachment = self.env['ir.attachment'].create({
            'name': "attachments_by_employee.zip",
            'type': 'binary',
            'datas': base64.b64encode(zip_buffer.read()),
            'res_model': self._name,
            'res_id': self[0].id,
            'mimetype': 'application/zip',
        })
    


class BankInherit(models.Model):
    _inherit = "res.partner.bank"
    iban = fields.Char('IBAN')
    routing_no = fields.Char('Routing No')
