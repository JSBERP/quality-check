import frappe
from frappe.utils import cint, flt


def _row_gsm(row) -> float:
	gsm = None
	if hasattr(row, "gsm"):
		gsm = getattr(row, "gsm", None)
	elif isinstance(row, dict):
		gsm = row.get("gsm")
	if gsm in (None, "") and hasattr(row, "sticker_gsm"):
		gsm = getattr(row, "sticker_gsm", None)
	if gsm in (None, "") and hasattr(row, "target_gsm"):
		gsm = getattr(row, "target_gsm", None)
	try:
		return flt(gsm)
	except Exception:
		return 0.0


def _row_batch(row) -> str:
	if hasattr(row, "batch_no"):
		return str(getattr(row, "batch_no", None) or "").strip()
	if isinstance(row, dict):
		return str(row.get("batch_no") or "").strip()
	return ""


def _row_roll_no(row) -> int:
	roll = 0
	if hasattr(row, "roll_no"):
		roll = cint(getattr(row, "roll_no", None) or 0)
	elif isinstance(row, dict):
		roll = cint(row.get("roll_no") or 0)
	if roll:
		return roll
	batch = _row_batch(row)
	if "/" in batch:
		return cint(batch.split("/")[-1])
	return 0


def _batch_matches(row_batch: str, target: str) -> bool:
	if not target:
		return True
	row_batch = (row_batch or "").strip()
	target = (target or "").strip()
	if not row_batch:
		return False
	return row_batch == target or row_batch.startswith(target + "/") or target.startswith(row_batch + "/")


def _row_skipped(row) -> bool:
	wasted = 0
	bundle = 0
	if hasattr(row, "is_wasted"):
		wasted = cint(getattr(row, "is_wasted", 0) or 0)
	elif isinstance(row, dict):
		wasted = cint(row.get("is_wasted") or 0)
	if hasattr(row, "is_bundle_row"):
		bundle = cint(getattr(row, "is_bundle_row", 0) or 0)
	elif isinstance(row, dict):
		bundle = cint(row.get("is_bundle_row") or 0)
	return bool(wasted or bundle)


def _one_gsm(values):
	uniq = []
	for v in values or []:
		gsm = flt(v)
		if gsm > 0 and gsm not in uniq:
			uniq.append(gsm)
	return uniq[:1]


def _collect_gsm_from_rows(rows, target_batch: str, target_roll: int):
	exact = []
	related = []
	all_values = []
	for row in rows or []:
		if _row_skipped(row):
			continue
		gsm = _row_gsm(row)
		if gsm <= 0:
			continue
		all_values.append(gsm)
		row_batch = _row_batch(row)
		row_roll = _row_roll_no(row)
		if target_batch:
			if row_batch == target_batch:
				exact.append(gsm)
			elif _batch_matches(row_batch, target_batch):
				related.append(gsm)
		elif target_roll and row_roll == target_roll:
			# Roll numbers restart per job (50 GSM roll 1 and 60 GSM roll 1).
			# Without a batch, do not collect every job's matching roll.
			exact.append(gsm)
	if target_batch:
		return [v for v in (exact or related) if v > 0]
	if target_roll:
		return _one_gsm(exact)
	return [v for v in all_values if v > 0]


@frappe.whitelist()
def get_unique_gsm_values(shaft_production_run: str, batch_no: str = None, roll_no=None, gsm=None):
	if not shaft_production_run:
		return []

	# Fast path: caller already knows the exact GSM (e.g. redirected from GSM Production Entry).
	# Skip the shaft scan entirely — return that single value so exactly 1 section is built.
	gsm_direct = flt(gsm) if gsm not in (None, "") else 0.0
	if gsm_direct > 0:
		return [gsm_direct]

	doc = frappe.get_doc("Shaft Production Run", shaft_production_run)
	target_batch = (batch_no or "").strip()
	target_roll = cint(roll_no)

	# Production rolls only — do not pull every job GSM on the shaft.
	items = getattr(doc, "items", None) or []
	item_values = _collect_gsm_from_rows(items, target_batch, target_roll)
	if item_values:
		return _one_gsm(item_values)

	# Rolls exist but none matched this batch — do not fall back to shaft_jobs (50 + 60).
	if items:
		return []

	if not (target_batch or target_roll):
		return []

	matched = []
	for df in doc.meta.get_table_fields():
		if df.fieldname == "items":
			continue
		matched.extend(_collect_gsm_from_rows(getattr(doc, df.fieldname, None) or [], target_batch, target_roll))
	return _one_gsm(matched)


@frappe.whitelist()
def get_batches_from_shaft(shaft_production_run: str):
	if not shaft_production_run:
		return []

	doc = frappe.get_doc("Shaft Production Run", shaft_production_run)
	batches = []
	if hasattr(doc, "items") and doc.items:
		for row in doc.items:
			if cint(getattr(row, "is_wasted", 0) or 0) or cint(getattr(row, "is_bundle_row", 0) or 0):
				continue
			batch = _row_batch(row)
			if batch:
				batches.append(batch)
	return sorted(set(batches))


@frappe.whitelist()
def create_quality_checking_from_shaft(
	shaft_production_run: str, batch_no: str = None, testing_type: str = "Round Cutting GSM Test", roll_no=None, gsm=None
):
	if not shaft_production_run:
		frappe.throw("Missing shaft_production_run")

	shaft = frappe.get_doc("Shaft Production Run", shaft_production_run)
	# Pass gsm through so a GSM Production Entry redirect bypasses the full shaft scan.
	gsm_values = get_unique_gsm_values(shaft_production_run, batch_no=batch_no, roll_no=roll_no, gsm=gsm)

	if testing_type in ("Round Cutting GSM Test", "Patty Cutting GSM Test"):
		if not (batch_no or roll_no):
			frappe.throw("Select a Batch No so only that roll's GSM table is created.")
		if not gsm_values:
			frappe.throw("No GSM values found for the selected batch.")

	qc = frappe.new_doc("Quality Checking")
	if not hasattr(qc, "testing_type"):
		try:
			from quality_gsm_app.patches.v2_10_add_tensile_testing import execute

			execute()
			dt = frappe.get_doc("DocType", "Quality Checking")
			dt.save(ignore_permissions=True)
			frappe.db.commit()
			frappe.clear_cache(doctype="Quality Checking")
			qc = frappe.new_doc("Quality Checking")
		except Exception as e:
			frappe.log_error("Failed to run Tensile patch dynamically", str(e))

	if hasattr(qc, "testing_type"):
		qc.testing_type = testing_type

	qc.shaft_production_run = shaft.name
	qc.batch_no = (batch_no or "").strip() or None
	qc.quality = getattr(shaft, "quality", None)
	qc.order_code = getattr(shaft, "custom_order_code", None)
	qc.unit = getattr(shaft, "custom_unit", None)
	qc.shift = getattr(shaft, "shift", None)

	color_val = getattr(shaft, "custom_color", None) or getattr(shaft, "color", None)
	qc.color = color_val

	run_date_val = getattr(shaft, "run_date", None)
	if run_date_val:
		qc.date = run_date_val

	prod_plan_id = getattr(shaft, "production_plan", None)
	if prod_plan_id:
		try:
			prod_plan = frappe.get_doc("Production Plan", prod_plan_id)
			qc.fabric_type = getattr(prod_plan, "custom_fabric_type", None)
		except Exception:
			pass

	for df in shaft.meta.get_table_fields():
		for row in getattr(shaft, df.fieldname, None) or []:
			if batch_no and not _batch_matches(_row_batch(row), batch_no):
				continue
			if qc.quality in (None, "") and getattr(row, "quality", None):
				qc.quality = row.quality
			if not qc.color and getattr(row, "color", None):
				qc.color = row.color
			if not qc.color and getattr(row, "custom_color", None):
				qc.color = row.custom_color
			if not cint(getattr(qc, "roll_no", 0) or 0):
				qc.roll_no = _row_roll_no(row) or roll_no
			if qc.quality and qc.color:
				break

	if not cint(getattr(qc, "roll_no", 0) or 0) and qc.batch_no and "/" in str(qc.batch_no):
		qc.roll_no = cint(str(qc.batch_no).split("/")[-1])

	if gsm_values and qc.meta.has_field("gsm"):
		qc.gsm = gsm_values[0]

	if testing_type in ("Round Cutting GSM Test", "Patty Cutting GSM Test", "GSM Testing"):
		for gsm in gsm_values[:1]:
			child = qc.append("sections", {})
			child.representative_gsm = gsm
			child.quality = qc.quality

	unit_val_clean = str(qc.unit or "").lower().replace(" ", "")
	valid_units = ["unit1", "unit2", "unit3", "unit4"]
	if unit_val_clean not in valid_units:
		frappe.throw("Quality Testing is only applicable for Unit 1, Unit 2, Unit 3, and Unit 4.")

	unit_map = {"unit1": "U1", "unit2": "U2", "unit3": "U3", "unit4": "U4"}
	u = unit_map.get(unit_val_clean, "U1")
	if testing_type == "Tensile Testing":
		prefix = "TT"
	elif testing_type == "Patty Cutting GSM Test":
		prefix = "PGSM"
	elif testing_type == "Colour Spectrum":
		prefix = "CS"
	else:
		prefix = "RGSM"
	qc.naming_series = f"JSB/{prefix}-{u}/26-27/.###"

	qc.insert(ignore_permissions=True)
	frappe.db.commit()
	return qc.name
