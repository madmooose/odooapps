from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAccountPaymentPortal(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create two partners
        portal_partner = self.env["res.partner"].create({"name": "Portal User"})
        other_partner = self.env["res.partner"].create({"name": "Other User"})

        # Create two users, one portal
        portal_group = self.env.ref("base.group_portal")
        portal_user = self.env["res.users"].create(
            {
                "name": "Portal User",
                "login": "portaluser@example.com",
                "partner_id": portal_partner.id,
                "groups_id": [(6, 0, [portal_group.id])],
            }
        )
        other_user = self.env["res.users"].create(
            {
                "name": "Other User",
                "login": "otheruser@example.com",
                "partner_id": other_partner.id,
            }
        )

        # Create two payments
        portal_partner_payment = self.env["account.payment"].create(
            {
                "partner_id": portal_partner.id,
                "amount": 100,
                "payment_type": "inbound",
                "state": "draft",
            }
        )
        other_partner_payment = self.env["account.payment"].create(
            {
                "partner_id": other_partner.id,
                "amount": 200,
                "payment_type": "inbound",
                "state": "draft",
            }
        )

        self.portal_user = portal_user
        self.other_user = other_user
        self.portal_partner_payment = portal_partner_payment
        self.other_partner_payment = other_partner_payment

    def test_portal_user_sees_only_own_payment(self):
        # Switch to portal user context
        payments = self.env["account.payment"].with_user(self.portal_user.id).search([])
        self.assertIn(self.portal_partner_payment, payments)
        self.assertNotIn(self.other_partner_payment, payments)
