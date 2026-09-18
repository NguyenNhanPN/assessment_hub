// Copyright (c) 2026, Frappe Developer and contributors
// For license information, please see license.txt

frappe.listview_settings["Assessment"] = {
	add_fields: ["status"],
	get_indicator: function(doc) {
		if (doc.status === "Published") {
			return [__("Published"), "green", "status,=,Published"];
		} else if (doc.status === "Archived") {
			return [__("Archived"), "red", "status,=,Archived"];
		} else {
			return [__("Draft"), "gray", "status,=,Draft"];
		}
	}
};
