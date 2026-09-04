import frappe

def execute():
    # Remove the gsm_shift_session field since it's no longer needed
    if frappe.db.exists("DocField", {"parent": "Quality Checking", "fieldname": "gsm_shift_session"}):
        frappe.delete_doc("DocField", frappe.db.get_value("DocField", {"parent": "Quality Checking", "fieldname": "gsm_shift_session"}, "name"), force=1)
        frappe.clear_cache(doctype="Quality Checking")
