import frappe

def execute():
    # Find all Client Scripts for Shaft Production Run
    client_scripts = frappe.get_all("Client Script", filters={"dt": "Shaft Production Run"}, fields=["name", "script"])
    for cs_info in client_scripts:
        cs = frappe.get_doc("Client Script", cs_info.name)
        script = cs.script or ""
        
        # Check if this script contains the old button adding code but is not our managed one
        if "Start GSM Testing" in script:
            # To safely disable the button addition without breaking JS syntax:
            # wrap the call in `if (false)`
            updated_script = script
            
            targets = [
                'frm.add_custom_button(__("Start GSM Testing")',
                "frm.add_custom_button(__('Start GSM Testing')",
                'frm.add_custom_button("Start GSM Testing"',
                "frm.add_custom_button('Start GSM Testing'"
            ]
            
            for target in targets:
                if target in updated_script:
                    # Only disable if it's not already disabled
                    disabled_target = f"if (false) {target}"
                    if disabled_target not in updated_script:
                        updated_script = updated_script.replace(target, disabled_target)
            
            if updated_script != script:
                cs.script = updated_script
                cs.save(ignore_permissions=True)
                frappe.db.commit()

    frappe.clear_cache()
