from odoo import api, fields, models

from .sale_order_batch import READONLY_FIELD_STATES


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
    state = fields.Selection(related="batch_id.state")
    product_id = fields.Many2one(comodel_name="product.product", required=True, readonly=True)
    product_template_id = fields.Many2one(
        "product.template", related="product_id.product_tmpl_id", string="Product Template"
    )
    sale_order_line_ids = fields.One2many("sale.order.line", "batch_product_id", states=READONLY_FIELD_STATES)
    product_uom_category_id = fields.Many2one(related="product_id.uom_id.category_id", depends=["product_id"])
    product_uom_qty = fields.Float(compute="_compute_uom_qty", string="Quantity")
    product_uom = fields.Many2one(related="product_id.uom_id")
    lst_price = fields.Float(
        "Sales Price",
        related="product_id.lst_price",
        digits="Product Price",
        help="""The sale price is managed from the product template. Click on the
        'Configure Variants' button to set the extra attribute prices.""",
    )
    product_packaging_id = fields.Many2one(
        comodel_name="product.packaging",
        string="Packaging",
        compute="_compute_product_packaging_id",
        store=True,
        readonly=False,
        precompute=True,
        domain="[('sales', '=', True), ('product_id','=',product_id)]",
    )
    product_packaging_qty = fields.Float(compute="_compute_product_packaging_qty")

    @api.constrains("product_id", "sale_order_line_ids")
    def _check_sale_order_line_products(self):
        for product in self:
            if any(line.product_id != product.product_id for line in product.sale_order_line_ids):
                raise ValueError("Product must be the same for all Sale Order Lines")

    @api.depends("sale_order_line_ids.product_uom_qty")
    def _compute_uom_qty(self):
        for product in self:
            product.product_uom_qty = sum(product.sale_order_line_ids.mapped("product_uom_qty"))

    @api.depends("product_id", "product_uom_qty", "product_uom")
    def _compute_product_packaging_id(self):
        for line in self:
            # remove packaging if not match the product
            if line.product_packaging_id and line.product_packaging_id.product_id != line.product_id:
                line.product_packaging_id = False
            # suggest always the first packaging
            if line.product_id and line.product_uom_qty and line.product_uom:
                suggested_packaging = line.product_id.packaging_ids[0] if line.product_id.packaging_ids else False
                line.product_packaging_id = suggested_packaging or line.product_packaging_id

    @api.depends("product_packaging_id")
    def _compute_product_packaging_qty(self):
        for product in self:
            product.product_packaging_qty = product.product_packaging_id.qty if product.product_packaging_id else 1
