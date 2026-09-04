import frappe


def _run_quality_checking_setup():
    # Run latest schema setup in an idempotent way for cloud updates.
    # Cloud-safe: create/update only the new main doctype (Quality Checking) and GSM schema.
    from quality_gsm_app.patches.v2_0 import create_quality_checking_only
    from quality_gsm_app.patches.v1_3 import force_quality_checking_parent_fix
    from quality_gsm_app.patches.v1_4 import ensure_quality_checking_permissions
    from quality_gsm_app.patches.v2_2 import update_gsm_report_layout_excel_style
    from quality_gsm_app.patches.v2_3 import enforce_field_permanence

    create_quality_checking_only.execute()
    force_quality_checking_parent_fix.execute()
    ensure_quality_checking_permissions.execute()
    update_gsm_report_layout_excel_style.execute()
    enforce_field_permanence.execute()
    from quality_gsm_app.patches.v2_20_filter_qc_sections_by_roll import execute as sync_qc_scripts
    from quality_gsm_app.patches.v2_21_show_only_selected_gsm_and_test import execute as show_selected_gsm

    sync_qc_scripts()
    show_selected_gsm()
    frappe.db.commit()


def after_install():
    _run_quality_checking_setup()


def after_migrate():
    _run_quality_checking_setup()

