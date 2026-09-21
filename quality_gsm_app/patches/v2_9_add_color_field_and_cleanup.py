import frappe
import os

def execute():
    PARENT_DTYPE = "Quality Checking"

    # Add Color field below Quality
    if not frappe.db.exists("DocField", {"parent": PARENT_DTYPE, "fieldname": "color"}):
        frappe.get_doc({
            "doctype": "DocField",
            "parent": PARENT_DTYPE,
            "parenttype": "DocType",
            "parentfield": "fields",
            "fieldname": "color",
            "label": "Color",
            "fieldtype": "Data",
            "insert_after": "quality"
        }).insert(ignore_permissions=True)

    # Update Client Scripts
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
            
        with open(full_path, "r") as f:
            script_content = f.read()
            
        script_name = f"{dt} Client Script"
        
        existing = frappe.get_all("Client Script", filters={"dt": dt}, limit=1)
        if existing:
            cs = frappe.get_doc("Client Script", existing[0].name)
            cs.script = script_content
            cs.enabled = 1
            cs.save(ignore_permissions=True)
