from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    batch_id = fields.Many2one(related="order_id.batch_id")
    batch_product_id = fields.Many2one("sale.order.batch.product")

    # TODO:
    # - recompute values on batchproduct
    # - check for last item on unlink or removal ob batch_id and remove batch_product_id
    @api.depends("batch_id", "batch_product_id")
    def _update_batch_product(self):
        for line in self:
            batch_id = line.batch_id
            if batch_id:
                batch_product = line.env["sale.order.batch.product"].search(
                    [("product_id", "=", line.product_id.id), ("batch_id", "=", batch_id.id)]
                )
                if not batch_product:
                    batch_product = line.env["sale.order.batch.product"].create(
                        {"batch_id": batch_id.id, "product_id": line.product_id.id}
                    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for line in res:
            if line.batch_id:
                res._update_batch_product()
        return res
