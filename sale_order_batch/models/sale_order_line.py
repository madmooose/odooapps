from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    batch_id = fields.Many2one(related="order_id.batch_id")

    def _update_batch_products(self):
        for order_line in self:
            batch_id = order_line.order_id.batch_id
            if batch_id:
                registered_products = batch_id.mapped("product_ids").mapped("product_id")
                if order_line.product_id not in registered_products:
                    self.env["sale.order.batch.product"].create(
                        {"batch_id": batch_id.id, "product_id": order_line.product_id.id}
                    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._update_batch_products()
        return res
