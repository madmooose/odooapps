from odoo.tests import TransactionCase


class TestSaleOrderBatchProduct(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context={**cls.env.context, "tracking_disable": True})
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "service"}
        )

    def _create_batch_with_order(self, qty=1):
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
                            "product_uom_qty": qty,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        return batch, order, batch.product_ids[0]

    # --- _compute_uom_qty ---

    def test_compute_uom_qty_single_line(self):
        batch, order, batch_product = self._create_batch_with_order(qty=3)
        self.assertAlmostEqual(batch_product.product_uom_qty, 3.0)

    def test_compute_uom_qty_multiple_lines(self):
        batch, order, batch_product = self._create_batch_with_order(qty=3)
        self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom_qty": 2,
                "price_unit": 10.0,
            }
        )
        self.assertAlmostEqual(batch_product.product_uom_qty, 5.0)

    # --- _compute_product_packaging_qty ---

    def test_compute_product_packaging_qty_without_packaging(self):
        batch, order, batch_product = self._create_batch_with_order()
        if not batch_product.product_packaging_id:
            self.assertEqual(batch_product.product_packaging_qty, 1)

    def test_compute_product_packaging_qty_with_packaging(self):
        packaging = self.env["product.packaging"].create(
            {
                "name": "Box of 10",
                "product_id": self.product.id,
                "qty": 10.0,
                "sales": True,
            }
        )
        batch, order, batch_product = self._create_batch_with_order(qty=5)
        self.assertEqual(batch_product.product_packaging_id, packaging)
        self.assertEqual(batch_product.product_packaging_qty, 10.0)

    # --- _compute_product_packaging_id ---

    def test_compute_product_packaging_id_suggests_first_packaging(self):
        packaging = self.env["product.packaging"].create(
            {
                "name": "Box of 6",
                "product_id": self.product.id,
                "qty": 6.0,
                "sales": True,
            }
        )
        batch, order, batch_product = self._create_batch_with_order(qty=4)
        self.assertEqual(batch_product.product_packaging_id, packaging)

    def test_compute_product_packaging_id_clears_wrong_product_packaging(self):
        product2 = self.env["product.product"].create(
            {"name": "Other Product", "type": "service"}
        )
        packaging2 = self.env["product.packaging"].create(
            {
                "name": "Box of 5",
                "product_id": product2.id,
                "qty": 5.0,
                "sales": True,
            }
        )
        batch, order, batch_product = self._create_batch_with_order()
        batch_product.product_packaging_id = packaging2
        batch_product._compute_product_packaging_id()
        self.assertFalse(batch_product.product_packaging_id)

    def test_compute_product_packaging_id_no_packaging_when_no_qty(self):
        self.env["product.packaging"].create(
            {
                "name": "Box of 12",
                "product_id": self.product.id,
                "qty": 12.0,
                "sales": True,
            }
        )
        batch = self.env["sale.order.batch"].create({})
        batch_product = self.env["sale.order.batch.product"].create(
            {"batch_id": batch.id, "product_id": self.product.id}
        )
        # With no lines, product_uom_qty is 0 — packaging should not be suggested
        self.assertFalse(batch_product.product_uom_qty)
        self.assertFalse(batch_product.product_packaging_id)
