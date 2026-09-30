# -*- coding: utf-8 -*-
"""Fix Quality Checking form layout: restore 2-column header and group Colour Spectrum fields."""

from __future__ import annotations

import os

import frappe

PARENT_DTYPE = "Quality Checking"

# Layout fieldnames we may need to create
LAYOUT_FIELDS = [
	{"fieldname": "section_details", "label": "", "fieldtype": "Section Break"},
	{"fieldname": "cb_details_1", "label": "", "fieldtype": "Column Break"},
	{"fieldname": "cb_main", "label": "", "fieldtype": "Column Break"},
	{"fieldname": "section_tensile", "label": "Tensile Testing", "fieldtype": "Section Break"},
	{"fieldname": "cb_tensile_1", "label": "", "fieldtype": "Column Break"},
	{"fieldname": "colour_spectrum_sb", "label": "Colour Spectrum Test", "fieldtype": "Section Break"},
	{"fieldname": "colour_spectrum_summary_sb", "label": "Colour Spectrum Summary", "fieldtype": "Section Break"},
	{"fieldname": "cs_cb_1", "label": "", "fieldtype": "Column Break"},
	{"fieldname": "cs_cb_2", "label": "", "fieldtype": "Column Break"},
	{"fieldname": "cs_cb_3", "label": "", "fieldtype": "Column Break"},
	{"fieldname": "cs_cb_4", "label": "", "fieldtype": "Column Break"},
	{"fieldname": "section_gsm", "label": "GSM Testing", "fieldtype": "Section Break"},
	{"fieldname": "section_gsm_summary", "label": "GSM Summary", "fieldtype": "Section Break"},
	{"fieldname": "cb_gsm_summary", "label": "", "fieldtype": "Column Break"},
	{"fieldname": "section_template_details", "label": "Template Details", "fieldtype": "Section Break"},
]

# Canonical field order. Missing fields are skipped; unknown fields keep relative order at the end.
DESIRED_ORDER = [
	# Header details — 2 columns (always visible)
	"naming_series",
	"section_details",
	"testing_type",
	"date",
	"batch_no",
	"order_code",
	"cb_details_1",
	"gsm_production_entry",
	"gsm",
	# Colour Spectrum Test (table full width)
	"colour_spectrum_sb",
	"colour_spectrum_sections",
	# Colour Spectrum Summary — 5 columns
	"colour_spectrum_summary_sb",
	"cs_pass_d65",
	"cs_cb_1",
	"cs_pass_tl84",
	"cs_cb_2",
	"cs_pass_uv",
	"cs_cb_3",
	"cs_pass_fl_tfl",
	"cs_cb_4",
	"cs_pass_cwf",
	# Quality Checking — 2 columns
	"section_main",
	"shaft_production_run",
	"unit",
	"shift",
	"roll_no",
	"cb_main",
	"fabric_type",
	"quality",
	"color",
	# Template Details
	"section_template_details",
	"test_method",
	"cutting_template_width",
	"cb_tensile_1",
	"cutting_template_height",
	# Tensile Table
	"section_tensile",
	"tensile_total_samples",
	"tensile_sections",
	# GSM grid (full width)
	"section_gsm",
	"custom_html_grid",
	"custom_gsm_grid_html",
	"sections",
	# GSM Summary
	"section_gsm_summary",
	"gsm_overall_result",
	"gsm_total_samples",
	"cb_gsm_summary",
	"gsm_pass_samples",
	"gsm_fail_samples",
]

COLOUR_DEPENDS = "eval:doc.testing_type=='Colour Spectrum'"
TENSILE_DEPENDS = "eval:doc.testing_type=='Tensile Testing'"
GSM_DEPENDS = "eval:doc.testing_type!='Tensile Testing' && doc.testing_type!='Colour Spectrum'"
CUTTING_DEPENDS = (
	"eval:in_list(['Tensile Testing','Patty Cutting GSM Test'], doc.testing_type)"
)

FIELD_DEPENDS = {
	"section_tensile": TENSILE_DEPENDS,
	"test_method": TENSILE_DEPENDS,
	"tensile_sections": TENSILE_DEPENDS,
	"tensile_total_samples": TENSILE_DEPENDS,
	"cb_tensile_1": TENSILE_DEPENDS,
	"cutting_template_width": CUTTING_DEPENDS,
	"cutting_template_height": CUTTING_DEPENDS,
	"colour_spectrum_sb": COLOUR_DEPENDS,
	"colour_spectrum_sections": COLOUR_DEPENDS,
	"colour_spectrum_summary_sb": COLOUR_DEPENDS,
	"cs_pass_d65": COLOUR_DEPENDS,
	"cs_pass_tl84": COLOUR_DEPENDS,
	"cs_pass_uv": COLOUR_DEPENDS,
	"cs_pass_fl_tfl": COLOUR_DEPENDS,
	"cs_pass_cwf": COLOUR_DEPENDS,
	"cs_cb_1": COLOUR_DEPENDS,
	"cs_cb_2": COLOUR_DEPENDS,
	"cs_cb_3": COLOUR_DEPENDS,
	"cs_cb_4": COLOUR_DEPENDS,
	"section_gsm": GSM_DEPENDS,
	"section_gsm_summary": GSM_DEPENDS,
	"custom_html_grid": GSM_DEPENDS,
	"custom_gsm_grid_html": GSM_DEPENDS,
	"gsm_total_samples": GSM_DEPENDS,
	"gsm_pass_samples": GSM_DEPENDS,
	"gsm_fail_samples": GSM_DEPENDS,
	"gsm_overall_result": GSM_DEPENDS,
	"cb_gsm_summary": GSM_DEPENDS,
	"gsm": GSM_DEPENDS,
	"section_template_details": CUTTING_DEPENDS,
}


def execute():
	if not frappe.db.exists("DocType", PARENT_DTYPE):
		return

	_ensure_layout_fields()
	_reorder_and_configure()
	_sync_client_scripts()
	frappe.clear_cache(doctype=PARENT_DTYPE)
	frappe.db.commit()


def _ensure_layout_fields():
	for field in LAYOUT_FIELDS:
		if frappe.db.exists("DocField", {"parent": PARENT_DTYPE, "fieldname": field["fieldname"]}):
			continue
		frappe.get_doc(
			{
				"doctype": "DocField",
				"parent": PARENT_DTYPE,
				"parenttype": "DocType",
				"parentfield": "fields",
				"fieldname": field["fieldname"],
				"label": field["label"],
				"fieldtype": field["fieldtype"],
			}
		).insert(ignore_permissions=True)


def _reorder_and_configure():
	dt = frappe.get_doc("DocType", PARENT_DTYPE)
	by_name = {f.fieldname: f for f in dt.fields}

	# Avoid duplicate section title on the table itself
	table_field = by_name.get("colour_spectrum_sections")
	if table_field:
		table_field.label = ""

	# Ensure section labels are clean
	if by_name.get("colour_spectrum_sb"):
		by_name["colour_spectrum_sb"].label = "Colour Spectrum Test"
		by_name["colour_spectrum_sb"].collapsible = 0
	if by_name.get("colour_spectrum_summary_sb"):
		by_name["colour_spectrum_summary_sb"].label = "Colour Spectrum Summary"
		by_name["colour_spectrum_summary_sb"].collapsible = 0
	if by_name.get("section_main"):
		by_name["section_main"].label = "Quality Checking"
		by_name["section_main"].collapsible = 0
	if by_name.get("section_tensile"):
		by_name["section_tensile"].label = "Tensile Testing"
	if by_name.get("section_gsm"):
		by_name["section_gsm"].label = "GSM Testing"
	if by_name.get("section_details"):
		by_name["section_details"].label = ""
		by_name["section_details"].collapsible = 0
	if by_name.get("section_template_details"):
		by_name["section_template_details"].label = "Template Details"

	for old_field in ["gsm_total_sections", "gsm_pass_sections", "gsm_fail_sections"]:
		if by_name.get(old_field):
			by_name[old_field].hidden = 1

	# Column breaks must not carry labels (avoids phantom headings)
	for cb_name in (
		"cb_details_1",
		"cb_main",
		"cb_tensile_1",
		"cb_gsm_summary",
		"cs_cb_1",
		"cs_cb_2",
		"cs_cb_3",
		"cs_cb_4",
	):
		if by_name.get(cb_name):
			by_name[cb_name].label = ""

	for fieldname, depends_on in FIELD_DEPENDS.items():
		field = by_name.get(fieldname)
		if field:
			field.depends_on = depends_on

	order_map = {name: idx for idx, name in enumerate(DESIRED_ORDER)}
	known = [f for f in dt.fields if f.fieldname in order_map]
	unknown = [f for f in dt.fields if f.fieldname not in order_map]
	known.sort(key=lambda f: order_map[f.fieldname])
	# Keep unknown fields after known ones, preserving their relative idx
	unknown.sort(key=lambda f: f.idx or 0)
	dt.fields = known + unknown
	for i, df in enumerate(dt.fields):
		df.idx = i + 1

	dt.save(ignore_permissions=True)

	# Also stamp idx in DB directly (DocType save can leave stale idx on some sites)
	for i, df in enumerate(dt.fields):
		frappe.db.set_value("DocField", df.name, "idx", i + 1, update_modified=False)


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
					"module": "Quality",
					"script": script_content,
					"enabled": 1,
				}
			).insert(ignore_permissions=True)
