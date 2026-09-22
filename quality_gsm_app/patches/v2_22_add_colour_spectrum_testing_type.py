# -*- coding: utf-8 -*-
"""Add Colour Spectrum to Quality Checking.testing_type."""

from __future__ import annotations

import frappe

PARENT_DTYPE = "Quality Checking"
TESTING_TYPE_OPTIONS = (
	"Round Cutting GSM Test\nPatty Cutting GSM Test\nTensile Testing\nColour Spectrum"
)


def execute():
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
		frappe.clear_cache(doctype=PARENT_DTYPE)
		frappe.db.commit()
