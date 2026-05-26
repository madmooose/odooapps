from odoo.tests import TransactionCase


class TestProductAttributeValue(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context={**cls.env.context, "tracking_disable": True})
        cls.attribute = cls.env["product.attribute"].create({"name": "Color"})
        cls.value_red = cls.env["product.attribute.value"].create(
            {"name": "Red", "attribute_id": cls.attribute.id}
        )
        cls.value_blue = cls.env["product.attribute.value"].create(
            {"name": "Blue", "attribute_id": cls.attribute.id}
        )

    # --- visible_in_ecommerce field ---

    def test_default_is_true(self):
        value = self.env["product.attribute.value"].create(
            {"name": "Green", "attribute_id": self.attribute.id}
        )
        self.assertTrue(value.visible_in_ecommerce)

    def test_can_be_set_false_on_create(self):
        value = self.env["product.attribute.value"].create(
            {
                "name": "Yellow",
                "attribute_id": self.attribute.id,
                "visible_in_ecommerce": False,
            }
        )
        self.assertFalse(value.visible_in_ecommerce)

    def test_write_false(self):
        self.value_red.write({"visible_in_ecommerce": False})
        self.assertFalse(self.value_red.visible_in_ecommerce)

    def test_write_toggle(self):
        self.value_red.write({"visible_in_ecommerce": False})
        self.assertFalse(self.value_red.visible_in_ecommerce)
        self.value_red.write({"visible_in_ecommerce": True})
        self.assertTrue(self.value_red.visible_in_ecommerce)
