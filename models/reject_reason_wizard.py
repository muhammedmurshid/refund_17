from odoo import fields,models,api,_
from datetime import date, datetime, timedelta


class WhatsappSendMessage(models.TransientModel):
   """This model is used for sending WhatsApp messages through Odoo."""
   _name = 'refund.reject.reason'
   _description = "Refund Rejection"

   refund_id = fields.Many2one('student.refund', string="Refund")
   reason = fields.Text(string="Reason", required=True)

   def action_reject(self):
       print('hi')
       self.refund_id.status = 'reject'
       self.refund_id.reject_date = date.today()
       self.refund_id.reject_reason = self.reason
       activity_id = self.env['mail.activity'].search([('res_id', '=', self.refund_id.id), ('user_id', '=', self.env.user.id), (
          'activity_type_id', '=', self.env.ref('refund_17.mail_activity_refund_alert_custome').id)])
       activity_id.action_feedback(feedback=f'Rejected {self.env.user.name}')
       other_activity_ids = self.env['mail.activity'].search([('res_id', '=', self.refund_id.id), (
          'activity_type_id', '=', self.env.ref('refund_17.mail_activity_refund_alert_custome').id)])
       other_activity_ids.unlink()
