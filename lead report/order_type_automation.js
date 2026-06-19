frappe.ui.form.on('Opportunity', {
    refresh: function(frm) {
        frm.trigger('calculate_order_type');
    },

    custom_requirement: function(frm) {
        frm.trigger('calculate_order_type');
    },

    custom_monthly_fabric_requirement_kg: function(frm) {
        frm.trigger('calculate_order_type');
    },

    custom_monthly_fabric_need_kgs: function(frm) {
        frm.trigger('calculate_order_type');
    },

    calculate_order_type: function(frm) {
        let req = frm.doc.custom_requirement;
        let target_value = '';

        if (req === 'Non Woven Fabric') {
            let val = frm.doc.custom_monthly_fabric_requirement_kg;
            if (val !== undefined && val !== null && val !== '') {
                let qty = flt(val);
                if (qty < 1000) target_value = 'Below 1 Ton';
                else if (qty >= 1000 && qty <= 5000) target_value = '1-5 Ton';
                else if (qty > 5000) target_value = 'Above 5 Ton';
            }
        } else if (req === 'Non Woven Fabric & Bag') {
            let val = frm.doc.custom_monthly_fabric_need_kgs;
            if (val !== undefined && val !== null && val !== '') {
                let qty = flt(val);
                if (qty < 1000) target_value = 'Below 1 Ton';
                else if (qty >= 1000 && qty <= 5000) target_value = '1-5 Ton';
                else if (qty > 5000) target_value = 'Above 5 Ton';
            }
        } else {
            target_value = '';
        }

        if (target_value) {
            // Dynamically match the casing and spacing of the custom_order_type options
            let order_type_field = frappe.meta.get_docfield(frm.doc.doctype, 'custom_order_type', frm.doc.name);
            if (order_type_field && order_type_field.options) {
                let options = order_type_field.options.split('\n').map(opt => opt.trim());
                let matched_opt = options.find(opt => opt.toLowerCase().replace(/\s+/g, '') === target_value.toLowerCase().replace(/\s+/g, ''));
                if (matched_opt) {
                    target_value = matched_opt;
                }
            }
        }

        if (frm.doc.custom_order_type !== target_value) {
            frm.set_value('custom_order_type', target_value);
        }
    }
});
