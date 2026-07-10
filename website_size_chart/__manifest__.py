{
    "name": "Website Size Chart",
    "version": "19.0.1.0.0",
    "category": "Website/Website",
    "summary": "Display product size chart on website dynamically using Bootstrap Modal.",
    "author": "Tejash Ardeshna",
    "license": "LGPL-3",
    "depends": ["website_sale", "html_builder"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_size_chart_views.xml",
        "views/website_sale_templates.xml",
    ],
    "assets": {
        "website.website_builder_assets": [
            (
                "after",
                "website_sale/static/src/website_builder/product_page_option.xml",
                "website_size_chart/static/src/website_builder/product_page_option.xml",
            ),
        ],
    },
    "installable": True,
    "application": False,
}