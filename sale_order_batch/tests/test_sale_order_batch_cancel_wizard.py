from odoo.tests import TransactionCase


class TestSaleOrderBatchCancelWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context={**cls.env.context, "tracking_disable": True})
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "service"}
        )

    def _create_batch_with_order(self):
        batch = self.env["sale.order.batch"].create({})
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "batch_id": batch.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        return batch, order

    def _create_wizard(self, batch):
        return (
            self.env["sale.order.batch.cancel.wizard"]
            .with_context(active_ids=[batch.id])
            .create({"batch_ids": [(4, batch.id)]})
        )

    # --- _compute_order_ids ---

    def test_compute_order_ids(self):
        batch, order = self._create_batch_with_order()
        wizard = self._create_wizard(batch)
        self.assertIn(order, wizard.order_ids)

    def test_compute_order_ids_multiple_batches(self):
        batch1, order1 = self._create_batch_with_order()
        batch2, order2 = self._create_batch_with_order()
        wizard = (
            self.env["sale.order.batch.cancel.wizard"]
            .with_context(active_ids=[batch1.id, batch2.id])
            .create({"batch_ids": [(4, batch1.id), (4, batch2.id)]})
        )
        self.assertIn(order1, wizard.order_ids)
        self.assertIn(order2, wizard.order_ids)

    # --- action_cancel ---

    def test_action_cancel_sets_batch_state_cancel(self):
        batch, order = self._create_batch_with_order()
        wizard = self._create_wizard(batch)
        wizard.action_cancel()
        self.assertEqual(batch.state, "cancel")

    def test_action_cancel_cancels_orders(self):
        batch, order = self._create_batch_with_order()
        wizard = self._create_wizard(batch)
        wizard.action_cancel()
        self.assertEqual(order.state, "cancel")

    def test_action_cancel_returns_window_close(self):
        batch, order = self._create_batch_with_order()
        wizard = self._create_wizard(batch)
        result = wizard.action_cancel()
        self.assertEqual(result["type"], "ir.actions.act_window_close")

    # --- action_discard ---

    def test_action_discard_returns_window_close(self):
        batch, order = self._create_batch_with_order()
        wizard = self._create_wizard(batch)
        result = wizard.action_discard()
        self.assertEqual(result["type"], "ir.actions.act_window_close")
