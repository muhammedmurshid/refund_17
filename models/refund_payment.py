from odoo import models, fields, api
from odoo.exceptions import UserError


class RefundPayment(models.Model):
    _name = 'refund.payment'
    _inherit = 'mail.thread'
    _description = 'Refund Payment'

    name = fields.Char(string='Name', readonly=True)
    amount = fields.Float(string='Total Refund', readonly=True)
    batch = fields.Char(string='Batch', readonly=True)
    course = fields.Many2one('op.course', string='Course', readonly=True)
    id_refund_record = fields.Integer(string='Refund Record id')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    status = fields.Selection([
        ('in_payment', 'Draft'),
        ('cancel', 'Cancel'),
        ('paid', 'Paid'),
        ('reverted', 'Reverted'),
    ], string='Status', default='in_payment')
    transaction_id = fields.Char(string='Transaction Id')
    student_admission_no = fields.Char('Admission Number', readonly=True)
    # invoice_number = fields.Char('Invoice number', readonly=True)
    # invoice_date = fields.Date('Invoice date', readonly=True)
    date_of_refund = fields.Date('Refund Date')
    refund_amount = fields.Float('Amount Refunded', help="Please enter the refund amount here: ")
    account_number = fields.Char(string='Account Number')
    account_holder_name = fields.Char(string='Account holder name')
    ifsc_code = fields.Char(string='IFSC Code')
    bank_name = fields.Char(string='Bank Name')

    def action_return_to_draft(self):
        self.status = 'draft'

    def action_return_to_teacher(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reason',
            'res_model': 'student.refund.reverted.records',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_user': 'teacher'}
        }

    def action_return_to_head(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reason',
            'res_model': 'student.refund.reverted.records',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_user': 'head_assign'}
        }

    def action_return_to_manager(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reason',
            'res_model': 'student.refund.reverted.records',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_user': 'manager'}
        }

    total_refund = fields.Float('Total Amount')

    def paid(self):
        ss = self.env['student.refund'].search([('id', '=', self.id_refund_record)])
        print(ss, 'sssssss')
        self.env['op.credit.notes'].sudo().create({
            'date': fields.Datetime.now(), 'admission_no': ss.student_id.gr_no, 'fee_type': 'Credit Note',
            'batch_id': ss.student_id.batch_id.id, 'amount': self.total_refund, 'student_id': ss.student_id.id,
            'refund_id': self.id_refund_record,
            'refund_given_by': self.env.user.id
        })
        voucher_no = self.env['op.credit.notes'].sudo().search([('student_id', '=', ss.student_id.id)], limit=1,
                                                               order='id desc')
        ss.status = 'paid'
        sl_no = len(ss.student_id.payment_ids)
        ss.student_id.sudo().write({
            'payment_ids': [(0, 0, {'date': fields.Datetime.now(), 'payment_mode': 'Credit Note',
                                    'voucher_name': 'Credit Note', 'sl_no': sl_no + 1,
                                    'debit_amount': self.total_refund, 'voucher_no': voucher_no.voucher_no,
                                    'type': 'credit_note', 'batch_name': ss.student_id.batch_id.name,
                                    'course_name': ss.student_id.course_id.name, 'fee_name': 'Credit Note'})]
        })

        # for i in ss:
        #     if self.name == i.student_name and self.student_admission_no == i.student_admission_no and self.id_refund_record == i.id:
        #         i.status = 'paid'

        self.status = 'paid'
        activity_id = self.env['mail.activity'].search(
            [('res_id', '=', self.id_refund_record), ('user_id', '=', self.env.user.id), (
                'activity_type_id', '=', self.env.ref('refund_17.mail_activity_refund_alert_custome').id)])
        activity_id.action_feedback(feedback=f'Refund request is paid.')
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Paid successfully.',
                'type': 'rainbow_man',
            }
        }

    def cancel(self):
        self.status = 'cancel'

    def compute_count(self):
        for record in self:
            record.form_count = self.env['student.refund'].search_count(
                [('id', '=', self.id_refund_record)])

    form_count = fields.Integer(compute='compute_count')

    def get_payments_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Refund',
            'view_mode': 'tree,form',
            'res_model': 'student.refund',
            'domain': [('id', '=', self.id_refund_record)],
            'context': "{'create': False}"
        }


class StudentRefundRevertedRecords(models.TransientModel):
    _name = 'student.refund.reverted.records'

    reason_for_reverting = fields.Text(string='Reason')
    user = fields.Selection([('teacher', 'Teacher'), ('head_assign', 'Academic Head'), ('manager', 'Manager')],
                            string='User')

    def action_done_teacher(self):
        refund_payment = self.env['refund.payment'].search([('id', '=', self.env.context.get('active_id'))])
        if refund_payment:
            refund_record = self.env['student.refund'].search([('id', '=', refund_payment.id_refund_record)])
            refund_record.status = 'teacher'
            refund_payment.status = 'reverted'
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', refund_payment.id_refund_record), ('user_id', '=', refund_payment.env.user.id), (
                    'activity_type_id', '=', self.env.ref('refund_17.mail_activity_refund_alert_custome').id)])
            activity_id.action_feedback(feedback=f'Refund request is rejected.')
            refund_record.activity_schedule('refund_17.mail_activity_refund_alert_custome',
                                            user_id=refund_record.assign_to.user_id.id,
                                            note=f'This record is rejected due to: {self.reason_for_reverting}')

    def action_done_academic_head(self):
        refund_payment = self.env['refund.payment'].search([('id', '=', self.env.context.get('active_id'))])
        if refund_payment:
            refund_record = self.env['student.refund'].search([('id', '=', refund_payment.id_refund_record)])
            refund_record.status = 'head_assign'
            refund_payment.status = 'reverted'
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', refund_payment.id_refund_record), ('user_id', '=', refund_payment.env.user.id), (
                    'activity_type_id', '=', self.env.ref('refund_17.mail_activity_refund_alert_custome').id)])
            activity_id.action_feedback(feedback=f'Refund request is rejected.')
            refund_record.activity_schedule('refund_17.mail_activity_refund_alert_custome',
                                            user_id=refund_record.assign_to.parent_id.user_id.id,
                                            note=f'This record is rejected due to: {self.reason_for_reverting}')

    def action_done_manager(self):
        refund_payment = self.env['refund.payment'].search([('id', '=', self.env.context.get('active_id'))])
        if refund_payment:

            refund_record = self.env['student.refund'].search([('id', '=', refund_payment.id_refund_record)])
            refund_record.status = 'manager'
            refund_payment.status = 'reverted'

            users = self.env.ref('refund_17.refund_manager').users
            for i in users:
                print(i.name, 'users')
                activity_id = self.env['mail.activity'].search(
                    [('res_id', '=', refund_payment.id_refund_record), ('user_id', '=', i.id), (
                        'activity_type_id', '=', self.env.ref('refund_17.mail_activity_refund_alert_custome').id)])
                activity_id.action_feedback(feedback=f'Refund request is rejected.')
                refund_record.activity_schedule('refund_17.mail_activity_refund_alert_custome',
                                                user_id=i.id,
                                                note=f'This record is rejected due to: {self.reason_for_reverting}')

    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)

    @api.model
    def get_refund_dashboard(self):
        expense_state = {
            'draft': {
                'description': _('to report'),
                'amount': 0.0,
                'currency': self.env.company.currency_id.id,
            },
            # 'reported': {
            #     'description': _('under validation'),
            #     'amount': 0.0,
            #     'currency': self.env.company.currency_id.id,
            # },
            # 'approved': {
            #     'description': _('to be reimbursed'),
            #     'amount': 0.0,
            #     'currency': self.env.company.currency_id.id,
            # }
        }
        if not self.env.user.employee_ids:
            return expense_state
        target_currency = self.env.company.currency_id
        expenses = self.read_group(
            [
                ('employee_id', 'in', self.env.user.employee_ids.ids),
                ('payment_mode', '=', 'own_account'),
                ('state', 'in', ['draft', 'cancel', 'paid'])
            ], ['total_refund', 'currency_id', 'status'], ['status', 'currency_id'], lazy=False)
        for expense in expenses:
            state = expense['state']
            currency = self.env['res.currency'].browse(expense['currency_id'][0]) if expense[
                'currency_id'] else target_currency
            amount = currency._convert(
                expense['total_refund'], target_currency, self.env.company, fields.Date.today())
            expense_state[state]['amount'] += amount
        return expense_state
