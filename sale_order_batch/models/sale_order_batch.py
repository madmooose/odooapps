from datetime import timedelta

from odoo import _, api, fields, models


STATES = [("open", "Open"), ("close", "Close")]

READONLY_FIELD_STATES = {state: [("readonly", True)] for state in {"close"}}


class SaleOrderBatch(models.Model):
    """Group serveral Sale Orders into a batch"""

    _name = "sale.order.batch"
    _description = "Sales Order Batch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_order desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        string="Order Batch Reference",
        required=True,
        copy=False,
        readonly=True,
        index="trigram",
        default=lambda self: _("New"),
    )
    company_id = fields.Many2one(
        comodel_name="res.company", required=True, index=True, default=lambda self: self.env.company
    )
    state = fields.Selection(
        selection=[("open", "Open"), ("closed", "Closed")],
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        tracking=1,
        default="open",
    )
    date_order = fields.Datetime(
        string="Order Date",
        required=True,
        readonly=False,
        copy=False,
        states={"closed": [("readonly", True)]},
        help="Creation date of order batch,\nConfirmation date of confirmed orders.",
        default=fields.Datetime.now,
    )
    validity_date = fields.Date(
        string="Expiration",
        compute="_compute_validity_date",
        inverse="_inverse_validity_date",
        store=True,
        readonly=False,
        copy=False,
        precompute=True,
        states=READONLY_FIELD_STATES,
    )
    sale_order_ids = fields.One2many("sale.order", "batch_id")
    sale_order_count = fields.Integer(compute="_compute_sale_order_count")
    sale_order_line_ids = fields.Many2many("sale.order.line", compute="_compute_sale_order_line_ids", store=True)
    invoice_ids = fields.Many2many("account.move", compute="_compute_invoice_ids")
    invoice_count = fields.Integer(compute="_compute_invoice_ids")
    amount_total = fields.Float(compute="_compute_amount_total", string="Total")
    product_ids = fields.One2many("sale.order.batch.product", "batch_id")
    product_count = fields.Integer(compute="_compute_product_count")
    partner_credit_warning = fields.Text(compute="_compute_partner_credit_warning")

    @api.depends("company_id")
    def _compute_validity_date(self):
        enabled_feature = bool(self.env["ir.config_parameter"].sudo().get_param("sale.use_quotation_validity_days"))
        if not enabled_feature:
            self.validity_date = False
            return
        today = fields.Date.context_today(self)
        for batch in self:
            days = batch.company_id.quotation_validity_days
            if days > 0:
                batch.validity_date = today + timedelta(days)
            else:
                batch.validity_date = False

    def _inverse_validity_date(self):
        """
        Set validity date on all Sale Orders
        """
        for batch in self:
            for order in batch.sale_order_ids:
                order.validity_date = batch.validity_date

    @api.depends("sale_order_ids.order_line")
    def _compute_sale_order_line_ids(self):
        for batch in self:
            order_lines = self.env["sale.order.line"].search([("order_id", "in", batch.sale_order_ids.ids)])
            batch.sale_order_line_ids = order_lines

    @api.depends("sale_order_ids")
    def _compute_sale_order_count(self):
        for batch in self:
            batch.sale_order_count = len(batch.sale_order_ids)

    @api.depends("sale_order_ids.invoice_ids")
    def _compute_invoice_ids(self):
        for batch in self:
            invoices = batch.sale_order_ids.mapped("invoice_ids")
            batch.invoice_ids = invoices
            batch.invoice_count = len(invoices)

    @api.depends("sale_order_ids.amount_total")
    def _compute_amount_total(self):
        for batch in self:
            batch.amount_total = sum(batch.sale_order_ids.mapped("amount_total"))

    @api.depends("product_ids")
    def _compute_product_count(self):
        for batch in self:
            batch.product_count = len(batch.product_ids)

    @api.depends("sale_order_ids.partner_credit_warning")
    def _compute_partner_credit_warning(self):
        for batch in self:
            batch.partner_credit_warning = ""
            for order in batch.sale_order_ids:
                if order.partner_credit_warning:
                    batch.partner_credit_warning += order.partner_credit_warning + "\n"

    def action_view_source_sale_orders(self):
        self.ensure_one()
        result = self.env["ir.actions.act_window"]._for_xml_id("sale.action_orders")
        if len(self.sale_order_ids) > 1:
            result["domain"] = [("id", "in", self.sale_order_ids.ids)]
        elif len(self.sale_order_ids) == 1:
            result["views"] = [(self.env.ref("sale.view_order_form", False).id, "form")]
            result["res_id"] = self.sale_order_ids.id
        else:
            result = {"type": "ir.actions.act_window_close"}
        return result

    def action_view_products(self):
        self.ensure_one()
        result = self.env["ir.actions.act_window"]._for_xml_id("product.product_normal_action_sell")
        if len(self.product_ids) > 1:
            result["domain"] = [("id", "in", self.product_ids.ids)]
        elif len(self.product_ids) == 1:
            result["views"] = [(self.env.ref("product.product_product_tree_view", False).id, "form")]
            result["res_id"] = self.product_ids.id
        else:
            result = {"type": "ir.actions.act_window_close"}
        return result

    def action_view_invoice(self):
        invoices = self.mapped("invoice_ids")
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(invoices) > 1:
            action["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref("account.view_move_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [(state, view) for state, view in action["views"] if view != "form"]
            else:
                action["views"] = form_view
            action["res_id"] = invoices.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        action["context"] = {"default_move_type": "out_invoice"}
        return action

    def action_confirm(self):
        for batch in self:
            orders = batch.with_context(bypass_batch=True).sale_order_ids
            orders.action_confirm()
            batch.state = "closed"
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "company_id" in vals:
                self = self.with_company(vals["company_id"])
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("sale.order.batch") or _("New")
        return super().create(vals_list)
