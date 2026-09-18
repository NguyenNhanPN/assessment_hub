# Copyright (c) 2026, Frappe Developer and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Assessment(Document):
	def validate(self):
		self.validate_status_transition()

	def validate_status_transition(self):
		if not self.is_new():
			previous_status = frappe.db.get_value("Assessment", self.name, "status")
			if previous_status == "Archived" and self.status not in ["Archived", "Draft"]:
				frappe.throw(
					_("Cannot change status of an Archived Assessment to {0}. It can only be reverted to Draft.").format(self.status),
					frappe.ValidationError
				)

	@frappe.whitelist()
	def set_status(self, status):
		self.check_permission("write")
		if status not in ["Draft", "Published", "Archived"]:
			frappe.throw(_("Invalid status: {0}").format(status), frappe.ValidationError)
		self.status = status
		self.save()
		return self.status
