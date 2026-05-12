from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestSaleOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context={**cls.env.context, "tracking_disable": True})
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Service", "type": "service", "list_price": 100.0}
        )

    def _create_order(self, **kwargs):
        vals = {
            "partner_id": self.partner.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_qty": 1,
                        "price_unit": 100.0,
                    },
                )
            ],
        }
        vals.update(kwargs)
        return self.env["sale.order"].create(vals)

    def _create_batch(self):
        return self.env["sale.order.batch"].create({})

    # --- _get_current_batch ---

    def test_get_current_batch_finds_open_batch(self):
        batch = self._create_batch()
        order = self._create_order()
        self.assertEqual(order._get_current_batch(), batch)

    def test_get_current_batch_ignores_closed_batch(self):
        batch = self._create_batch()
        batch.action_confirm()
        order = self._create_order()
        self.assertNotEqual(order._get_current_batch(), batch)

    # --- action_add_to_batch ---

    def test_action_add_to_batch_creates_new_batch(self):
        order = self._create_order()
        order.action_add_to_batch()
        self.assertTrue(order.batch_id)

    def test_action_add_to_batch_uses_existing_open_batch(self):
        batch = self._create_batch()
        order = self._create_order()
        order.action_add_to_batch()
        self.assertEqual(order.batch_id, batch)

    def test_action_add_to_batch_skips_already_batched_order(self):
        batch1 = self._create_batch()
        order = self._create_order(batch_id=batch1.id)
        order.action_add_to_batch()
        self.assertEqual(order.batch_id, batch1)

    def test_action_add_to_batch_skips_confirmed_order(self):
        order = self._create_order()
        order.with_context(bypass_batch=True).action_confirm()
        order.action_add_to_batch()
        self.assertFalse(order.batch_id)

    # --- action_view_sale_order_batch ---

    def test_action_view_sale_order_batch_returns_form_action(self):
        batch = self._create_batch()
        order = self._create_order(batch_id=batch.id)
        result = order.action_view_sale_order_batch()
        self.assertEqual(result["res_model"], "sale.order.batch")
        self.assertEqual(result["res_id"], batch.id)
        self.assertEqual(result["view_mode"], "form")

    # --- action_confirm ---

    def test_action_confirm_raises_user_error_when_in_batch(self):
        batch = self._create_batch()
        order = self._create_order(batch_id=batch.id)
        with self.assertRaises(UserError):
            order.action_confirm()

    def test_action_confirm_raises_for_multiple_batched_orders(self):
        batch = self._create_batch()
        order1 = self._create_order(batch_id=batch.id)
        order2 = self._create_order(batch_id=batch.id)
        with self.assertRaises(UserError):
            (order1 | order2).action_confirm()

    def test_action_confirm_works_with_bypass_batch_context(self):
        batch = self._create_batch()
        order = self._create_order(batch_id=batch.id)
        order.with_context(bypass_batch=True).action_confirm()
        self.assertEqual(order.state, "sale")

    def test_action_confirm_works_without_batch(self):
        order = self._create_order()
        order.action_confirm()
        self.assertEqual(order.state, "sale")

    # --- action_quotation_send ---

    def test_action_quotation_send_raises_user_error_when_in_batch(self):
        batch = self._create_batch()
        order = self._create_order(batch_id=batch.id)
        with self.assertRaises(UserError):
            order.action_quotation_send()

    def test_action_quotation_send_raises_for_multiple_batched_orders(self):
        batch = self._create_batch()
        order1 = self._create_order(batch_id=batch.id)
        order2 = self._create_order(batch_id=batch.id)
        with self.assertRaises(UserError):
            (order1 | order2).action_quotation_send()

    def test_action_quotation_send_works_with_bypass_batch_context(self):
        batch = self._create_batch()
        order = self._create_order(batch_id=batch.id)
        result = order.with_context(bypass_batch=True).action_quotation_send()
        self.assertIsNotNone(result)

    def test_action_quotation_send_works_without_batch(self):
        order = self._create_order()
        result = order.action_quotation_send()
        self.assertIsNotNone(result)

    # --- action_cancel ---

    def test_action_cancel_clears_batch_id(self):
        batch = self._create_batch()
        order = self._create_order(batch_id=batch.id)
        order.action_cancel()
        self.assertFalse(order.batch_id)

    # --- write ---

    def test_write_batch_id_updates_batch_products(self):
        batch = self._create_batch()
        order = self._create_order()
        self.assertFalse(order.order_line.batch_product_id)
        order.write({"batch_id": batch.id})
        self.assertTrue(order.order_line.batch_product_id)

    def test_write_without_batch_id_does_not_change_products(self):
        batch = self._create_batch()
        order = self._create_order(batch_id=batch.id)
        batch_product = order.order_line.batch_product_id
        order.write({"note": "test note"})
        self.assertEqual(order.order_line.batch_product_id, batch_product)
