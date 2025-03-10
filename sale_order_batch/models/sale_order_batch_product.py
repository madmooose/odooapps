from odoo import api, fields, models


class SaleOrderBatchProduct(models.Model):
    """Show Products available in Sale Order Batch"""

    _name = "sale.order.batch.product"
    _description = "Sale Order Batch Product"

    batch_id = fields.Many2one(
        comodel_name="sale.order.batch",
        string="Batch Reference",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
        readonly=True,
    )

    # TODO: compute and store
    product_id = fields.Many2one(comodel_name="product.product", required=True, readonly=True)

    product_template_id = fields.Many2one(
        "product.template", related="product_id.product_tmpl_id", string="Product Template"
    )
    sale_order_line_ids = fields.One2many("sale.order.line", "batch_product_id")
    product_uom_category_id = fields.Many2one(related="product_id.uom_id.category_id", depends=["product_id"])
    product_uom_qty = fields.Float(compute="_compute_uom_qty", string="Quantity")
    product_uom = fields.Many2one(related="product_id.uom_id")
    product_packaging_id = fields.Many2one("product.packaging")
    product_packaging_qty = fields.Float(compute="_compute_product_packaging_qty")

    @api.depends("sale_order_line_ids.product_uom_qty")
    def _compute_uom_qty(self):
        for product in self:
            product.product_uom_qty = sum(product.sale_order_line_ids.mapped("product_uom_qty"))

    @api.depends("product_packaging_id")
    def _compute_product_packaging_qty(self):
        for product in self:
            product.product_packaging_qty = product.product_packaging_id.qty if product.product_packaging_id else 1

    def unlink(self):
        for product in self:
            if not product.sale_order_line_ids:
                return super().unlink()
        return True
