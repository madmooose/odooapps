from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    batch_id = fields.Many2one(related="order_id.batch_id")
    batch_product_id = fields.Many2one("sale.order.batch.product")

    def _link_batch_product(self):
        lines_with_batch = self.filtered(lambda l: l.batch_id)
        for line in lines_with_batch:
            batch_id = line.batch_id
            batch_product = self.env["sale.order.batch.product"].search(
                [("product_id", "=", line.product_id.id), ("batch_id", "=", batch_id.id)], limit=1
            )
            if not batch_product:
                batch_product = self.env["sale.order.batch.product"].create(
                    {"batch_id": batch_id.id, "product_id": line.product_id.id}
                )
            line.batch_product_id = batch_product

    def _unlink_batch_product(self):
        lines_to_unlink = self.filtered(lambda l: l.batch_product_id)
        batch_product_unlink = self.env["sale.order.batch.product"]
        for line in lines_to_unlink:
            if line.batch_product_id:
                batch_product = line.batch_product_id
                if len(batch_product.sale_order_line_ids) == 1:
                    batch_product_unlink += batch_product
                else:
                    line.batch_product_id = False
        batch_product_unlink.unlink()

    def _update_batch_product(self):
        lines_with_batch = self.filtered(lambda l: l.batch_id)
        lines_without_batch = self - lines_with_batch
        lines_with_batch.filtered(
            lambda l: l.batch_product_id and l.batch_product_id.product_id != l.product_id
        )._unlink_batch_product()
        lines_with_batch._link_batch_product()
        lines_without_batch._unlink_batch_product()

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._link_batch_product()
        return res

    def write(self, vals):
        res = super().write(vals)
        if vals.get("product_id"):
            self._update_batch_product()
        return res

    def unlink(self):
        self._unlink_batch_product()
        return super().unlink()
