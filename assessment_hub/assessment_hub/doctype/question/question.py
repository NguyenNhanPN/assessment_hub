# Copyright (c) 2026, Frappe Developer and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Question(Document):
	def validate(self):
		self.validate_assessment_status()

	def validate_assessment_status(self):
		if not self.assessment:
			return

		assessment_status = frappe.db.get_value("Assessment", self.assessment, "status")
		if not assessment_status:
			frappe.throw(
				_("Assessment {0} does not exist.").format(self.assessment),
				frappe.DoesNotExistError
			)

		if assessment_status == "Archived":
			frappe.throw(
				_("Cannot add or modify questions for an Archived Assessment ({0}).").format(self.assessment),
				frappe.ValidationError
			)
