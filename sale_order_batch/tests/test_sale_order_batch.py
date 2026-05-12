from odoo.tests import TransactionCase


class TestSaleOrderBatch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context={**cls.env.context, "tracking_disable": True})
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Service Product",
                "type": "service",
                "list_price": 100.0,
                "invoice_policy": "order",
            }
        )
        cls.product2 = cls.env["product.product"].create(
            {
                "name": "Test Service Product 2",
                "type": "service",
                "list_price": 200.0,
                "invoice_policy": "order",
            }
        )

    def _create_batch(self, **kwargs):
        return self.env["sale.order.batch"].create(kwargs)

    def _create_order(self, batch=None, product=None, qty=1, price=100.0):
        if product is None:
            product = self.product
        vals = {
            "partner_id": self.partner.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_uom_qty": qty,
                        "price_unit": price,
                    },
                )
            ],
        }
        if batch:
            vals["batch_id"] = batch.id
        return self.env["sale.order"].create(vals)

    def test_create_generates_sequence_name(self):
        batch = self._create_batch()
        self.assertTrue(batch.name.startswith("SOB"))
        self.assertNotEqual(batch.name, "New")

    def test_create_keeps_explicit_name(self):
        batch = self.env["sale.order.batch"].create({"name": "MY-BATCH-001"})
        self.assertEqual(batch.name, "MY-BATCH-001")

    def test_compute_sale_order_count_with_orders(self):
        batch = self._create_batch()
        self._create_order(batch=batch)
        self._create_order(batch=batch)
        self.assertEqual(batch.sale_order_count, 2)

    def test_compute_amount_total(self):
        batch = self._create_batch()
        order1 = self._create_order(batch=batch, price=100.0)
        order2 = self._create_order(batch=batch, price=200.0)
        self.assertAlmostEqual(
            batch.amount_total, order1.amount_total + order2.amount_total
        )

    def test_compute_product_count_with_products(self):
        batch = self._create_batch()
        self._create_order(batch=batch, product=self.product)
        self._create_order(batch=batch, product=self.product2)
        self.assertEqual(batch.product_count, 2)

    def test_compute_invoice_ids_with_invoice(self):
        batch = self._create_batch()
        order = self._create_order(batch=batch)
        order.with_context(bypass_batch=True).action_confirm()
        invoice = order._create_invoices()
        self.assertIn(invoice, batch.invoice_ids)
        self.assertEqual(batch.invoice_count, 1)

    def test_compute_partner_credit_warning_no_warnings(self):
        batch = self._create_batch()
        self._create_order(batch=batch)
        self.assertEqual(batch.partner_credit_warning, "")

    # --- action_view_source_sale_orders ---

    def test_action_view_source_sale_orders_zero(self):
        batch = self._create_batch()
        result = batch.action_view_source_sale_orders()
        self.assertEqual(result["type"], "ir.actions.act_window_close")

    def test_action_view_source_sale_orders_one(self):
        batch = self._create_batch()
        order = self._create_order(batch=batch)
        result = batch.action_view_source_sale_orders()
        self.assertEqual(result["res_id"], order.id)
        self.assertIn("views", result)

    def test_action_view_source_sale_orders_multiple(self):
        batch = self._create_batch()
        self._create_order(batch=batch)
        self._create_order(batch=batch)
        result = batch.action_view_source_sale_orders()
        self.assertIn("domain", result)

    # --- action_view_products ---

    def test_action_view_products_zero(self):
        batch = self._create_batch()
        result = batch.action_view_products()
        self.assertEqual(result["type"], "ir.actions.act_window_close")

    def test_action_view_products_one(self):
        batch = self._create_batch()
        self._create_order(batch=batch)
        result = batch.action_view_products()
        self.assertIn("res_id", result)
        self.assertIn("views", result)
        self.assertEqual(result["res_id"], batch.product_ids.id)

    def test_action_view_products_multiple(self):
        batch = self._create_batch()
        self._create_order(batch=batch, product=self.product)
        self._create_order(batch=batch, product=self.product2)
        result = batch.action_view_products()
        self.assertIn("domain", result)

    # --- action_view_invoice ---

    def test_action_view_invoice_zero(self):
        batch = self._create_batch()
        result = batch.action_view_invoice()
        self.assertEqual(result["type"], "ir.actions.act_window_close")

    def test_action_view_invoice_one(self):
        batch = self._create_batch()
        order = self._create_order(batch=batch)
        order.with_context(bypass_batch=True).action_confirm()
        order._create_invoices()
        result = batch.action_view_invoice()
        self.assertIn("res_id", result)
        self.assertIn("views", result)

    def test_action_view_invoice_multiple(self):
        batch = self._create_batch()
        order1 = self._create_order(batch=batch)
        order2 = self._create_order(batch=batch)
        order1.with_context(bypass_batch=True).action_confirm()
        order2.with_context(bypass_batch=True).action_confirm()
        order1._create_invoices()
        order2._create_invoices()
        result = batch.action_view_invoice()
        self.assertIn("domain", result)

    # --- action_in_progress ---

    def test_action_in_progress_sets_state(self):
        batch = self._create_batch()
        self._create_order(batch=batch)
        batch.action_in_progress()
        self.assertEqual(batch.state, "in_progress")

    def test_action_in_progress_sends_quotation(self):
        batch = self._create_batch()
        order = self._create_order(batch=batch)
        batch.action_in_progress()
        self.assertEqual(order.state, "sent")

    # --- action_confirm ---

    def test_action_confirm_sets_batch_closed(self):
        batch = self._create_batch()
        self._create_order(batch=batch)
        batch.action_confirm()
        self.assertEqual(batch.state, "closed")

    def test_action_confirm_confirms_orders(self):
        batch = self._create_batch()
        order = self._create_order(batch=batch)
        batch.action_confirm()
        self.assertEqual(order.state, "sale")

    # --- action_open ---

    def test_action_open_resets_state(self):
        batch = self._create_batch()
        self._create_order(batch=batch)
        batch.action_in_progress()
        batch.action_open()
        self.assertEqual(batch.state, "open")

    def test_action_open_resets_orders_to_draft(self):
        batch = self._create_batch()
        order = self._create_order(batch=batch)
        batch.action_in_progress()
        batch.action_open()
        self.assertEqual(order.state, "draft")

    # --- _show_cancel_wizard ---

    def test_show_cancel_wizard_disabled_by_context(self):
        batch = self._create_batch()
        self._create_order(batch=batch)
        batch.action_in_progress()
        result = batch.with_context(disable_cancel_warning=True)._show_cancel_wizard()
        self.assertFalse(result)

    def test_show_cancel_wizard_no_orders(self):
        batch = self._create_batch()
        self.assertFalse(batch._show_cancel_wizard())

    def test_show_cancel_wizard_with_sent_orders(self):
        batch = self._create_batch()
        self._create_order(batch=batch)
        batch.action_in_progress()
        self.assertTrue(batch._show_cancel_wizard())

    # --- action_cancel ---

    def test_action_cancel_returns_wizard_for_sent_orders(self):
        batch = self._create_batch()
        self._create_order(batch=batch)
        batch.action_in_progress()
        result = batch.action_cancel()
        self.assertIsNotNone(result)
        self.assertEqual(result.get("res_model"), "sale.order.batch.cancel.wizard")

    def test_action_cancel_without_wizard_sets_cancel(self):
        batch = self._create_batch()
        self._create_order(batch=batch)
        batch.with_context(disable_cancel_warning=True).action_cancel()
        self.assertEqual(batch.state, "cancel")

    # --- _action_cancel ---

    def test_action_cancel_directly(self):
        batch = self._create_batch()
        order = self._create_order(batch=batch)
        batch._action_cancel()
        self.assertEqual(batch.state, "cancel")
        self.assertEqual(order.state, "cancel")
