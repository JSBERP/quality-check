import frappe
import os

def execute():
    PARENT_DTYPE = "Quality Checking"

    # 1. Add naming_series field
    if not frappe.db.exists("DocField", {"parent": PARENT_DTYPE, "fieldname": "naming_series"}):
        frappe.get_doc({
            "doctype": "DocField",
            "parent": PARENT_DTYPE,
            "parenttype": "DocType",
            "parentfield": "fields",
            "fieldname": "naming_series",
            "label": "Naming Series",
            "fieldtype": "Select",
            "options": "\nJSB/GSM-U1/26-27/.###\nJSB/GSM-U2/26-27/.###\nJSB/GSM-U3/26-27/.###\nJSB/GSM-U4/26-27/.###\nJSB/TT-U1/26-27/.###\nJSB/TT-U2/26-27/.###\nJSB/TT-U3/26-27/.###\nJSB/TT-U4/26-27/.###",
            "insert_after": "batch",
            "reqd": 1
        }).insert(ignore_permissions=True)
    else:
        doc = frappe.get_doc("DocField", {"parent": PARENT_DTYPE, "fieldname": "naming_series"})
        doc.options = "\nJSB/GSM-U1/26-27/.###\nJSB/GSM-U2/26-27/.###\nJSB/GSM-U3/26-27/.###\nJSB/GSM-U4/26-27/.###\nJSB/TT-U1/26-27/.###\nJSB/TT-U2/26-27/.###\nJSB/TT-U3/26-27/.###\nJSB/TT-U4/26-27/.###"
        doc.save(ignore_permissions=True)

    # 2. Update DocType Auto Name
    dt = frappe.get_doc("DocType", PARENT_DTYPE)
    dt.autoname = "naming_series:"
    dt.save(ignore_permissions=True)

    # 3. Add custom_unit to Shaft Production Run if it doesn't exist (assuming the user might need it if it's missing)
    # Actually wait, let's just make sure it runs.

    frappe.clear_cache(doctype=PARENT_DTYPE)
