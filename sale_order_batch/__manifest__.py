{
    "name": "Sale Order Batch",
    "summary": "Group Sale Orders into a batch",
    "author": "BAKEUP",
    "website": "https://www.bakeup.org",
    "category": "Sale",
    "version": "16.0.2.2.1",
    "depends": ["sale", "product"],
    "data": [
        "data/ir_sequence_data.xml",
        "views/sale_order_batch_views.xml",
        "views/sale_order_batch_product_views.xml",
        "views/sale_order_views.xml",
        "views/sale_menus.xml",
        "security/ir.model.access.csv",
        "security/ir_rules.xml",
    ],
    "license": "LGPL-3",
}
