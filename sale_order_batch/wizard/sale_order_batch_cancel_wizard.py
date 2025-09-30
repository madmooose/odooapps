from odoo import api, fields, models


class SaleOrderBatchCancelWizard(models.TransientModel):
    _name = "sale.order.batch.cancel.wizard"
    _description = "Cancel Sale Order Batch Confirmation"

    batch_ids = fields.Many2many(
        comodel_name="sale.order.batch",
        string="Batches to Cancel",
        default=lambda self: self.env["sale.order.batch"].browse(
            self.env.context.get("active_ids", [])
        ),
    )

    order_ids = fields.Many2many(
        comodel_name="sale.order",
        string="Orders to Cancel",
        compute="_compute_order_ids",
    )

    @api.depends("batch_ids")
    def _compute_order_ids(self):
        for record in self:
            batches = record.batch_ids
            record.order_ids = batches.mapped("sale_order_ids")

    def action_cancel(self):
        batches = self.batch_ids
        batches._action_cancel()
        return {"type": "ir.actions.act_window_close"}

    def action_discard(self):
        return {"type": "ir.actions.act_window_close"}
