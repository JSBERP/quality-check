import frappe
import os

def execute():
    PARENT_DTYPE = "Quality Checking"

    # 1. Add new header fields
    fields_to_add = [
        {"fieldname": "order_code", "label": "Order Code", "fieldtype": "Data", "insert_after": "roll_no"},
        {"fieldname": "unit", "label": "Unit", "fieldtype": "Data", "insert_after": "order_code"},
        {"fieldname": "shift", "label": "Shift", "fieldtype": "Data", "insert_after": "unit"},
        {"fieldname": "fabric_type", "label": "Fabric Type", "fieldtype": "Data", "insert_after": "shift"}
    ]

    for field in fields_to_add:
        if not frappe.db.exists("DocField", {"parent": PARENT_DTYPE, "fieldname": field["fieldname"]}):
            frappe.get_doc({
                "doctype": "DocField",
                "parent": PARENT_DTYPE,
                "parenttype": "DocType",
                "parentfield": "fields",
                "fieldname": field["fieldname"],
                "label": field["label"],
                "fieldtype": field["fieldtype"],
                "insert_after": field["insert_after"]
            }).insert(ignore_permissions=True)

    # 2. Add new summary fields
    summary_fields = [
        {"fieldname": "gsm_total_samples", "label": "Total Samples", "fieldtype": "Int", "read_only": 1, "insert_after": "gsm_overall_result"},
        {"fieldname": "gsm_pass_samples", "label": "Pass Samples", "fieldtype": "Int", "read_only": 1, "insert_after": "gsm_total_samples"},
        {"fieldname": "gsm_fail_samples", "label": "Fail Samples", "fieldtype": "Int", "read_only": 1, "insert_after": "gsm_pass_samples"}
    ]

    for field in summary_fields:
        if not frappe.db.exists("DocField", {"parent": PARENT_DTYPE, "fieldname": field["fieldname"]}):
            frappe.get_doc({
                "doctype": "DocField",
                "parent": PARENT_DTYPE,
                "parenttype": "DocType",
                "parentfield": "fields",
                "fieldname": field["fieldname"],
                "label": field["label"],
                "fieldtype": field["fieldtype"],
                "read_only": field.get("read_only", 0),
                "insert_after": field["insert_after"]
            }).insert(ignore_permissions=True)

    # 3. Hide old summary fields
    old_fields = ["gsm_total_sections", "gsm_pass_sections", "gsm_fail_sections"]
    for field in old_fields:
        if frappe.db.exists("DocField", {"parent": PARENT_DTYPE, "fieldname": field}):
            frappe.db.set_value("DocField", {"parent": PARENT_DTYPE, "fieldname": field}, "hidden", 1)

    # 4. Update Client Scripts
    update_client_scripts()

    frappe.clear_cache(doctype=PARENT_DTYPE)
    frappe.clear_cache(doctype="Shaft Production Run")


def update_client_scripts():
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
