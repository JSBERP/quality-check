import frappe
import os

def execute():
    PARENT_DTYPE = "Quality Checking"

    if not frappe.db.exists("DocField", {"parent": PARENT_DTYPE, "fieldname": "date"}):
        frappe.get_doc({
            "doctype": "DocField",
            "parent": PARENT_DTYPE,
            "parenttype": "DocType",
            "parentfield": "fields",
            "fieldname": "date",
            "label": "Date",
            "fieldtype": "Date",
            "insert_after": "roll_no"
        }).insert(ignore_permissions=True)

    # Update Client Scripts to make sure latest JS is applied
    update_client_scripts()
    frappe.clear_cache(doctype=PARENT_DTYPE)

def update_client_scripts():
    app_path = frappe.get_app_path("quality_gsm_app")
    
    scripts = {
        "Quality Checking": "public/js/quality_inspection_gsm.js"
    }
    
    for dt, js_path in scripts.items():
        if not frappe.db.exists("DocType", dt):
            continue
            
        full_path = os.path.join(app_path, js_path)
        if not os.path.exists(full_path):
            continue
            
        with open(full_path, "r", encoding="utf-8") as f:
            script_content = f.read()
            
        existing = frappe.get_all("Client Script", filters={"dt": dt}, limit=1)
        if existing:
            cs = frappe.get_doc("Client Script", existing[0].name)
            cs.script = script_content
            cs.enabled = 1
            cs.save(ignore_permissions=True)
