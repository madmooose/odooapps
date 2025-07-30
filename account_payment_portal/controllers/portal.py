from collections import OrderedDict

from odoo import _, http
from odoo.http import request
from odoo.osv import expression

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class AccountPaymentPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "payment_count" in counters:
            payment_count = (
                request.env["account.payment"].search_count(self._get_payment_domain())
                if request.env["account.payment"].check_access_rights(
                    "read", raise_exception=False
                )
                else 0
            )
            values["payment_count"] = payment_count
        return values

    # ------------------------------------------------------------
    # My Payments
    # ------------------------------------------------------------

    def _payment_get_page_view_values(self, payment, access_token, **kwargs):
        values = {"page_name": "payment", "payment": payment}
        return self._get_page_view_values(
            payment, access_token, values, "my_invoices_history", False, **kwargs
        )

    def _get_payment_domain(self):
        return [("is_internal_transfer", "=", False)]

    def _get_account_searchbar_sortings(self):
        return {
            "date": {"label": _("Date"), "order": "date desc"},
            "name": {"label": _("Reference"), "order": "name desc"},
            "state": {"label": _("Status"), "order": "state"},
        }

    def _get_account_searchbar_filters(self):
        # Add filter for payments and credit notes?
        return {
            "all": {"label": _("All"), "domain": []},
            "sent": {
                "label": _("Sent"),
                "domain": [("payment_type", "=", "inbound")],
            },
            "received": {
                "label": _("Received"),
                "domain": [("payment_type", "=", "outbound")],
            },
        }

    @http.route(
        ["/my/payments", "/my/payments/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_payments(
        self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw
    ):
        values = self._prepare_my_payments_values(
            page, date_begin, date_end, sortby, filterby
        )

        # pager
        pager = portal_pager(**values["pager"])

        # content according to pager and archive selected
        payments = values["payments"](pager["offset"])
        request.session["my_payments_history"] = payments.ids[:100]

        values.update({"payments": payments, "pager": pager})

        return request.render("account_payment_portal.portal_my_payments", values)

    def _prepare_my_payments_values(
        self,
        page,
        date_begin,
        date_end,
        sortby,
        filterby,
        domain=None,
        url="/my/payments",
    ):
        values = self._prepare_portal_layout_values()
        AccountPayment = request.env["account.payment"]

        domain = expression.AND([domain or [], self._get_payment_domain()])

        searchbar_sortings = self._get_account_searchbar_sortings()
        # default sort by order
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]

        searchbar_filters = self._get_account_searchbar_filters()
        # default filter by value
        if not filterby:
            filterby = "all"
        domain += searchbar_filters[filterby]["domain"]

        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]

        values.update(
            {
                "date": date_begin,
                # content according to pager and archive selected lambda function to
                # get the invoices recordset when the pager will be defined in the main
                # method of a route
                "payments": lambda pager_offset: (
                    AccountPayment.search(
                        domain,
                        order=order,
                        limit=self._items_per_page,
                        offset=pager_offset,
                    )
                    if AccountPayment.check_access_rights("read", raise_exception=False)
                    else AccountPayment
                ),
                "page_name": "payment",
                "pager": {  # vals to define the pager.
                    "url": url,
                    "url_args": {
                        "date_begin": date_begin,
                        "date_end": date_end,
                        "sortby": sortby,
                    },
                    "total": AccountPayment.search_count(domain)
                    if AccountPayment.check_access_rights("read", raise_exception=False)
                    else 0,
                    "page": page,
                    "step": self._items_per_page,
                },
                "default_url": url,
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
                "searchbar_filters": OrderedDict(sorted(searchbar_filters.items())),
                "filterby": filterby,
            }
        )
        return values
