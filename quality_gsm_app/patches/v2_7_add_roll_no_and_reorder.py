import frappe
import os

def execute():
    PARENT_DTYPE = "Quality Checking"

    # 1. Add Roll No field
    if not frappe.db.exists("DocField", {"parent": PARENT_DTYPE, "fieldname": "roll_no"}):
        frappe.get_doc({
            "doctype": "DocField",
            "parent": PARENT_DTYPE,
            "parenttype": "DocType",
            "parentfield": "fields",
            "fieldname": "roll_no",
            "label": "Roll No",
            "fieldtype": "Data",
            "insert_after": "batch_no"
        }).insert(ignore_permissions=True)

    # 2. Reorder fields
    # Desired order: section_main, shaft_production_run, batch_no, roll_no, quality, custom_html_grid, sections
    doc = frappe.get_doc("DocType", PARENT_DTYPE)
    desired_order = [
        "section_main",
        "shaft_production_run",
        "batch_no",
        "roll_no",
        "quality",
        "custom_html_grid",
        "sections",
        "gsm_overall_result",
        "gsm_total_sections",
        "gsm_pass_sections",
        "gsm_fail_sections"
    ]
    order_map = {f: i for i, f in enumerate(desired_order)}

    def get_order(df):
        return order_map.get(df.fieldname, 999)

    doc.fields.sort(key=get_order)
    for i, df in enumerate(doc.fields):
        df.idx = i + 1
    doc.save(ignore_permissions=True)

    # 3. Update Print Format
    update_print_format(PARENT_DTYPE)

    # 4. Update Client Scripts (to get the larger font-size changes)
    update_client_scripts()

    frappe.clear_cache(doctype=PARENT_DTYPE)


def update_print_format(PARENT_DTYPE):
    name = "GSM Testing Report"
    html = """
<style>
  .gsm-report-container { font-family: Inter, sans-serif; color:#333; padding: 10px; }
  .gsm-header { text-align:center; margin-bottom:16px; border-bottom:2px solid #3498db; padding-bottom:8px; }
  .gsm-table { width:100%; border-collapse: collapse; margin: 14px 0 24px; font-size:10px; }
  .gsm-table th, .gsm-table td { border:1px solid #bdc3c7; padding:6px; text-align:center; }
  .gsm-table th { background:#f7f9f9; }
  .row-header { text-align:left !important; font-weight:700; background:#f8f9fa; }
  .highlight-avg { background:#ecf0f1; font-weight:700; }
  .pass-diff { background:#eafaf1; color:#1e8449; font-weight:700; }
  .fail-diff { background:#fdedec; color:#c0392b; font-weight:700; }
  .section-title { margin: 14px 0 6px; font-size: 14px; font-weight: 700; }
  .info-table { width: 100%; margin-bottom: 20px; font-size: 12px; }
  .info-table td { padding: 4px; }
  .info-label { font-weight: bold; }
</style>

<div class="gsm-report-container">
  <div class="gsm-header">
    <h2>GSM TESTING REPORT</h2>
    <div>Quality Checking: {{ doc.name }}</div>
  </div>

  <table class="info-table">
    <tr>
      <td><span class="info-label">Shaft Production Run:</span> {{ doc.shaft_production_run or "-" }}</td>
      <td><span class="info-label">Batch No:</span> {{ doc.batch_no or "-" }}</td>
    </tr>
    <tr>
      <td><span class="info-label">Roll No:</span> {{ doc.roll_no or "-" }}</td>
      <td><span class="info-label">Quality:</span> {{ doc.quality or "-" }}</td>
    </tr>
    <tr>
      <td><span class="info-label">Date:</span> {{ doc.creation[:10] }}</td>
      <td><span class="info-label">Overall Result:</span> {{ doc.gsm_overall_result or "-" }}</td>
    </tr>
  </table>

  {% for row in doc.sections %}
    {% set q = (row.quality or doc.quality or '')|lower %}
    {% set limit = 5 if ('low' in q or 'lower' in q) else 3 %}
    <div class="section-title">
      Section {{ loop.index }} - Set GSM: {{ row.representative_gsm }} | Result: {{ row.section_result or "-" }} | Tolerance: &lt; {{ limit }}
    </div>

    <table class="gsm-table">
      <thead>
        <tr>
          <th>PROPERTIES</th>
          <th>SET GSM</th>
          {% for i in range(1, 26) %}<th>S{{ i }}</th>{% endfor %}
          <th>AVERAGE</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="row-header">GSM (ROW 1)</td>
          <td>{{ row.representative_gsm }}</td>
          {% for i in range(1, 26) %}<td>{{ row["r1_s" ~ i] }}</td>{% endfor %}
          <td class="highlight-avg">{{ row.r1_average }}</td>
        </tr>

        <tr>
          <td class="row-header">GSM (ROW 2)</td>
          <td>{{ row.representative_gsm }}</td>
          {% for i in range(1, 26) %}<td>{{ row["r2_s" ~ i] }}</td>{% endfor %}
          <td class="highlight-avg">{{ row.r2_average }}</td>
        </tr>

        <tr class="highlight-avg">
          <td class="row-header">COMBINED AVG</td>
          <td>-</td>
          {% for i in range(1, 26) %}<td>{{ row["s" ~ i ~ "_combined_avg"] }}</td>{% endfor %}
          <td>{{ row.grand_average_gsm }}</td>
        </tr>

        <tr>
          <td class="row-header">DIFF</td>
          <td>-</td>
          {% for i in range(1, 26) %}
            {% set d = row["s" ~ i ~ "_diff"] %}
            {% set cls = "pass-diff" if (d is not none and d|string != '' and (d|abs) < limit) else "fail-diff" %}
            <td class="{{ cls }}">{{ d }}</td>
          {% endfor %}
          <td>{{ row.section_result }}</td>
        </tr>
      </tbody>
    </table>
  {% endfor %}
</div>
"""

    if frappe.db.exists("Print Format", name):
        pf = frappe.get_doc("Print Format", name)
        pf.html = html
        pf.save(ignore_permissions=True)


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
