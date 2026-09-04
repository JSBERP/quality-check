import frappe
import os

def execute():
    app_path = frappe.get_app_path("quality_gsm_app")
    
    scripts = {
        "Quality Checking": "public/js/quality_inspection_gsm.js",
        "Shaft Production Run": "public/js/shaft_production_run_quality_button.js"
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
        
        # Check if client script already exists for this doctype
        existing = frappe.get_all("Client Script", filters={"dt": dt}, limit=1)
        if existing:
            cs = frappe.get_doc("Client Script", existing[0].name)
            cs.script = script_content
            cs.enabled = 1
            cs.save(ignore_permissions=True)
        else:
            frappe.get_doc({
                "doctype": "Client Script",
                "name": script_name,
                "dt": dt,
                "module": "Quality",
                "script": script_content,
                "enabled": 1
            }).insert(ignore_permissions=True)

    frappe.clear_cache()
