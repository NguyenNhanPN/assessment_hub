# Copyright (c) 2026, Frappe Developer and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime


class TestAssessment(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Assessment", {"title": ["in", ["Python Developer Assessment", "Backend Assessment"]]})

	def tearDown(self):
		frappe.db.delete("Assessment", {"title": ["in", ["Python Developer Assessment", "Backend Assessment"]]})

	def test_assessment_default_status_and_naming(self):
		assessment = frappe.get_doc({
			"doctype": "Assessment",
			"title": "Python Developer Assessment",
			"description": "Assessment for Python and Frappe developers"
		}).insert()

		self.assertEqual(assessment.status, "Draft")
		current_year = str(now_datetime().year)
		self.assertTrue(assessment.name.startswith(f"ASM-{current_year}-"))

	def test_status_field_is_readonly(self):
		meta = frappe.get_meta("Assessment")
		status_field = meta.get_field("status")
		self.assertEqual(status_field.read_only, 1)

	def test_status_transitions(self):
		assessment = frappe.get_doc({
			"doctype": "Assessment",
			"title": "Backend Assessment",
			"status": "Draft"
		}).insert()

		# Transition to Published
		assessment.set_status("Published")
		self.assertEqual(assessment.status, "Published")

		# Transition to Archived
		assessment.set_status("Archived")
		self.assertEqual(assessment.status, "Archived")

		# Attempt to revert Archived directly to Published should fail
		assessment.status = "Published"
		self.assertRaises(frappe.ValidationError, assessment.save)

		# Reload to clear failed in-memory state
		assessment.reload()

		# Revert Archived to Draft should succeed
		assessment.set_status("Draft")
		self.assertEqual(assessment.status, "Draft")
