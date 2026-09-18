# Copyright (c) 2026, Frappe Developer and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestQuestion(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Assessment", {"title": ["in", ["General Knowledge Assessment", "Archived Assessment"]]})

		self.assessment = frappe.get_doc({
			"doctype": "Assessment",
			"title": "General Knowledge Assessment",
			"status": "Published"
		}).insert()

		self.archived_assessment = frappe.get_doc({
			"doctype": "Assessment",
			"title": "Archived Assessment",
			"status": "Archived"
		}).insert()

	def tearDown(self):
		frappe.db.delete("Question", {"assessment": ["in", [self.assessment.name, self.archived_assessment.name]]})
		frappe.db.delete("Assessment", {"name": ["in", [self.assessment.name, self.archived_assessment.name]]})

	def test_create_question_with_answers(self):
		question = frappe.get_doc({
			"doctype": "Question",
			"assessment": self.assessment.name,
			"content": "What is Frappe Framework?",
			"sort_order": 1,
			"status": "Active",
			"answers": [
				{"content": "Fullstack web framework", "score": 10, "sort_order": 1},
				{"content": "Relational database", "score": 0, "sort_order": 2}
			]
		}).insert()

		self.assertTrue(question.name.startswith("QST-"))
		self.assertEqual(len(question.answers), 2)
		self.assertEqual(question.answers[0].score, 10.0)

		# Verify answers stored in child table
		stored_answers = frappe.get_all(
			"Assessment Answer",
			filters={"parent": question.name}
		)
		self.assertEqual(len(stored_answers), 2)

	def test_cannot_add_question_to_archived_assessment(self):
		question = frappe.get_doc({
			"doctype": "Question",
			"assessment": self.archived_assessment.name,
			"content": "Invalid question on archived assessment",
			"status": "Active"
		})
		self.assertRaises(frappe.ValidationError, question.insert)

	def test_cascade_delete_answers(self):
		question = frappe.get_doc({
			"doctype": "Question",
			"assessment": self.assessment.name,
			"content": "Question to delete",
			"answers": [
				{"content": "Answer 1", "score": 5},
				{"content": "Answer 2", "score": 0}
			]
		}).insert()

		q_name = question.name
		question.delete()

		remaining_answers = frappe.get_all("Assessment Answer", filters={"parent": q_name})
		self.assertEqual(len(remaining_answers), 0)
