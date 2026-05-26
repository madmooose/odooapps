from odoo import fields, models


class ProductAttributeValue(models.Model):
    """
    This class extends the functionality of product attribute values in Odoo.
    It adds a boolean field to determine if the variant value is visible in e-commerce.
    """

    _inherit = "product.attribute.value"

    visible_in_ecommerce = fields.Boolean(
        string="Visible in e-commerce",
        default=True,
        help="Determines if the variant value is visible in the e-commerce.",
    )
