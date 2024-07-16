from odoo import _, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    batch_id = fields.Many2one("sale.order.batch")

    def action_add_to_batch(self):
        batch = self.env["sale.order.batch"].search([("state", "=", "open")], limit=1)
        if not batch:
            batch = self.env["sale.order.batch"].create()
        for sale_order in self:
            if not sale_order.batch_id and sale_order.state in ["draft", "sent"]:
                sale_order.batch_id = batch

    def write(self, vals):
        if "batch_id" in vals:
            invalid_orders = []
            for order in self:
                if order.state not in ["draft", "sent"]:
                    invalid_orders.append(order.name)
            if invalid_orders:
                raise UserError(_(f"Sale Order not in State Draft or Sent: {', '.join(invalid_orders)}"))
        return super().write(vals)
