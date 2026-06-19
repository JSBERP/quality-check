# Server Script (DocType: Opportunity, Event: Before Save)

def safe_float(val):
    try:
        return float(val) if val else 0.0
    except (ValueError, TypeError):
        return 0.0

req = doc.custom_requirement
target_value = ''

if req == 'Non Woven Fabric':
    val = doc.custom_monthly_fabric_requirement_kg
    if val is not None and str(val).strip() != '':
        qty = safe_float(val)
        if qty < 1000:
            target_value = 'Below 1 Ton'
        elif 1000 <= qty <= 5000:
            target_value = '1-5 Ton'
        elif qty > 5000:
            target_value = 'Above 5 Ton'
elif req == 'Non Woven Fabric & Bag':
    val = doc.custom_monthly_fabric_need_kgs
    if val is not None and str(val).strip() != '':
        qty = safe_float(val)
        if qty < 1000:
            target_value = 'Below 1 Ton'
        elif 1000 <= qty <= 5000:
            target_value = '1-5 Ton'
        elif qty > 5000:
            target_value = 'Above 5 Ton'
else:
    target_value = ''

if target_value:
    # Match the database option casing dynamically
    meta = frappe.get_meta('Opportunity')
    field = meta.get_field('custom_order_type')
    if field and field.options:
        options = [opt.strip() for opt in field.options.split('\n') if opt.strip()]
        for opt in options:
            if opt.lower().replace(" ", "") == target_value.lower().replace(" ", ""):
                target_value = opt
                break

doc.custom_order_type = target_value
