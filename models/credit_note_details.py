from odoo import fields,models,api,_

class CreditNoteDetails(models.Model):
    _inherit = 'op.student'

    credit_note_date = fields.Date(string="Date", help="credit note date")
    credit_note_amount = fields.Float(string="Amount", help="credit note amount")
    credit_note_reason = fields.Text(string="Reason", help="credit note reason")
