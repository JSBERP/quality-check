import frappe
import re

def execute():
    # Find all Client Scripts for Shaft Production Run
    client_scripts = frappe.get_all("Client Script", filters={"dt": "Shaft Production Run"}, fields=["name", "script"])
    
    # Regex pattern to match: (frm or cur_frm).add_custom_button(optional __("Start GSM/Tensile Testing")
    # This matches across newlines and spaces.
    pattern_gsm = re.compile(r"((?:frm|cur_frm)\s*\.\s*add_custom_button\s*\(\s*(?:__\s*\(\s*)?['\"]Start GSM Testing['\"])", re.IGNORECASE)
    pattern_tensile = re.compile(r"((?:frm|cur_frm)\s*\.\s*add_custom_button\s*\(\s*(?:__\s*\(\s*)?['\"]Start Tensile Testing['\"])", re.IGNORECASE)
    
    for cs_info in client_scripts:
        cs = frappe.get_doc("Client Script", cs_info.name)
        script = cs.script or ""
        
        updated_script = script
        
        # Disable GSM button if found
        if "Start GSM Testing" in updated_script:
            # Check if already disabled
            # We look for `if (false) ...` prefix
            matches = pattern_gsm.findall(updated_script)
            for match in matches:
                # Find if it is already preceded by `if (false)`
                # To be simple and robust, we can just replace the match if it doesn't already have `if (false)`
                idx = updated_script.find(match)
                if idx >= 11 and "if (false)" in updated_script[idx-15:idx]:
                    continue
                updated_script = updated_script.replace(match, f"if (false) {match}")
                
        # Disable Tensile button if found
        if "Start Tensile Testing" in updated_script:
            matches = pattern_tensile.findall(updated_script)
            for match in matches:
                idx = updated_script.find(match)
                if idx >= 11 and "if (false)" in updated_script[idx-15:idx]:
                    continue
                updated_script = updated_script.replace(match, f"if (false) {match}")
                
        if updated_script != script:
            cs.script = updated_script
            cs.save(ignore_permissions=True)
            frappe.db.commit()

    frappe.clear_cache()
