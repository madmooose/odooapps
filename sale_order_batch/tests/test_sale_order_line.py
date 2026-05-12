from odoo.tests import TransactionCase


class TestSaleOrderLine(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context={**cls.env.context, "tracking_disable": True})
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Product A", "type": "service"}
        )
        cls.product2 = cls.env["product.product"].create(
            {"name": "Product B", "type": "service"}
        )

    def _create_batch(self):
        return self.env["sale.order.batch"].create({})

    def _create_order(self, batch=None, product=None, qty=1):
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
                        "price_unit": 10.0,
                    },
                )
            ],
        }
        if batch:
            vals["batch_id"] = batch.id
        return self.env["sale.order"].create(vals)

    # --- create ---

    def test_create_line_with_batch_links_batch_product(self):
        batch = self._create_batch()
        order = self._create_order(batch=batch)
        line = order.order_line
        self.assertTrue(line.batch_product_id)
        self.assertEqual(line.batch_product_id.product_id, self.product)
        self.assertEqual(line.batch_product_id.batch_id, batch)

    def test_create_line_without_batch_has_no_batch_product(self):
        order = self._create_order()
        self.assertFalse(order.order_line.batch_product_id)

    def test_create_two_lines_same_product_share_batch_product(self):
        batch = self._create_batch()
        order = self._create_order(batch=batch)
        line2 = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom_qty": 2,
                "price_unit": 10.0,
            }
        )
        self.assertEqual(order.order_line[0].batch_product_id, line2.batch_product_id)

    def test_create_two_lines_different_products_get_different_batch_products(self):
        batch = self._create_batch()
        order = self._create_order(batch=batch)
        line2 = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product2.id,
                "product_uom_qty": 1,
                "price_unit": 10.0,
            }
        )
        self.assertNotEqual(
            order.order_line[0].batch_product_id, line2.batch_product_id
        )
        self.assertEqual(batch.product_count, 2)

    # --- write ---

    def test_write_product_id_updates_batch_product(self):
        batch = self._create_batch()
        order = self._create_order(batch=batch)
        line = order.order_line
        old_batch_product = line.batch_product_id
        line.write({"product_id": self.product2.id})
        self.assertNotEqual(line.batch_product_id, old_batch_product)
        self.assertEqual(line.batch_product_id.product_id, self.product2)

    def test_write_without_product_id_keeps_batch_product(self):
        batch = self._create_batch()
        order = self._create_order(batch=batch)
        line = order.order_line
        batch_product = line.batch_product_id
        line.write({"product_uom_qty": 5})
        self.assertEqual(line.batch_product_id, batch_product)

    # --- unlink ---

    def test_unlink_last_line_removes_batch_product(self):
        batch = self._create_batch()
        order = self._create_order(batch=batch)
        line = order.order_line
        batch_product = line.batch_product_id
        line.unlink()
        self.assertFalse(batch_product.exists())

    def test_unlink_line_keeps_batch_product_when_other_lines_exist(self):
        batch = self._create_batch()
        order = self._create_order(batch=batch)
        line2 = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom_qty": 2,
                "price_unit": 10.0,
            }
        )
        batch_product = order.order_line[0].batch_product_id
        order.order_line[0].unlink()
        self.assertTrue(batch_product.exists())
        self.assertIn(line2, batch_product.sale_order_line_ids)

    # --- _update_batch_product ---

    def test_update_batch_product_links_when_batch_assigned(self):
        order = self._create_order()
        line = order.order_line
        self.assertFalse(line.batch_product_id)
        batch = self._create_batch()
        order.write({"batch_id": batch.id})
        self.assertTrue(line.batch_product_id)

    def test_update_batch_product_unlinks_when_batch_removed(self):
        batch = self._create_batch()
        order = self._create_order(batch=batch)
        line = order.order_line
        self.assertTrue(line.batch_product_id)
        order.with_context(disable_cancel_warning=True).write({"batch_id": False})
        self.assertFalse(line.batch_product_id)
