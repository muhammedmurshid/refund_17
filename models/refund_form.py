from odoo import fields, models, api, _
import requests
from datetime import date, datetime
from odoo.exceptions import UserError
import requests


class StudentRefund(models.Model):
    _name = 'student.refund'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference_no'
    _description = "Refund"
    _order = 'id desc'

    student_name = fields.Char(string='Name', )
    reference_no = fields.Char(string="Sequence Number", required=True,
                               copy=False, default='New')
    batch = fields.Char(string='Batch')
    course = fields.Many2one('op.course', string='Course')
    email = fields.Char(string='Email')
    phone_number = fields.Char(string='Phone Number', widget='phone')
    reason = fields.Text(string='Student Reason')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    ded_ids = fields.One2many('refund.deduction', 'ded_id', string='Deduction')
    status = fields.Selection([
        ('accountant', 'Draft'),
        ('teacher', 'Teacher Approval'),
        ('head_assign', 'Academic Head Approval'),
        ('head', 'Head Approval'),
        ('manager', 'Marketing Manager Approval'),
        ('accounts', 'Approved'),
        ('reject', 'Rejected'),
        ('paid', 'Paid'),
    ], string='Status', default='accountant', tracking=True)
    assign_head = fields.Many2one('res.users', string='Assign head')
    branch = fields.Char('Branch')
    student_admission_no = fields.Char('Admission Number',)
    parent_number = fields.Char('Parent Number')
    # invoice_number = fields.Text('Invoice number')
    sat_class = fields.Integer(string='How many days he sat in the class')
    teacher_reason = fields.Text('Remarks for teacher')
    head_reason = fields.Text('Remarks of Academic Head')
    assign_to = fields.Many2one('hr.employee', string='Assign to')

    make_visible_teacher = fields.Boolean(string="User", default=True, compute='get_teacher')
    action_testing = fields.Float('Action')
    stream = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline'),
    ], string='Stream')
    attended_class = fields.Integer(string='Attended Class')
    total_class = fields.Integer(string='Total Class')
    session_completed = fields.Text(string='Session Completed')
    part_attended = fields.Text(string='Part Attended')
    admission_officer = fields.Char(string='Admission Officer')
    board_registration = fields.Selection([('completed', 'Completed'),
                                           ('not', 'Not')], string='Board registration')
    board_check = fields.Boolean()
    inv_ids = fields.One2many('refund.invoice.details', 'inv_id', string='Invoices')
    account_number = fields.Char(string='Account Number')
    account_holder_name = fields.Char(string='Account holder name')
    ifsc_code = fields.Char(string='IFSC Code')
    bank_name = fields.Char(string='Bank Name')
    student_id = fields.Many2one('op.student', string="Student")
    reject_reason = fields.Text(string="Reject Reason")
    reject_date = fields.Date(string="Reject Date")

    @api.depends('inv_ids.refund_amt')
    def _amount_all(self):
        total = 0
        for order in self.inv_ids:
            total += order.refund_amt
        self.update({
            'ref_total': total,

        })

    ref_total = fields.Float(string='Refund Requested', compute='_amount_all', store=True)

    refund_allowed_amt = fields.Float(string='Total Paid', readonly=False)

    def action_approve_selected(self):
        for rec in self:
            print(rec.student_name, 'rec name')
            rec.sudo().write({'status': 'manager'})

    @api.depends('ded_ids.amount')
    def _amount_deduction_all(self):
        """
        Compute the total amounts of the SO.
        """
        total_deduction = 0
        for order in self.ded_ids:
            total_deduction += order.amount
        self.update({
            'total_deduction': total_deduction,
        })

    total_deduction = fields.Float(string='Total Deduction', compute='_amount_deduction_all', store=True)

    def get_students(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Students',
            'view_mode': 'tree,form',
            'res_model': 'op.student',
            'domain': [('id', '=', self.student_id.id)],
            'context': "{'create': False}"
        }

    @api.depends('total_deduction', 'ref_total', 'refund_allowed_amt')
    def _amount_total_refund(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            total_deduction = order.refund_allowed_amt - order.total_deduction
        self.update({
            'total_all_refund': total_deduction
        })

    total_all_refund = fields.Float(string='Total Refund', compute='_amount_total_refund', store=True)

    @api.model
    def get_refund_dashboard(self):
        expense_state = {
            'draft': {
                'description': _('to report'),
                'amount': 0.0,
                'currency': self.env.company.currency_id.id,
            },
            'reported': {
                'description': _('under validation'),
                'amount': 0.0,
                'currency': self.env.company.currency_id.id,
            },
            'approved': {
                'description': _('to be reimbursed'),   
                'amount': 0.0,
                'currency': self.env.company.currency_id.id,
            }
        }
        if not self.env.user.employee_ids:
            return expense_state
        target_currency = self.env.company.currency_id
        expenses = self.sudo().read_group(
            [()], lazy=False)
        for expense in expenses:
            state = expense['state']
            currency = self.env['res.currency'].browse(expense['currency_id'][0]) if expense[
                'currency_id'] else target_currency
            amount = currency._convert(
                expense['total_all_refund'], target_currency, self.env.company, fields.Date.today())
            expense_state[state]['amount'] += amount
        return expense_state

    @api.depends('ref_total')
    def total_amount_refund(self):
        for rec in self:
            rec.amount = rec.ref_total

    amount = fields.Float(string='Amount', compute='total_amount_refund', store=True)

    def confirm_assign(self):
        return {'type': 'ir.actions.act_window',
                'name': _('Assign Form'),
                'res_model': 'assignment.wizard.refund',
                'target': 'new',
                'view_mode': 'form',
                'context': {'default_refund_id': self.id, }, }

    def act_add_refund_amount(self):
        refund = self.env['student.refund'].search([])
        for i in refund:
            if i.total_all_refund == 0:
                print(i.id, 'dhdf', i.total_all_refund)
                i.total_all_refund = i.refund_allowed_amt

    teacher_head_id = fields.Many2one('res.users', string='Teacher Head', compute='_compute_teacher_head_name',
                                      store=True, readonly=False)
    verified = fields.Boolean('Verified')

    @api.depends('assign_to')
    def _compute_teacher_head_name(self):
        for rec in self:
            rec.teacher_head_id = rec.assign_to.parent_id.user_id

    def confirm_assign_teacher(self):
        if not self.assign_to:
            raise UserError('Please assign a Teacher..')
        else:
            # self.status = 'teacher'
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', '=', self.env.user.id), (
                    'activity_type_id', '=', self.env.ref('refund_17.mail_activity_refund_alert_custome').id)])
            activity_id.action_feedback(feedback='Assigned')
            other_activity_ids = self.env['mail.activity'].search([('res_id', '=', self.id), (
                'activity_type_id', '=', self.env.ref('refund_17.mail_activity_refund_alert_custome').id)])
            other_activity_ids.unlink()

    @api.depends('make_visible_teacher')
    def get_teacher(self):
        print('kkkll')
        user_crnt = self.env.user.id

        res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
        if res_user.has_group('refund_17.group_refund_teacher'):
            self.make_visible_teacher = False

        else:
            self.make_visible_teacher = True

    make_visible_head = fields.Boolean(string="User", default=True, compute='get_head')

    def compute_count(self):
        for record in self:
            record.payment_count = self.env['refund.payment'].search_count(
                [('id_refund_record', '=', self.id)])

    payment_count = fields.Integer(compute='compute_count')

    def get_payments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payments',
            'view_mode': 'tree,form',
            'res_model': 'refund.payment',
            'domain': [('id_refund_record', '=', self.id)],
            'context': "{'create': False}"
        }

    @api.depends('make_visible_accountant')
    def get_accountant(self):
        print('kkkll')
        user_crnt = self.env.user.id
        res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
        if res_user.has_group('refund_17.group_refund_accounts'):
            self.make_visible_accountant = False
        else:
            self.make_visible_accountant = True

    make_visible_accountant = fields.Boolean(string="User", default=True, compute='get_accountant')

    @api.depends('make_visible_head')
    def get_head(self):
        print('kkkll')
        user_crnt = self.env.user.id
        res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
        if res_user.has_group('refund_17.group_refund_marketing_head'):
            self.make_visible_head = False
        else:
            self.make_visible_head = True

    @api.model
    def create(self, vals):
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'student.refund') or _('New')
        res = super(StudentRefund, self).create(vals)
        return res

    def teacher_approval(self):
        self.message_post(body="Teacher is approved")
        self.status = 'head_assign'
        activity_id = self.env['mail.activity'].search([('res_id', '=', self.id), ('user_id', '=', self.env.user.id), (
            'activity_type_id', '=', self.env.ref('refund_17.mail_activity_refund_alert_custome').id)])
        activity_id.action_feedback(feedback='Teacher Approved')
        self.activity_schedule('refund_17.mail_activity_refund_alert_custome', user_id=self.teacher_head_id.id,
                               note='Please approve the refund request.')
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Approved successfully.',
                'type': 'rainbow_man',
            }
        }

    def head_approval(self):
        self.status = 'manager'
        activity_id = self.env['mail.activity'].search(
            [('res_id', '=', self.id), ('user_id', '=', self.env.user.id), (
                'activity_type_id', '=', self.env.ref('refund_17.mail_activity_refund_alert_custome').id)])
        activity_id.action_feedback(feedback='Head Approved')
        users = self.env.ref('refund_17.refund_manager').users
        for j in users:
            self.activity_schedule('refund_17.mail_activity_refund_alert_custome', user_id=j.id,
                                   note='Please approve the refund request.')
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Approved successfully.',
                'type': 'rainbow_man',
            }
        }
    def manager_approval(self):
        # self.message_post(body="Marketing Manager is approved")
        self.env['refund.payment'].create({
            'name': self.student_name,
            'amount': self.total_all_refund,
            'batch': self.batch,
            'course': self.course.id,
            'id_refund_record': self.id,
            'account_number': self.account_number,
            'bank_name': self.bank_name,
            'ifsc_code': self.ifsc_code,
            'account_holder_name': self.account_holder_name,
            'total_refund': self.total_all_refund,
            'student_id': self.student_id.id,
            'student_admission_no': self.student_id.gr_no
            # 'invoice_number': self.invoice_number,
            # 'invoice_date': self.invoice_date,

        }
        )
        self.status = 'accounts'
        manager_users = self.env.ref('refund_17.refund_manager').users
        for manager in manager_users:
            activity_id = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('user_id', '=', manager.id), (
                    'activity_type_id', '=', self.env.ref('refund_17.mail_activity_refund_alert_custome').id)])
            activity_id.action_feedback(feedback='Manager Approved')

        users = self.env.ref('refund_17.group_refund_accounts').users
        print(users, 'user')
        for j in users:
            self.activity_schedule('refund_17.mail_activity_refund_alert_custome', user_id=j.id,
                                   note='Please approve the refund request.')
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Approved successfully.',
                'type': 'rainbow_man',
            }
        }

    @api.onchange('student_id')
    def _onchange_student_admission_officer(self):
        for i in self:
            if i.student_id:
                i.admission_officer = i.student_id.admission_officer_id.name

    # def remove_activity_for_manager(self):
    #     print('erwyuqqwqwi')
        # if self.status != 'manager':
        #     users = self.env.ref('Refund.refund_manager').users
        #     for i in users:
        #         activity_id = self.env['mail.activity'].search([('user_id', '=', i.id), (
        #             'activity_type_id', '=', self.env.ref('Refund.mail_activity_refund_alert_custome').id)])
        #         activity_id.unlink()

    def remove_activity_for_accounts(self):
        refund_record = self.env['student.refund'].search([])
        users = self.env.ref('refund_17.group_refund_accounts').users
        for i in users:
            # print(i.name, 'lll')
            for record in refund_record:
                if record.status != 'accounts':
                    activity_id = record.env['mail.activity'].search(
                        [('res_id', '=', record.id), ('user_id', '=', i.id), (
                            'activity_type_id', '=', self.env.ref('refund_17.mail_activity_refund_alert_custome').id)])
                    activity_id.unlink()

    def rejected(self):
        return {'type': 'ir.actions.act_window',
                'name': _('Reject Reason'),
                'res_model': 'refund.reject.reason',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_refund_id': self.id}, }


    def student_count(self):
        for record in self:
            record.refund_student_count = self.env['op.student'].search_count(
                [('id', '=', self.student_id.id)])

    refund_student_count = fields.Integer(compute='student_count')

    def paid_payments(self):

        self.status = 'paid'
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Paid successfully.',
                'type': 'rainbow_man',
            }
        }

    def teacher_refund_activity(self):
        print('hhhi')
        ss = self.env['student.refund'].search([])
        for i in ss:
            if i.status == 'teacher':
                users = ss.env.ref('refund_17.group_refund_teacher').users
                activity_type = i.env.ref('refund_17.mail_activity_refund_alert_custome')
                i.activity_schedule('refund_17.mail_activity_refund_alert_custome', user_id=i.assign_to.id,
                                    note=f'Please Approve {i.assign_to.name}')

    def head_refund_activity(self):
        print('hhhi')
        ss = self.env['student.refund'].search([])
        for i in ss:
            if i.status == 'head':
                users = ss.env.ref('refund_17.group_refund_marketing_head').users
                for j in users:
                    activity_type = i.env.ref('refund_17.mail_activity_refund_alert_custome')
                    i.activity_schedule('refund_17.mail_activity_refund_alert_custome', user_id=j.id,
                                        note=f'Please Approve {j.name}')

    def accounts_request_refund_activity(self):
        print('hhhi')
        ss = self.env['student.refund'].search([])
        for i in ss:
            # Check if the refund status is 'accountant'
            if i.status == 'accountant':
                # Get the accountant group users
                accountant_group = self.env.ref('refund_17.group_refund_accounts')
                users = accountant_group.users

                # Select only the first user (or you can choose based on specific criteria)
                if users:
                    # Get the first user in the group
                    selected_user = users[0]

                    # Get the custom activity type
                    activity_type = self.env.ref('refund_17.mail_activity_refund_alert_custome')

                    # Schedule the activity for the selected user
                    i.activity_schedule(
                        activity_type.id,  # Pass the activity type id
                        user_id=selected_user.id,  # Pass the selected accountant's user ID
                        note='Received a new Refund request form'
                    )

    def marketing_refund_activity(self):
        print('hhhi')
        ss = self.env['student.refund'].search([])
        for i in ss:
            if i.status == 'manager':
                users = ss.env.ref('refund_17.refund_manager').users
                for j in users:
                    activity_type = i.env.ref('refund_17.mail_activity_refund_alert_custome')
                    i.activity_schedule('refund_17.mail_activity_refund_alert_custome', user_id=j.id,
                                        note=f'Please Approve {j.name}')


class PaymentDetails(models.Model):
    _name = 'payment.details'
    _inherit = 'mail.thread'

    refund_amount = fields.Float(string='Refund amount')
    refund_date = fields.Date(string='Refund date')
    transaction_id = fields.Integer(string='Transaction id')


class RefundInvoiceDetails(models.Model):
    _name = 'refund.invoice.details'
    _inherit = 'mail.thread'

    invoice_number = fields.Char(string='Invoice Number')
    invoice_date = fields.Date(string='Invoice Date')
    refund_amt = fields.Integer(string='Refund Amount')
    inv_id = fields.Many2one('student.refund', string='Invoice', ondelete='cascade')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)


class RefundDeduction(models.Model):
    _name = 'refund.deduction'
    _inherit = 'mail.thread'

    item = fields.Char(string='Name')
    amount = fields.Float(string='Amount')
    ded_id = fields.Many2one('student.refund', string='Deduction', ondelete='cascade')
