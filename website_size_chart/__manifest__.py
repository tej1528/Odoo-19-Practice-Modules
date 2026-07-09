{
    "name": "Website Size Chart",
    "version": "19.0.1.0.0",
    "category": "Website/Website",
    "summary": "Display product size chart on website dynamically using Bootstrap Modal.",
    "author": "Tejash Ardeshna",
    "depends": ["website", "website_sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_size_chart_views.xml",
        # "views/website_snippet_options.xml",
    ],
    'assets': {
    'website.assets_wysiwyg': [
        'website_size_chart/static/src/website_builder/product_page_option.xml',
    ],
},
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}