// Copyright (c) 2026, Frappe Developer and contributors
// For license information, please see license.txt

frappe.ui.form.on("Assessment", {
	refresh: function(frm) {
		// Ensure status is always read-only in UI
		frm.set_df_property("status", "read_only", 1);

		if (frm.is_new()) {
			return;
		}

		const is_manager = frappe.user_roles.includes("Assessment Manager") ||
			frappe.user_roles.includes("System Manager") ||
			frappe.session.user === "Administrator";

		// Action buttons for status transitions
		if (is_manager) {
			if (frm.doc.status === "Draft") {
				frm.add_custom_button(__("Publish"), function() {
					frappe.confirm(__("Are you sure you want to Publish this Assessment?"), function() {
						frm.call("set_status", { status: "Published" })
							.then(() => {
								frm.reload_doc();
								frappe.show_alert({
									message: __("Assessment Published successfully."),
									indicator: "green"
								});
							});
					});
				}).addClass("btn-primary");
			} else if (frm.doc.status === "Published") {
				frm.add_custom_button(__("Archive"), function() {
					frappe.confirm(__("Archiving this Assessment will freeze questions from being added or edited. Continue?"), function() {
						frm.call("set_status", { status: "Archived" })
							.then(() => {
								frm.reload_doc();
								frappe.show_alert({
									message: __("Assessment Archived."),
									indicator: "orange"
								});
							});
					});
				}).addClass("btn-danger");
			} else if (frm.doc.status === "Archived") {
				frm.add_custom_button(__("Mark as Draft"), function() {
					frappe.confirm(__("Are you sure you want to revert this Assessment to Draft?"), function() {
						frm.call("set_status", { status: "Draft" })
							.then(() => {
								frm.reload_doc();
								frappe.show_alert({
									message: __("Assessment marked as Draft."),
									indicator: "green"
								});
							});
					});
				}).addClass("btn-primary");
			}
		}

		// Quick action: Add Question
		if (frm.doc.status !== "Archived" && is_manager) {
			frm.add_custom_button(__("Add Question"), function() {
				frappe.new_doc("Question", {
					assessment: frm.doc.name
				});
			}, __("Actions"));
		}

		// Intro message for Archived
		if (frm.doc.status === "Archived") {
			frm.set_intro(__("This Assessment is Archived. Questions cannot be added or modified."), "red");
		}
	}
});
