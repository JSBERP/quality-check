import frappe

def execute():
    if frappe.db.exists("DocType", "Quality Checking"):
        doc = frappe.get_doc("DocType", "Quality Checking")
        
        updated = False
        for field in doc.fields:
            if field.fieldname == "testing_type":
                # Update the options to include the new ones
                field.options = "Round Cutting GSM Test\nPatty Cutting GSM Test\nTensile Testing"
                
                if field.default == "GSM Testing":
                    field.default = "Round Cutting GSM Test"
                    
                updated = True
                break
                
        if updated:
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            
            # Since the options changed, we should also update any existing records that have "GSM Testing"
            frappe.db.sql("""
                UPDATE `tabQuality Checking`
                SET testing_type = 'Round Cutting GSM Test'
                WHERE testing_type = 'GSM Testing' OR testing_type IS NULL OR testing_type = ''
            """)
            frappe.db.commit()
