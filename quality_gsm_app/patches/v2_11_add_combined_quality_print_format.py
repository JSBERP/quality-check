import frappe
import os


PARENT_DTYPE = "Quality Checking"
PRINT_FORMAT_NAME = "Quality Testing Report"


def execute():
    app_path = frappe.get_app_path("quality_gsm_app")
    html_path = os.path.normpath(os.path.join(app_path, "..", "quality_checking_print_format.html"))

    if not os.path.exists(html_path):
        html_path = os.path.join(app_path, "quality_checking_print_format.html")

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    if frappe.db.exists("Print Format", PRINT_FORMAT_NAME):
        pf = frappe.get_doc("Print Format", PRINT_FORMAT_NAME)
        pf.doc_type = PARENT_DTYPE
        pf.print_format_type = "Jinja"
        pf.html = html
        pf.disabled = 0
        pf.save(ignore_permissions=True)
        return

    frappe.get_doc(
        {
            "doctype": "Print Format",
            "name": PRINT_FORMAT_NAME,
            "doc_type": PARENT_DTYPE,
            "print_format_type": "Jinja",
            "html": html,
            "disabled": 0,
        }
    ).insert(ignore_permissions=True)
