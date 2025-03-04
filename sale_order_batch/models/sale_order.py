from odoo import _, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    batch_id = fields.Many2one("sale.order.batch", copy=False, check_company=True, domain="[('state','!=','closed')]")

    def action_add_to_batch(self):
        """
        TODO: Add Wizard to choose between batches if more than one existis. Picking the first one for now.
        """
        for sale_order in self:
            company = sale_order.company_id
            sale_order = sale_order.with_company(company)
            batch = self.env["sale.order.batch"].search(
                [("state", "=", "open"), ("company_id", "=", company.id)], limit=1
            )
            if not sale_order.batch_id and sale_order.state in ["draft", "sent"]:
                if not batch:
                    batch = sale_order.env["sale.order.batch"].create({})
                sale_order.batch_id = batch

    def action_view_sale_order_batch(self):
        return {
            "name": _("Sale Order Batch"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sale.order.batch",
            "res_id": self.batch_id.id,
        }

    def action_confirm(self):
        invalid_orders = []
        if not self.env.context.get("bypass_batch", False):
            for order in self:
                if order.batch_id:
                    invalid_orders.append(order.name)
            if invalid_orders:
                raise UserError(_(f"Sale Order belongs to a Batch: {', '.join(invalid_orders)}"))
        return super().action_confirm()
