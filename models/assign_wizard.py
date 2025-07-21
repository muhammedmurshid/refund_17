from odoo import fields,models,api,_

class AssignWizard(models.TransientModel):
    _name = 'assignment.wizard.refund'

    assign_to = fields.Many2one('hr.employee', string="Assign to Teacher", required=1)
    student_id = fields.Many2one('op.student', string="Student", required=1)
    admission_id = fields.Char(string="Admission ID", required=1)
    refund_id = fields.Many2one('student.refund', string="Refund")

    def act_confirm(self):
        print('jj')
        self.refund_id.assign_to = self.assign_to.id
        self.refund_id.status = 'teacher'
        self.refund_id.student_id = self.student_id.id
        # self.refund_id.activity_schedule('refund_17.mail_activity_refund_alert_custome', user_id=self.assign_to.user_id.id,
        #                        note='Please approve the refund request.')
        # activity_id = self.env['mail.activity'].search(
        #     [('res_id', '=', self.refund_id), ('user_id', '=', self.env.user.id), (
        #         'activity_type_id', '=', self.env.ref('refund_17.mail_activity_refund_alert_custome').id)])
        # if activity_id:
        #     activity_id.action_feedback(feedback='Assigned')
        # if self.refund_id.course.board_registration == True:
        #     self.refund_id.board_check = True
        # else:
        #     self.refund_id.board_check = False
        #
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Teacher Assigned',
                'type': 'rainbow_man',
            }
        }

    @api.onchange('student_id')
    def _onchange_student_id(self):
        if self.student_id:
            self.admission_id = self.student_id.gr_no