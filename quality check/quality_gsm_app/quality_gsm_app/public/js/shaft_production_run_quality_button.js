frappe.ui.form.on("Shaft Production Run", {
    refresh(frm) {
        // Avoid duplicating button on every refresh.
        if (frm.custom_buttons && frm.custom_buttons[__("Start GSM Testing")]) {
            return;
        }

        const unit = (frm.doc.custom_unit || "").toLowerCase().replace(/ /g, "");
        if (!["unit1", "unit2", "unit3", "unit4"].includes(unit)) {
            // Remove the buttons if they were added by any other script (using interval to catch late renders)
            let attempts = 0;
            const cleanupInterval = setInterval(() => {
                frm.remove_custom_button(__("Start GSM Testing"), __("Quality"));
                frm.remove_custom_button(__("Start GSM Testing"), __("Quality Check"));
                frm.remove_custom_button(__("Start Tensile Testing"), __("Quality"));
                frm.remove_custom_button(__("Start Tensile Testing"), __("Quality Check"));
                attempts++;
                if (attempts > 30) {
                    clearInterval(cleanupInterval);
                }
            }, 100);
            return;
        }

        frm.add_custom_button(
            __("Round Cutting GSM Test"),
            () => {
                frappe.call({
                    method: "quality_gsm_app.api.quality.get_batches_from_shaft",
                    args: { shaft_production_run: frm.doc.name },
                    callback: (r) => {
                        const batches = r.message || [];
                        let prompt_field = {
                            fieldtype: "Data",
                            fieldname: "batch_no",
                            label: __("Enter Batch No"),
                            reqd: 1,
                        };
                        if (batches.length) {
                            prompt_field = {
                                fieldtype: "Select",
                                fieldname: "batch_no",
                                label: __("Select Batch No"),
                                options: batches,
                                reqd: 1,
                                default: batches.length === 1 ? batches[0] : "",
                            };
                        }
                        
                        frappe.prompt(
                            [prompt_field],
                            (values) => { create_quality_checking(frm.doc.name, values.batch_no, "Round Cutting GSM Test"); },
                            batches.length ? __("Select Batch") : __("Start Testing"), 
                            __("Start Testing")
                        );
                    }
                });
            },
            __("Quality Check")
        );

        frm.add_custom_button(
            __("Patty Cutting GSM Test"),
            () => {
                frappe.call({
                    method: "quality_gsm_app.api.quality.get_batches_from_shaft",
                    args: { shaft_production_run: frm.doc.name },
                    callback: (r) => {
                        const batches = r.message || [];
                        let prompt_field = {
                            fieldtype: "Data",
                            fieldname: "batch_no",
                            label: __("Enter Batch No"),
                            reqd: 1,
                        };
                        if (batches.length) {
                            prompt_field = {
                                fieldtype: "Select",
                                fieldname: "batch_no",
                                label: __("Select Batch No"),
                                options: batches,
                                reqd: 1,
                                default: batches.length === 1 ? batches[0] : "",
                            };
                        }
                        
                        frappe.prompt(
                            [prompt_field],
                            (values) => { create_quality_checking(frm.doc.name, values.batch_no, "Patty Cutting GSM Test"); },
                            batches.length ? __("Select Batch") : __("Start Testing"), 
                            __("Start Testing")
                        );
                    }
                });
            },
            __("Quality Check")
        );

        frm.add_custom_button(
            __("Tensile Testing"),
            () => {
                frappe.call({
                    method: "quality_gsm_app.api.quality.get_batches_from_shaft",
                    args: { shaft_production_run: frm.doc.name },
                    callback: (r) => {
                        const batches = r.message || [];
                        let prompt_field = {
                            fieldtype: "Data",
                            fieldname: "batch_no",
                            label: __("Enter Batch No"),
                            reqd: 1,
                        };
                        if (batches.length) {
                            prompt_field = {
                                fieldtype: "Select",
                                fieldname: "batch_no",
                                label: __("Select Batch No"),
                                options: batches,
                                reqd: 1,
                                default: batches.length === 1 ? batches[0] : "",
                            };
                        }
                        
                        frappe.prompt(
                            [prompt_field],
                            (values) => { create_quality_checking(frm.doc.name, values.batch_no, "Tensile Testing"); },
                            batches.length ? __("Select Batch") : __("Start Testing"), 
                            __("Start Testing")
                        );
                    }
                });
            },
            __("Quality Check")
        );

        frm.add_custom_button(
            __("Colour Spectrum"),
            () => {
                frappe.call({
                    method: "quality_gsm_app.api.quality.get_batches_from_shaft",
                    args: { shaft_production_run: frm.doc.name },
                    callback: (r) => {
                        const batches = r.message || [];
                        let prompt_field = {
                            fieldtype: "Data",
                            fieldname: "batch_no",
                            label: __("Enter Batch No"),
                            reqd: 1,
                        };
                        if (batches.length) {
                            prompt_field = {
                                fieldtype: "Select",
                                fieldname: "batch_no",
                                label: __("Select Batch No"),
                                options: batches,
                                reqd: 1,
                                default: batches.length === 1 ? batches[0] : "",
                            };
                        }
                        
                        frappe.prompt(
                            [prompt_field],
                            (values) => { create_quality_checking(frm.doc.name, values.batch_no, "Colour Spectrum"); },
                            batches.length ? __("Select Batch") : __("Start Testing"), 
                            __("Start Testing")
                        );
                    }
                });
            },
            __("Quality Check")
        );
    }
});

function create_quality_checking(shaft_name, batch_no, testing_type="Round Cutting GSM Test") {
    const roll_no = (String(batch_no || "").includes("/"))
        ? cint(String(batch_no).split("/").pop())
        : 0;
    frappe.call({
        method: "quality_gsm_app.api.quality.create_quality_checking_from_shaft",
        args: { 
            shaft_production_run: shaft_name,
            batch_no: batch_no,
            testing_type: testing_type,
            roll_no: roll_no
        },
        freeze: true,
        callback: (r) => {
            const name = r.message;
            if (!name) {
                frappe.msgprint(__("Could not create Quality Checking doc."));
                return;
            }
            window.open(frappe.urllib.get_full_url('/app/quality-checking/' + name), '_blank');
        }
    });
}
