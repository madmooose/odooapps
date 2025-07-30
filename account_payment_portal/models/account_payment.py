from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    payment_count = fields.Integer(compute="_compute_count_payment")

    @api.depends("partner_id")
    def _compute_count_payment(self):
        for payment in self:
            payment.payment_count = self.env["account.payment"].search_count(
                [("partner_id", "=", payment.partner_id.id)]
            )
