from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    batch_id = fields.Many2one("sale.order.batch", copy=False, check_company=True)

    def action_add_to_batch(self):
        """
        TODO: Add Wizard to choose between batches if more than one existis. Picking the first one for now.
        """
        self = self.with_company(self.company_id)
        batch = self.env["sale.order.batch"].search(
            [("state", "=", "open"), ("company_id", "=", self.company_id.id)], limit=1
        )
        if not batch:
            batch = self.env["sale.order.batch"].create({})
        for sale_order in self:
            if not sale_order.batch_id and sale_order.state in ["draft", "sent"]:
                sale_order.batch_id = batch

    def action_view_sale_order_batch(self):
        return {
            "name": _("Sale Order Batch"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sale.order.batch",
            "res_id": self.batch_id.id,
            # 'target': '',
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("batch_id"):
                vals["validity_date"] = (
                    self.env["sale.order.batch"].search([("id", "=", vals.get("batch_id"))]).validity_date
                )
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("batch_id"):
            vals["validity_date"] = (
                self.env["sale.order.batch"].search([("id", "=", vals.get("batch_id"))]).validity_date
            )
        res = super().write(vals)
        if vals.get("batch_id"):
            self.order_line._update_batch_product()
        return res
