from odoo import api, fields, models


STATES = [("open", "Open"), ("close", "Close")]


class SaleOrderBatch(models.Model):
    _inherit = "sale.order.batch"

    picking_ids = fields.Many2many(
        "stock.picking", compute="_compute_picking_ids", string="Transfers"
    )
    delivery_count = fields.Integer(
        string="Delivery Orders", compute="_compute_picking_ids"
    )

    @api.depends("sale_order_ids.picking_ids")
    def _compute_picking_ids(self):
        for batch in self:
            pickings = batch.sale_order_ids.mapped("picking_ids")
            batch.picking_ids = pickings
            batch.delivery_count = len(pickings)

    def action_view_delivery(self):
        return self.env["sale.order"]._get_action_view_picking(self.picking_ids)
