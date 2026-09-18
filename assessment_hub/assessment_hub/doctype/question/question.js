// Copyright (c) 2026, Frappe Developer and contributors
// For license information, please see license.txt

frappe.ui.form.on("Question", {
	setup: function(frm) {
		// Do not allow selecting Archived Assessments
		frm.set_query("assessment", function() {
			return {
				filters: [
					["Assessment", "status", "!=", "Archived"]
				]
			};
		});
	},
	refresh: function(frm) {
		if (frm.doc.assessment) {
			frappe.db.get_value("Assessment", frm.doc.assessment, "status").then(r => {
				if (r && r.message && r.message.status === "Archived") {
					frm.set_intro(__("This Question belongs to an Archived Assessment and cannot be edited."), "red");
					frm.disable_save();
				}
			});
		}
	}
});
