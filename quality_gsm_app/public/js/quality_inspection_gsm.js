["Quality Checking"].forEach((parentDoctype) => {
frappe.ui.form.on(parentDoctype, {
    setup(frm) {
        try {
            // Disable fetch_from for these fields so they can be set via route options or manually
            const fields_to_unfetch = [
                'batch_no', 'order_code', 'quality', 'unit', 'color', 'shift', 'roll_no', 'date'
            ];
            fields_to_unfetch.forEach(f => {
                if (frm.fields_dict[f] && frm.fields_dict[f].df) {
                    frm.fields_dict[f].df.fetch_from = '';
                }
            });
        } catch (e) {
            console.error("Error in setup:", e);
        }
    },
    refresh(frm) {
        if (frm.is_new() && frm.fields_dict.date && !frm.doc.date) {
            frm.set_value('date', frappe.datetime.get_today());
        }

        // Apply any pending route_options (set by GSM Production Entry redirect)
        // before deciding which tables to show, so testing_type is always known.
        if (frm.is_new() && frappe.route_options) {
            const opts = frappe.route_options;
            ['testing_type','batch_no','roll_no','shaft_production_run',
             'gsm_production_entry','gsm','set_gsm','target_gsm','order_code','quality','unit',
             'color','shift','date'].forEach(f => {
                if (opts[f] !== undefined && opts[f] !== "" && !frm.doc[f]) {
                    frm.doc[f] = opts[f];
                }
            });
        }

        toggle_testing_type_fields(frm);
        if (frm.is_new()) {
            set_auto_naming_series(frm);
        }

        // Tensile / Colour Spectrum: never build GSM sample tables.
        if (is_tensile_testing(frm) || is_colour_spectrum(frm)) {
            empty_gsm_grid(frm);
            if (is_colour_spectrum(frm)) {
                ensure_colour_spectrum_rows(frm);
                recalc_colour_spectrum_summary(frm);
            }
            return;
        }

        // GSM tests: never leave the tensile / colour spectrum grids visible.
        hide_tensile_grid(frm);
        hide_colour_spectrum_grid(frm);

        add_load_gsm_button(frm);

        const sectionsField = get_sections_field(frm);
        const hasSections = !!(sectionsField && (frm.doc[sectionsField] || []).length);

        if (frm.is_new() && frm.doc.shaft_production_run && !hasSections) {
            // Only auto-load GSM sections when NOT tensile / colour spectrum
            if (!is_tensile_testing(frm) && !is_colour_spectrum(frm) && (frm.doc.batch_no || cint(frm.doc.roll_no))) {
                load_gsm_sections_for_batch(frm);
            }
        } else if (hasSections && (frm.doc.batch_no || cint(frm.doc.roll_no))) {
            filter_existing_sections_to_batch(frm);
        } else {
            recalc_all_sections(frm);
            render_custom_html_grid(frm);
        }
    },
    shaft_production_run(frm) {
        if (!frm.doc.shaft_production_run) {
            return;
        }
        frappe.model.with_doc('Shaft Production Run', frm.doc.shaft_production_run, () => {
            const doc = frappe.model.get_doc('Shaft Production Run', frm.doc.shaft_production_run);
            if (!doc) {
                return;
            }
            const fillIfEmpty = (field, value) => {
                if (value && !frm.doc[field]) {
                    frm.set_value(field, value);
                }
            };
            fillIfEmpty('order_code', doc.custom_order_code || doc.order_code);
            fillIfEmpty('unit', doc.custom_unit || doc.unit);
            fillIfEmpty('shift', doc.shift);
            fillIfEmpty('date', doc.run_date);
            fillIfEmpty('quality', doc.quality);
            fillIfEmpty('color', doc.custom_color || doc.color);
            // Do not copy header batch_no / roll_no — those come from the selected roll.
        });
    },
    gsm_production_entry(frm) {
        if (!frm.doc.gsm_production_entry) {
            return;
        }
        frappe.model.with_doc('GSM Production Entry', frm.doc.gsm_production_entry, () => {
            const doc = frappe.model.get_doc('GSM Production Entry', frm.doc.gsm_production_entry);
            if (!doc) {
                return;
            }
            const fillIfEmpty = (field, value) => {
                if (value && !frm.doc[field]) {
                    frm.set_value(field, value);
                }
            };
            fillIfEmpty('order_code', doc.order_code);
            fillIfEmpty('quality', doc.quality);
            fillIfEmpty('unit', doc.unit);
            fillIfEmpty('color', doc.color);
            fillIfEmpty('shift', doc.shift);
            fillIfEmpty('date', doc.run_date);
            // Keep the selected roll batch — do not overwrite from the session header.
        });
    },
    testing_type(frm) {
        toggle_testing_type_fields(frm);
        set_auto_naming_series(frm);
        if (is_tensile_testing(frm) || is_colour_spectrum(frm)) {
            empty_gsm_grid(frm);
            if (is_colour_spectrum(frm)) {
                ensure_colour_spectrum_rows(frm);
                recalc_colour_spectrum_summary(frm);
            }
        } else if (frm.doc.shaft_production_run && (frm.doc.batch_no || cint(frm.doc.roll_no))) {
            const sectionsField = get_sections_field(frm);
            if (sectionsField && !(frm.doc[sectionsField] || []).length) {
                load_gsm_sections_for_batch(frm);
            } else {
                render_custom_html_grid(frm);
            }
        }
    },
    unit(frm) {
        if (frm.is_new()) {
            set_auto_naming_series(frm);
        }
    },
    validate(frm) {
        const unit_val_clean = (frm.doc.unit || "").toLowerCase().replace(/ /g, "");
        const valid_units = ["unit1", "unit2", "unit3", "unit4"];
        if (!valid_units.includes(unit_val_clean)) {
            frappe.msgprint(__("Quality Testing is only applicable for Unit 1, Unit 2, Unit 3, and Unit 4."));
            frappe.validated = false;
        }
        if (is_colour_spectrum(frm)) {
            recalc_colour_spectrum_summary(frm);
        } else {
            recalc_all_sections(frm);
        }
    },
    colour_spectrum_sections_remove(frm) {
        recalc_colour_spectrum_summary(frm);
    },
    colour_spectrum_sections_add(frm) {
        recalc_colour_spectrum_summary(frm);
    },
    quality(frm) {
        const sectionsField = get_sections_field(frm);
        (frm.doc[sectionsField] || []).forEach((row) => {
            if (!row.quality) {
                frappe.model.set_value(row.doctype, row.name, "quality", frm.doc.quality || "");
            }
        });
        if (!is_tensile_testing(frm) && !is_colour_spectrum(frm)) {
            recalc_all_sections(frm);
            render_custom_html_grid(frm);
        } else {
            empty_gsm_grid(frm);
        }
    }
});
});

frappe.ui.form.on("Tensile Testing Result", {
    sample_1: calc_tensile_row,
    sample_2: calc_tensile_row,
    sample_3: calc_tensile_row,
    sample_4: calc_tensile_row,
    sample_5: calc_tensile_row,
    tensile_sections_remove: function(frm) {
        recalc_tensile_total_samples(frm);
    }
});

const COLOUR_SPECTRUM_SAMPLE_FIELDS = [
    "sample_1", "sample_2", "sample_3", "sample_4", "sample_5",
    "sample_6", "sample_7", "sample_8", "sample_9", "sample_10"
];

const COLOUR_SPECTRUM_PARAMS = ["D-65", "TL-84", "UV", "FL / TFL", "CWF"];

const COLOUR_SPECTRUM_PASS_FIELD_MAP = {
    "D-65": "cs_pass_d65",
    "TL-84": "cs_pass_tl84",
    "UV": "cs_pass_uv",
    "FL / TFL": "cs_pass_fl_tfl",
    "CWF": "cs_pass_cwf"
};

frappe.ui.form.on("Colour Spectrum Test Result", {
    sample_1: calc_colour_spectrum_row,
    sample_2: calc_colour_spectrum_row,
    sample_3: calc_colour_spectrum_row,
    sample_4: calc_colour_spectrum_row,
    sample_5: calc_colour_spectrum_row,
    sample_6: calc_colour_spectrum_row,
    sample_7: calc_colour_spectrum_row,
    sample_8: calc_colour_spectrum_row,
    sample_9: calc_colour_spectrum_row,
    sample_10: calc_colour_spectrum_row,
    parameter: calc_colour_spectrum_row,
    colour_spectrum_sections_remove: function(frm) {
        recalc_colour_spectrum_summary(frm);
    }
});

function calc_colour_spectrum_row(frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);
    let passCount = 0;
    COLOUR_SPECTRUM_SAMPLE_FIELDS.forEach((f) => {
        if (String(row[f] || "").toLowerCase() === "pass") {
            passCount += 1;
        }
    });
    frappe.model.set_value(cdt, cdn, "pass_count", passCount);
    recalc_colour_spectrum_summary(frm);
}

function recalc_colour_spectrum_summary(frm) {
    const totals = {
        "D-65": 0,
        "TL-84": 0,
        "UV": 0,
        "FL / TFL": 0,
        "CWF": 0
    };
    (frm.doc.colour_spectrum_sections || []).forEach((row) => {
        const key = row.parameter;
        if (!(key in totals)) {
            return;
        }
        let passCount = 0;
        COLOUR_SPECTRUM_SAMPLE_FIELDS.forEach((f) => {
            if (String(row[f] || "").toLowerCase() === "pass") {
                passCount += 1;
            }
        });
        row.pass_count = passCount;
        totals[key] = passCount;
    });
    Object.keys(COLOUR_SPECTRUM_PASS_FIELD_MAP).forEach((param) => {
        safe_set_value(frm, COLOUR_SPECTRUM_PASS_FIELD_MAP[param], totals[param] || 0);
    });
}

function ensure_colour_spectrum_rows(frm) {
    if (!frm.fields_dict.colour_spectrum_sections) {
        return;
    }
    const rows = frm.doc.colour_spectrum_sections || [];
    const existing = new Set(rows.map((r) => r.parameter).filter(Boolean));
    let added = false;
    COLOUR_SPECTRUM_PARAMS.forEach((param) => {
        if (existing.has(param)) {
            return;
        }
        const row = frm.add_child("colour_spectrum_sections");
        row.parameter = param;
        row.pass_count = 0;
        added = true;
    });
    if (added) {
        frm.refresh_field("colour_spectrum_sections");
    }
}

function is_colour_spectrum(frm) {
    return String(frm.doc.testing_type || "").toLowerCase().includes("colour spectrum");
}

function hide_colour_spectrum_grid(frm) {
    [
        "colour_spectrum_sb",
        "colour_spectrum_sections",
        "colour_spectrum_summary_sb",
        "cs_pass_d65",
        "cs_pass_tl84",
        "cs_pass_uv",
        "cs_pass_fl_tfl",
        "cs_pass_cwf"
    ].forEach((fn) => {
        if (!frm.fields_dict[fn]) {
            return;
        }
        frm.toggle_display(fn, 0);
        frm.set_df_property(fn, "hidden", 1);
        if (frm.fields_dict[fn].$wrapper) {
            frm.fields_dict[fn].$wrapper.hide();
        }
    });
}

function calc_tensile_row(frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);
    let total = 0;
    let count = 0;
    ['sample_1', 'sample_2', 'sample_3', 'sample_4', 'sample_5'].forEach(f => {
        if (row[f] !== undefined && row[f] !== null && row[f] !== '') {
            total += flt(row[f]);
            count++;
        }
    });
    const avg = count > 0 ? total / count : 0;
    frappe.model.set_value(cdt, cdn, 'average', avg);
    
    recalc_tensile_total_samples(frm);
}

function recalc_tensile_total_samples(frm) {
    let count = 0;
    (frm.doc.tensile_sections || []).forEach(row => {
        ['sample_1', 'sample_2', 'sample_3', 'sample_4', 'sample_5'].forEach(f => {
            if (row[f] !== undefined && row[f] !== null && row[f] !== '') count++;
        });
    });
    safe_set_value(frm, 'tensile_total_samples', count);
}

function is_tensile_testing(frm) {
    return String(frm.doc.testing_type || "").toLowerCase().includes("tensile");
}

function is_gsm_testing(frm) {
    return !is_tensile_testing(frm) && !is_colour_spectrum(frm);
}

function selected_gsm(frm) {
    const opts = (typeof frappe !== "undefined" && frappe.route_options) || {};
    return flt(
        frm.doc.gsm ||
        frm.doc.set_gsm ||
        frm.doc.target_gsm ||
        opts.gsm ||
        opts.set_gsm ||
        opts.target_gsm ||
        frm._qc_target_gsm
    );
}

function hide_tensile_grid(frm) {
    ["tensile_sections", "tensile_total_samples", "test_method"].forEach((fn) => {
        if (!frm.fields_dict[fn]) {
            return;
        }
        frm.toggle_display(fn, 0);
        frm.set_df_property(fn, "hidden", 1);
        if (frm.fields_dict[fn].$wrapper) {
            frm.fields_dict[fn].$wrapper.hide();
        }
    });
}

function empty_gsm_grid(frm) {
    ["custom_html_grid", "custom_gsm_grid_html"].forEach((fn) => {
        if (frm.fields_dict[fn] && frm.fields_dict[fn].$wrapper) {
            frm.fields_dict[fn].$wrapper.empty();
        }
        if (frm.fields_dict[fn]) {
            frm.set_df_property(fn, "hidden", 1);
        }
    });
}

function gsm_query_args(frm) {
    return {
        shaft_production_run: frm.doc.shaft_production_run,
        batch_no: frm.doc.batch_no || "",
        roll_no: frm.doc.roll_no || 0,
        gsm: selected_gsm(frm) || ""
    };
}

function parse_gsm_values(message) {
    const values = (message || []).map((v) => flt(v)).filter((v) => v > 0);
    return values.length ? [values[0]] : [];
}

function section_has_samples(row) {
    for (let i = 1; i <= 25; i++) {
        if (flt(row[`r1_s${i}`]) || flt(row[`r2_s${i}`])) {
            return true;
        }
    }
    return false;
}

function apply_gsm_sections(frm, values) {
    const sectionsField = get_sections_field(frm);
    if (!sectionsField) {
        return;
    }
    const gsm = selected_gsm(frm) || (values && values[0]);
    if (!gsm) {
        return;
    }
    frm._qc_target_gsm = gsm;
    if (frm.fields_dict.gsm) {
        frm.doc.gsm = gsm;
    }
    frm.clear_table(sectionsField);
    const row = frm.add_child(sectionsField);
    row.representative_gsm = gsm;
    row.quality = frm.doc.quality || "";
    frm.refresh_field(sectionsField);
    recalc_all_sections(frm);
    render_custom_html_grid(frm);
}

function load_gsm_sections_for_batch(frm) {
    if (is_tensile_testing(frm) || is_colour_spectrum(frm) || frm.__qc_sections_loading) {
        return;
    }
    if (!frm.doc.shaft_production_run || (!frm.doc.batch_no && !cint(frm.doc.roll_no))) {
        return;
    }
    const sectionsField = get_sections_field(frm);
    if (!sectionsField) {
        return;
    }
    frm.__qc_sections_loading = true;
    frappe.call({
        method: "quality_gsm_app.api.quality.get_unique_gsm_values",
        args: gsm_query_args(frm),
        callback: (r) => {
            frm.__qc_sections_loading = false;
            const values = parse_gsm_values(r.message);
            if (values.length) {
                apply_gsm_sections(frm, values);
            }
        },
        error: () => {
            frm.__qc_sections_loading = false;
        }
    });
}

function filter_existing_sections_to_batch(frm) {
    if (is_tensile_testing(frm) || is_colour_spectrum(frm) || frm.__qc_sections_filtering) {
        return;
    }
    if (!frm.doc.shaft_production_run || (!frm.doc.batch_no && !cint(frm.doc.roll_no))) {
        recalc_all_sections(frm);
        render_custom_html_grid(frm);
        return;
    }
    const filterKey = `${frm.doc.batch_no || ""}|${frm.doc.roll_no || 0}`;
    if (frm.__qc_filtered_for === filterKey && frm._qc_target_gsm) {
        recalc_all_sections(frm);
        render_custom_html_grid(frm);
        return;
    }
    frm.__qc_sections_filtering = true;
    frappe.call({
        method: "quality_gsm_app.api.quality.get_unique_gsm_values",
        args: gsm_query_args(frm),
        callback: (r) => {
            frm.__qc_sections_filtering = false;
            const values = parse_gsm_values(r.message);
            if (values.length) {
                frm._qc_target_gsm = selected_gsm(frm) || values[0];
                frm.__qc_filtered_for = `${frm.doc.batch_no || ""}|${frm.doc.roll_no || 0}`;
                const sectionsField = get_sections_field(frm);
                const rows = frm.doc[sectionsField] || [];
                const target = frm._qc_target_gsm;
                const remaining = rows.filter((row) => {
                    const match = Math.abs(flt(row.representative_gsm) - target) < 0.51;
                    if (frm.is_new()) {
                        return match;
                    }
                    return match || section_has_samples(row);
                });
                if (remaining.length !== rows.length) {
                    frm.doc[sectionsField] = remaining.length ? remaining : rows.slice(0, 1);
                    frm.refresh_field(sectionsField);
                }
            }
            recalc_all_sections(frm);
            render_custom_html_grid(frm);
        },
        error: () => {
            frm.__qc_sections_filtering = false;
            recalc_all_sections(frm);
            render_custom_html_grid(frm);
        }
    });
}

function toggle_testing_type_fields(frm) {
    const is_tensile = is_tensile_testing(frm);
    const is_colour = is_colour_spectrum(frm);
    const is_gsm = is_gsm_testing(frm);
    const is_patty = String(frm.doc.testing_type || "").toLowerCase().includes("patty");

    frm.toggle_display('test_method', is_tensile);
    frm.toggle_display('cutting_template_width', is_tensile || is_patty);
    frm.toggle_display('cutting_template_height', is_tensile || is_patty);
    frm.toggle_display('tensile_sections', is_tensile);
    frm.toggle_display('tensile_total_samples', is_tensile);
    frm.set_df_property('tensile_sections', 'hidden', is_tensile ? 0 : 1);
    frm.set_df_property('tensile_total_samples', 'hidden', is_tensile ? 0 : 1);
    if (frm.fields_dict.tensile_sections && frm.fields_dict.tensile_sections.$wrapper) {
        frm.fields_dict.tensile_sections.$wrapper.toggle(!!is_tensile);
    }

    // Colour Spectrum table + pass summaries
    [
        "colour_spectrum_sb",
        "colour_spectrum_sections",
        "colour_spectrum_summary_sb",
        "cs_pass_d65",
        "cs_pass_tl84",
        "cs_pass_uv",
        "cs_pass_fl_tfl",
        "cs_pass_cwf"
    ].forEach((fn) => {
        if (!frm.fields_dict[fn]) {
            return;
        }
        frm.toggle_display(fn, is_colour);
        frm.set_df_property(fn, "hidden", is_colour ? 0 : 1);
        if (frm.fields_dict[fn].$wrapper) {
            frm.fields_dict[fn].$wrapper.toggle(!!is_colour);
        }
    });

    frm.toggle_display('sections', is_gsm);
    frm.toggle_display('custom_gsm_grid_html', is_gsm);
    frm.toggle_display('custom_html_grid', is_gsm);
    frm.set_df_property('custom_gsm_grid_html', 'hidden', is_gsm ? 0 : 1);
    frm.set_df_property('custom_html_grid', 'hidden', is_gsm ? 0 : 1);
    frm.toggle_display('gsm', is_gsm);
    frm.toggle_display('gsm_total_samples', is_gsm);
    frm.toggle_display('gsm_pass_samples', is_gsm);
    frm.toggle_display('gsm_fail_samples', is_gsm);
    frm.toggle_display('gsm_overall_result', is_gsm);
    frm.toggle_display('gsm_total_sections', is_gsm);
    frm.toggle_display('gsm_pass_sections', is_gsm);
    frm.toggle_display('gsm_fail_sections', is_gsm);

    // Set read_only states
    const keep_editable = [
        'naming_series',
        'testing_type',
        'batch_no',
        'order_code',
        'shaft_production_run',
        'gsm_production_entry',
        'quality',
        'unit',
        'color',
        'shift',
        'roll_no',
        'date',
        'test_method',
        'cutting_template_width',
        'cutting_template_height',
        'tensile_sections',
        'colour_spectrum_sections'
    ];
    frm.meta.fields.forEach(f => {
        if (!keep_editable.includes(f.fieldname)) {
            frm.set_df_property(f.fieldname, 'read_only', 1);
        } else {
            // Explicitly unlock these fields to override DocType settings
            frm.set_df_property(f.fieldname, 'read_only', 0);
        }
    });

    if (is_tensile) {
        hide_colour_spectrum_grid(frm);
        frm.set_df_property('test_method', 'read_only', 0);
        frm.set_df_property('cutting_template_width', 'read_only', 0);
        frm.set_df_property('cutting_template_height', 'read_only', 0);
        frm.set_df_property('tensile_sections', 'read_only', 0);
        recalc_tensile_total_samples(frm);
        empty_gsm_grid(frm);
        if (frm.is_new()) {
            const sectionsField = get_sections_field(frm);
            if (sectionsField && (frm.doc[sectionsField] || []).length) {
                frm.clear_table(sectionsField);
                frm.refresh_field(sectionsField);
            }
        }
    } else if (is_colour) {
        hide_tensile_grid(frm);
        frm.set_df_property('colour_spectrum_sections', 'read_only', 0);
        ensure_colour_spectrum_rows(frm);
        recalc_colour_spectrum_summary(frm);
        empty_gsm_grid(frm);
        if (frm.is_new()) {
            const sectionsField = get_sections_field(frm);
            if (sectionsField && (frm.doc[sectionsField] || []).length) {
                frm.clear_table(sectionsField);
                frm.refresh_field(sectionsField);
            }
        }
    } else {
        hide_tensile_grid(frm);
        hide_colour_spectrum_grid(frm);
        frm.set_df_property('sections', 'read_only', 0);
        frm.set_df_property('custom_gsm_grid_html', 'read_only', 0);
        frm.set_df_property('custom_html_grid', 'hidden', 0);
        frm.set_df_property('custom_gsm_grid_html', 'hidden', 0);
        render_custom_html_grid(frm);
    }
}

function set_auto_naming_series(frm) {
    if (!frm.is_new() || !frm.doc.unit || !frm.doc.testing_type) return;
    
    let prefix = "RGSM";
    if (frm.doc.testing_type === "Tensile Testing") {
        prefix = "TT";
    } else if (frm.doc.testing_type === "Patty Cutting GSM Test") {
        prefix = "PGSM";
    } else if (frm.doc.testing_type === "Colour Spectrum") {
        prefix = "CS";
    }

    const unit_clean = frm.doc.unit.toLowerCase().replace(/\s+/g, '');
    const unit_map = {
        "unit1": "U1",
        "unit2": "U2",
        "unit3": "U3",
        "unit4": "U4"
    };
    const u = unit_map[unit_clean] || "U1";
    
    frm.set_value("naming_series", `JSB/${prefix}-${u}/26-27/.###`);
}

["Quality Checking Section"].forEach((childDoctype) => {
frappe.ui.form.on(childDoctype, {
    representative_gsm(frm, cdt, cdn) {
        recalc_section_and_parent(frm, cdt, cdn);
    },
    quality(frm, cdt, cdn) {
        recalc_section_and_parent(frm, cdt, cdn);
    }
});
});

for (let i = 1; i <= 25; i++) {
    ["Quality Checking Section"].forEach((childDoctype) => {
        frappe.ui.form.on(childDoctype, {
            [`r1_s${i}`]: function (frm, cdt, cdn) {
                recalc_section_and_parent(frm, cdt, cdn);
            },
            [`r2_s${i}`]: function (frm, cdt, cdn) {
                recalc_section_and_parent(frm, cdt, cdn);
            }
        });
    });
}

function get_sections_field(frm) {
    if (frm.fields_dict && frm.fields_dict.sections) return "sections";
    return null;
}

function safe_set_value(frm, fieldname, value) {
    if (frm.fields_dict && frm.fields_dict[fieldname]) {
        frm.set_value(fieldname, value);
    }
}

function add_load_gsm_button(frm) {
    const sectionsField = get_sections_field(frm);
    if (!frm.doc.shaft_production_run || !sectionsField) return;

    if (frm.custom_buttons && frm.custom_buttons[__("Load Quality Sections")]) {
        return;
    }

    frm.add_custom_button(__("Load Quality Sections"), () => {
        if (is_tensile_testing(frm) || is_colour_spectrum(frm)) {
            frappe.msgprint(__("GSM sample tables are not used for this testing type."));
            return;
        }
        if (!frm.doc.batch_no && !cint(frm.doc.roll_no)) {
            frappe.msgprint(__("Select Batch No first. The GSM table is loaded for that roll only."));
            return;
        }
        frappe.call({
            method: "quality_gsm_app.api.quality.get_unique_gsm_values",
            args: gsm_query_args(frm),
            callback: (r) => {
                const values = parse_gsm_values(r.message);
                if (!values.length) {
                    frappe.msgprint(__("No GSM values found for this batch / roll."));
                    return;
                }
                apply_gsm_sections(frm, values);
                frappe.show_alert({ message: __("Quality section loaded for this roll"), indicator: "green" });
            }
        });
    });
}

function recalc_section_and_parent(frm, cdt, cdn) {
    const sectionsField = get_sections_field(frm);
    const row = locals[cdt][cdn];
    if (!row || !sectionsField) return;
    recalc_one_section(frm, row);
    recalc_parent_summary(frm);
    update_dom_calculations(row);
}

function recalc_all_sections(frm) {
    const sectionsField = get_sections_field(frm);
    if (!sectionsField) return;
    (frm.doc[sectionsField] || []).forEach((row) => recalc_one_section(frm, row));
    recalc_parent_summary(frm);
}

function get_threshold(qualityText) {
    const q = (qualityText || "").toString().toLowerCase();
    return q.includes("low") || q.includes("lower") ? 5 : 3;
}

function recalc_one_section(frm, row) {
    const sampleCount = 25;
    const setGsm = flt(row.representative_gsm);
    const quality = row.quality || frm.doc.quality || "";
    const threshold = get_threshold(quality);

    let r1Sum = 0;
    let r2Sum = 0;
    let combinedSum = 0;
    let passCount = 0;
    let failCount = 0;
    let anyFailed = false;

    for (let i = 1; i <= sampleCount; i++) {
        const v1 = flt(row[`r1_s${i}`]);
        const v2 = flt(row[`r2_s${i}`]);

        r1Sum += v1;
        r2Sum += v2;

        const avg = flt((v1 + v2) / 2, 3);
        row[`s${i}_combined_avg`] = avg;

        let diff = 0;
        if (setGsm > 0) {
            diff = flt(avg - setGsm, 3);
            const isPass = Math.abs(diff) < threshold;
            if (isPass) passCount += 1;
            else {
                failCount += 1;
                anyFailed = true;
            }
        }
        row[`s${i}_diff`] = diff;
        combinedSum += avg;
    }

    row.r1_average = flt(r1Sum / sampleCount, 3);
    row.r2_average = flt(r2Sum / sampleCount, 3);
    row.grand_average_gsm = flt(combinedSum / sampleCount, 3);

    row.tolerance_limit = threshold;
    row.pass_count = passCount;
    row.fail_count = failCount;
    row.section_result = setGsm > 0 ? (anyFailed ? "FAIL" : "PASS") : "";
}

function recalc_parent_summary(frm) {
    const sectionsField = get_sections_field(frm);
    if (!sectionsField) return;
    const rows = frm.doc[sectionsField] || [];
    let passSamples = 0;
    let failSamples = 0;

    rows.forEach((r) => {
        passSamples += (r.pass_count || 0);
        failSamples += (r.fail_count || 0);
    });
    
    // Each section has exactly 25 samples
    let totalSamples = rows.length * 25;

    safe_set_value(frm, "gsm_total_samples", totalSamples);
    safe_set_value(frm, "gsm_pass_samples", passSamples);
    safe_set_value(frm, "gsm_fail_samples", failSamples);
    safe_set_value(frm, "gsm_overall_result", totalSamples ? (failSamples > 0 ? "FAIL" : "PASS") : "");
}


// -----------------------------------------------------
// CUSTOM HTML GRID RENDERER
// -----------------------------------------------------
function render_custom_html_grid(frm) {
    if (!frm.fields_dict.custom_html_grid) return;
    const wrapper = frm.fields_dict.custom_html_grid.$wrapper;
    wrapper.empty();

    if (is_tensile_testing(frm) || is_colour_spectrum(frm)) {
        empty_gsm_grid(frm);
        return;
    }

    const sectionsField = get_sections_field(frm);
    let rows = frm.doc[sectionsField] || [];
    const targetGsm = selected_gsm(frm) || flt(frm._qc_target_gsm);
    if (targetGsm > 0 && rows.length) {
        const matched = rows.filter((row) => Math.abs(flt(row.representative_gsm) - targetGsm) < 0.51);
        rows = matched.length ? matched : [rows[0]];
    } else if (rows.length > 1) {
        rows = [rows[0]];
    }
    if (!rows.length) {
        wrapper.html(`<div class="text-muted" style="padding: 15px;">No GSM section for this batch. Select Batch No, then Load Quality Sections if needed.</div>`);
        return;
    }

    let html = `
        <style>
            .gsm-excel-grid { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px; font-family: Inter, sans-serif; table-layout: fixed; }
            .gsm-excel-grid th, .gsm-excel-grid td { border: 1px solid #d1d8dd; padding: 6px 4px; text-align: center; overflow: hidden; }
            .gsm-excel-grid th { background-color: #f3f3f3; font-weight: bold; }
            .gsm-excel-grid input { width: 100%; border: none; text-align: center; font-size: 13px; background: transparent; outline: none; }
            .gsm-excel-grid input:focus { background-color: #e2e8f0; }
            .row-header { font-weight: bold; background-color: #f8f9fa; text-align: left !important; width: 100px; }
            .section-wrapper { margin-bottom: 30px; overflow-x: auto; }
            .set-gsm-col { font-weight: bold; width: 60px; }
            .avg-col { font-weight: bold; background-color: #ecf0f1; width: 60px; }
            .pass-diff { background-color: #eafaf1; color: #1e8449; font-weight: bold; }
            .fail-diff { background-color: #fdedec; color: #c0392b; font-weight: bold; }
            .s-idx-col { width: 45px; }
        </style>
    `;

    rows.forEach((row, idx) => {
        const quality = row.quality || frm.doc.quality || "";
        const limit = get_threshold(quality);

        html += `
        <div class="section-wrapper">
            <h5>Section ${idx + 1} - Set GSM: ${row.representative_gsm} | Result: <span id="res_${row.name}">${row.section_result || '-'}</span></h5>
            <table class="gsm-excel-grid" data-row-name="${row.name}">
                <thead>
                    <tr>
                        <th class="row-header">SI NO: ${idx + 1}</th>
                        <th class="set-gsm-col">SET GSM</th>
        `;
        for (let i = 1; i <= 25; i++) {
            html += `<th class="s-idx-col">S${i}</th>`;
        }
        html += `<th class="avg-col">AVERAGE</th></tr></thead><tbody>`;

        // Row 1
        html += `
            <tr>
                <td class="row-header">GSM (ROW 1)</td>
                <td class="set-gsm-col">${row.representative_gsm}</td>
        `;
        for (let i = 1; i <= 25; i++) {
            html += `<td><input type="number" class="gsm-input" data-row="${row.name}" data-field="r1_s${i}" value="${row[`r1_s${i}`] || ''}" /></td>`;
        }
        html += `<td class="avg-col" id="r1_avg_${row.name}">${row.r1_average || 0}</td></tr>`;

        // Row 2
        html += `
            <tr>
                <td class="row-header">GSM (ROW 2)</td>
                <td class="set-gsm-col">${row.representative_gsm}</td>
        `;
        for (let i = 1; i <= 25; i++) {
            html += `<td><input type="number" class="gsm-input" data-row="${row.name}" data-field="r2_s${i}" value="${row[`r2_s${i}`] || ''}" /></td>`;
        }
        html += `<td class="avg-col" id="r2_avg_${row.name}">${row.r2_average || 0}</td></tr>`;

        // Combined Avg
        html += `
            <tr class="avg-col">
                <td class="row-header">COMBINED AVG</td>
                <td class="set-gsm-col">-</td>
        `;
        for (let i = 1; i <= 25; i++) {
            html += `<td id="cmb_avg_${row.name}_${i}">${row[`s${i}_combined_avg`] || 0}</td>`;
        }
        html += `<td id="grand_avg_${row.name}">${row.grand_average_gsm || 0}</td></tr>`;

        // Diff
        html += `
            <tr>
                <td class="row-header">DIFF</td>
                <td class="set-gsm-col">-</td>
        `;
        for (let i = 1; i <= 25; i++) {
            const d = row[`s${i}_diff`];
            const isPass = (d !== null && d !== undefined && Math.abs(d) < limit);
            const cls = d !== undefined && d !== null ? (isPass ? 'pass-diff' : 'fail-diff') : '';
            html += `<td id="diff_${row.name}_${i}" class="${cls}">${d !== undefined && d !== null ? d : ''}</td>`;
        }
        html += `<td id="sec_res_${row.name}">${row.section_result || ''}</td></tr>`;

        html += `</tbody></table></div>`;
    });

    wrapper.html(html);

    // Bind events
    wrapper.find('.gsm-input').on('change', function() {
        const val = $(this).val();
        const rowName = $(this).data('row');
        const fieldName = $(this).data('field');
        
        // Update frappe model
        frappe.model.set_value("Quality Checking Section", rowName, fieldName, flt(val));
    });
}

function update_dom_calculations(row) {
    if (!row) return;
    const quality = row.quality || cur_frm.doc.quality || "";
    const limit = get_threshold(quality);

    $(`#r1_avg_${row.name}`).text(row.r1_average);
    $(`#r2_avg_${row.name}`).text(row.r2_average);
    $(`#grand_avg_${row.name}`).text(row.grand_average_gsm);
    $(`#res_${row.name}`).text(row.section_result);
    $(`#sec_res_${row.name}`).text(row.section_result);

    for (let i = 1; i <= 25; i++) {
        $(`#cmb_avg_${row.name}_${i}`).text(row[`s${i}_combined_avg`]);
        const d = row[`s${i}_diff`];
        const td = $(`#diff_${row.name}_${i}`);
        td.text(d !== undefined && d !== null ? d : '');
        td.removeClass('pass-diff fail-diff');
        if (d !== undefined && d !== null) {
            td.addClass(Math.abs(d) < limit ? 'pass-diff' : 'fail-diff');
        }
    }
}
