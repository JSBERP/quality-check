# -*- coding: utf-8 -*-
"""Add Colour Spectrum Test child table, summary fields, and print format."""

from __future__ import annotations

import os

import frappe

PARENT_DTYPE = "Quality Checking"
CHILD_DTYPE = "Colour Spectrum Test Result"
PRINT_FORMAT_NAME = "Quality Testing Report"
TESTING_TYPE_OPTIONS = (
	"Round Cutting GSM Test\nPatty Cutting GSM Test\nTensile Testing\nColour Spectrum"
)
COLOUR_PARAMS = ("D-65", "TL-84", "UV", "FL / TFL", "CWF")
SAMPLE_OPTIONS = "\nPass\nFail"


def execute():
	_ensure_child_doctype()
	_ensure_parent_fields()
	_ensure_testing_type_options()
	_sync_client_scripts()
	_update_print_format()
	frappe.clear_cache(doctype=PARENT_DTYPE)
	frappe.clear_cache(doctype=CHILD_DTYPE)
	frappe.db.commit()


def _ensure_child_doctype():
	sample_fields = [
		{
			"fieldname": f"sample_{i}",
			"label": f"Sample {i}",
			"fieldtype": "Select",
			"options": SAMPLE_OPTIONS,
			"in_list_view": 1,
			"columns": 1,
		}
		for i in range(1, 11)
	]

	fields = [
		{
			"fieldname": "parameter",
			"label": "Parameter",
			"fieldtype": "Select",
			"options": "\n".join(COLOUR_PARAMS),
			"in_list_view": 1,
			"reqd": 1,
			"columns": 2,
		},
		*sample_fields,
		{
			"fieldname": "pass_count",
			"label": "Pass Count",
			"fieldtype": "Int",
			"read_only": 1,
			"in_list_view": 1,
			"columns": 1,
		},
	]

	if not frappe.db.exists("DocType", CHILD_DTYPE):
		frappe.get_doc(
			{
				"doctype": "DocType",
				"name": CHILD_DTYPE,
				"module": "Quality",
				"custom": 1,
				"istable": 1,
				"editable_grid": 1,
				"fields": fields,
			}
		).insert(ignore_permissions=True)
		return

	# Keep existing child schema in sync (add any missing sample columns).
	dt = frappe.get_doc("DocType", CHILD_DTYPE)
	existing = {f.fieldname for f in dt.fields}
	changed = False
	for field in fields:
		if field["fieldname"] in existing:
			continue
		dt.append("fields", field)
		changed = True
	if changed:
		dt.save(ignore_permissions=True)


def _ensure_parent_fields():
	if not frappe.db.exists("DocType", PARENT_DTYPE):
		return

	fields_to_add = [
		{
			"fieldname": "colour_spectrum_sb",
			"label": "Colour Spectrum Test",
			"fieldtype": "Section Break",
			"insert_after": "tensile_total_samples",
		},
		{
			"fieldname": "colour_spectrum_sections",
			"label": "Colour Spectrum Test",
			"fieldtype": "Table",
			"options": CHILD_DTYPE,
			"insert_after": "colour_spectrum_sb",
		},
		{
			"fieldname": "colour_spectrum_summary_sb",
			"label": "Colour Spectrum Summary",
			"fieldtype": "Section Break",
			"insert_after": "colour_spectrum_sections",
		},
		{
			"fieldname": "cs_pass_d65",
			"label": "D-65 Pass",
			"fieldtype": "Int",
			"read_only": 1,
			"default": "0",
			"insert_after": "colour_spectrum_summary_sb",
		},
		{
			"fieldname": "cs_pass_tl84",
			"label": "TL-84 Pass",
			"fieldtype": "Int",
			"read_only": 1,
			"default": "0",
			"insert_after": "cs_pass_d65",
		},
		{
			"fieldname": "cs_pass_uv",
			"label": "UV Pass",
			"fieldtype": "Int",
			"read_only": 1,
			"default": "0",
			"insert_after": "cs_pass_tl84",
		},
		{
			"fieldname": "cs_pass_fl_tfl",
			"label": "FL / TFL Pass",
			"fieldtype": "Int",
			"read_only": 1,
			"default": "0",
			"insert_after": "cs_pass_uv",
		},
		{
			"fieldname": "cs_pass_cwf",
			"label": "CWF Pass",
			"fieldtype": "Int",
			"read_only": 1,
			"default": "0",
			"insert_after": "cs_pass_fl_tfl",
		},
	]

	for field in fields_to_add:
		if frappe.db.exists("DocField", {"parent": PARENT_DTYPE, "fieldname": field["fieldname"]}):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "DocField",
				"parent": PARENT_DTYPE,
				"parenttype": "DocType",
				"parentfield": "fields",
				"fieldname": field["fieldname"],
				"label": field["label"],
				"fieldtype": field["fieldtype"],
				"insert_after": field["insert_after"],
			}
		)
		if "options" in field:
			doc.options = field["options"]
		if "read_only" in field:
			doc.read_only = field["read_only"]
		if "default" in field:
			doc.default = field["default"]
		doc.insert(ignore_permissions=True)

	dt = frappe.get_doc("DocType", PARENT_DTYPE)
	dt.save(ignore_permissions=True)


def _ensure_testing_type_options():
	if not frappe.db.exists("DocType", PARENT_DTYPE):
		return
	dt = frappe.get_doc("DocType", PARENT_DTYPE)
	changed = False
	for field in dt.fields:
		if field.fieldname != "testing_type":
			continue
		if field.options != TESTING_TYPE_OPTIONS:
			field.options = TESTING_TYPE_OPTIONS
			changed = True
		break
	if changed:
		dt.save(ignore_permissions=True)


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


def _update_print_format():
	app_path = frappe.get_app_path("quality_gsm_app")
	html_path = os.path.normpath(os.path.join(app_path, "..", "quality_checking_print_format.html"))
	if not os.path.exists(html_path):
		html_path = os.path.join(app_path, "quality_checking_print_format.html")
	if not os.path.exists(html_path):
		return

	with open(html_path, "r", encoding="utf-8") as f:
		html = f.read()

	if frappe.db.exists("Print Format", PRINT_FORMAT_NAME):
		pf = frappe.get_doc("Print Format", PRINT_FORMAT_NAME)
		pf.doc_type = PARENT_DTYPE
		pf.print_format_type = "Jinja"
		pf.html = html
		pf.disabled = 0
		pf.save(ignore_permissions=True)
		return

	frappe.get_doc(
		{
			"doctype": "Print Format",
			"name": PRINT_FORMAT_NAME,
			"doc_type": PARENT_DTYPE,
			"print_format_type": "Jinja",
			"html": html,
			"disabled": 0,
		}
	).insert(ignore_permissions=True)
