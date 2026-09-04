import frappe
import os

def execute():
    # 1. Create Child Table DocType
    if not frappe.db.exists("DocType", "Tensile Testing Result"):
        frappe.get_doc({
            "doctype": "DocType",
            "name": "Tensile Testing Result",
            "module": "Quality",
            "custom": 1,
            "istable": 1,
            "editable_grid": 1,
            "fields": [
                {"fieldname": "properties", "label": "Properties", "fieldtype": "Data", "in_list_view": 1},
                {"fieldname": "uom", "label": "UOM", "fieldtype": "Link", "options": "UOM", "default": "Kg", "in_list_view": 1},
                {"fieldname": "sample_1", "label": "Sample 1", "fieldtype": "Float", "in_list_view": 1},
                {"fieldname": "sample_2", "label": "Sample 2", "fieldtype": "Float", "in_list_view": 1},
                {"fieldname": "sample_3", "label": "Sample 3", "fieldtype": "Float", "in_list_view": 1},
                {"fieldname": "sample_4", "label": "Sample 4", "fieldtype": "Float", "in_list_view": 1},
                {"fieldname": "sample_5", "label": "Sample 5", "fieldtype": "Float", "in_list_view": 1},
                {"fieldname": "average", "label": "Average", "fieldtype": "Float", "read_only": 1, "in_list_view": 1}
            ]
        }).insert(ignore_permissions=True)

    # 2. Add Fields to Quality Checking
    PARENT_DTYPE = "Quality Checking"
    fields_to_add = [
        {"fieldname": "testing_type", "label": "Testing Type", "fieldtype": "Select", "options": "GSM Testing\nTensile Testing", "default": "GSM Testing", "insert_after": "fabric_type"},
        {"fieldname": "test_method", "label": "Test Method", "fieldtype": "Data", "default": "ASTM D5733", "insert_after": "testing_type"},
        {"fieldname": "cutting_template_width", "label": "Cutting Template Width", "fieldtype": "Data", "default": "150 MM", "insert_after": "test_method"},
        {"fieldname": "cutting_template_height", "label": "Cutting Template Height", "fieldtype": "Data", "default": "75 MM", "insert_after": "cutting_template_width"},
        {"fieldname": "tensile_sections", "label": "Tensile Testing Sections", "fieldtype": "Table", "options": "Tensile Testing Result", "insert_after": "sections"},
        {"fieldname": "tensile_total_samples", "label": "Total Samples", "fieldtype": "Int", "read_only": 1, "insert_after": "tensile_sections"}
    ]

    for field in fields_to_add:
        if not frappe.db.exists("DocField", {"parent": PARENT_DTYPE, "fieldname": field["fieldname"]}):
            doc = frappe.get_doc({
                "doctype": "DocField",
                "parent": PARENT_DTYPE,
                "parenttype": "DocType",
                "parentfield": "fields",
                "fieldname": field["fieldname"],
                "label": field["label"],
                "fieldtype": field["fieldtype"],
                "insert_after": field["insert_after"]
            })
            if "options" in field:
                doc.options = field["options"]
            if "default" in field:
                doc.default = field["default"]
            if "read_only" in field:
                doc.read_only = field["read_only"]
            
            doc.insert(ignore_permissions=True)
            
    # Force the database schema to update
    dt = frappe.get_doc("DocType", PARENT_DTYPE)
    dt.save(ignore_permissions=True)

    # 3. Update Client Scripts
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
