import frappe
import os
import json

def execute(filters=None):
    if not filters:
        filters = {}

    # Read the query from the SQL file
    sql_path = os.path.join(os.path.dirname(__file__), 'requirement_report.sql')
    with open(sql_path, 'r') as f:
        query = f.read()

    def get_list_condition(field, column):
        val = filters.get(field)
        if not val:
            return ""
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except Exception:
                val = [v.strip() for v in val.split(",")]
        
        if not isinstance(val, list) or not val:
            return ""
            
        escaped_vals = ", ".join([frappe.db.escape(v) for v in val])
        return f" AND {column} IN ({escaped_vals}) "

    # Process MultiSelect lists for city and state safely
    city_cond = get_list_condition("city", "lead.city")
    state_cond = get_list_condition("state", "lead.state")
    
    combined_cond = f"{city_cond} {state_cond}"
    
    # Inject the multi-select conditions into the placeholder in the SQL string
    query = query.replace("/*city_condition*/", combined_cond)

    # Execute the query
    data = frappe.db.sql(query, filters, as_dict=False)
    
    # Extract columns exactly as defined in the .sql file
    columns = [desc[0] for desc in frappe.db.get_description()]

    # Find column indices dynamically to filter rows
    fabric_req_idx = -1
    fabric_need_idx = -1
    bag_qty_idx = -1
    bag_need_idx = -1

    for i, col in enumerate(columns):
        col_clean = col.split(":")[0].strip().lower()
        if col_clean == "fabric requirement":
            fabric_req_idx = i
        elif col_clean == "fabric need":
            fabric_need_idx = i
        elif col_clean == "bag quantity":
            bag_qty_idx = i
        elif col_clean == "bag need":
            bag_need_idx = i

    def is_zero_or_empty(val):
        if val is None:
            return True
        val_str = str(val).strip()
        if not val_str or val_str == "0" or val_str == "0.0":
            return True
        try:
            return float(val_str) == 0.0
        except ValueError:
            return False

    filtered_data = []
    for row in data:
        val_fabric_req = row[fabric_req_idx] if fabric_req_idx != -1 else "0"
        val_fabric_need = row[fabric_need_idx] if fabric_need_idx != -1 else "0"
        val_bag_qty = row[bag_qty_idx] if bag_qty_idx != -1 else "0"
        val_bag_need = row[bag_need_idx] if bag_need_idx != -1 else "0"
        
        # Exclude the row entirely if all four fields are zero or empty
        if (is_zero_or_empty(val_fabric_req) and 
            is_zero_or_empty(val_fabric_need) and 
            is_zero_or_empty(val_bag_qty) and 
            is_zero_or_empty(val_bag_need)):
            continue
            
        filtered_data.append(row)

    return columns, filtered_data

