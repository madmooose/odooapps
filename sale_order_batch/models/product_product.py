from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    batch_ids = fields.Many2many("sale.order.batch", "product_ids")
