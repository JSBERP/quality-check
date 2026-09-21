import frappe
import os


PARENT_DTYPE = "Quality Checking"

TESTING_TYPE_OPTIONS = "Round Cutting GSM Test\nPatty Cutting GSM Test\nTensile Testing"

FIELD_DEPENDS = {
    "test_method": "eval:doc.testing_type=='Tensile Testing'",
    "tensile_sections": "eval:doc.testing_type=='Tensile Testing'",
    "tensile_total_samples": "eval:doc.testing_type=='Tensile Testing'",
    "cutting_template_width": (
        "eval:in_list(['Tensile Testing','Patty Cutting GSM Test'], doc.testing_type)"
    ),
    "cutting_template_height": (
        "eval:in_list(['Tensile Testing','Patty Cutting GSM Test'], doc.testing_type)"
    ),
    "custom_html_grid": "eval:doc.testing_type!='Tensile Testing'",
    "custom_gsm_grid_html": "eval:doc.testing_type!='Tensile Testing'",
    "gsm_total_samples": "eval:doc.testing_type!='Tensile Testing'",
    "gsm_pass_samples": "eval:doc.testing_type!='Tensile Testing'",
    "gsm_fail_samples": "eval:doc.testing_type!='Tensile Testing'",
    "gsm_overall_result": "eval:doc.testing_type!='Tensile Testing'",
}


def execute():
    if not frappe.db.exists("DocType", PARENT_DTYPE):
        return

    dt = frappe.get_doc("DocType", PARENT_DTYPE)
    by_name = {f.fieldname: f for f in dt.fields}
    changed = False

    testing = by_name.get("testing_type")
    if testing:
        if testing.options != TESTING_TYPE_OPTIONS:
            testing.options = TESTING_TYPE_OPTIONS
            changed = True
        if testing.default in (None, "", "GSM Testing"):
            testing.default = "Round Cutting GSM Test"
            changed = True

    if "gsm" not in by_name:
        insert_after = "batch_no" if "batch_no" in by_name else "testing_type"
        dt.append(
            "fields",
            {
                "fieldname": "gsm",
                "label": "GSM",
                "fieldtype": "Float",
                "insert_after": insert_after,
                "read_only": 1,
            },
        )
        changed = True

    for fieldname, depends_on in FIELD_DEPENDS.items():
        field = by_name.get(fieldname)
        if not field:
            continue
        if field.depends_on != depends_on:
            field.depends_on = depends_on
            changed = True

    if changed:
        dt.save(ignore_permissions=True)
        frappe.db.commit()

    frappe.db.sql(
        """
        UPDATE `tabQuality Checking`
        SET testing_type = 'Round Cutting GSM Test'
        WHERE testing_type = 'GSM Testing' OR testing_type IS NULL OR testing_type = ''
        """
    )
    frappe.db.commit()

    _sync_client_scripts()
    frappe.clear_cache(doctype=PARENT_DTYPE)
    frappe.clear_cache(doctype="Shaft Production Run")


def _sync_client_scripts():
    app_path = frappe.get_app_path("quality_gsm_app")
    scripts = {
        "Quality Checking": "public/js/quality_inspection_gsm.js",
        "Shaft Production Run": "public/js/shaft_production_run_quality_button.js",
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
        else:
            frappe.get_doc(
                {
                    "doctype": "Client Script",
                    "name": f"{dt} Client Script",
                    "dt": dt,
                    "module": "Quality Checking" if dt == "Quality Checking" else "Manufacturing",
                    "script": script_content,
                    "enabled": 1,
                }
            ).insert(ignore_permissions=True)
    frappe.clear_cache()
