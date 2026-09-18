# Copyright (c) 2026, Frappe Developer and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime
from assessment_hub.api.v1.assessments import list_assessments, get_assessment
from assessment_hub.api.v1.questions import create_question, list_questions


class TestPartnerAPI(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("Assessment", {"title": ["in", ["API Test Assessment", "Archived API Assessment"]]})

		# Ensure test roles exist
		from assessment_hub.setup import setup_roles
		setup_roles()

		# Create test user with Assessment Viewer role
		if not frappe.db.exists("User", "viewer@test.com"):
			viewer = frappe.get_doc({
				"doctype": "User",
				"email": "viewer@test.com",
				"first_name": "Test",
				"last_name": "Viewer",
				"roles": [{"role": "Assessment Viewer"}]
			}).insert(ignore_permissions=True)

		# Create test user with Assessment Manager role
		if not frappe.db.exists("User", "manager@test.com"):
			manager = frappe.get_doc({
				"doctype": "User",
				"email": "manager@test.com",
				"first_name": "Test",
				"last_name": "Manager",
				"roles": [{"role": "Assessment Manager"}]
			}).insert(ignore_permissions=True)

		# Create seed assessment
		self.assessment = frappe.get_doc({
			"doctype": "Assessment",
			"title": "API Test Assessment",
			"description": "Assessment for API verification",
			"status": "Published"
		}).insert()

		self.archived_assessment = frappe.get_doc({
			"doctype": "Assessment",
			"title": "Archived API Assessment",
			"status": "Archived"
		}).insert()

		frappe.db.commit()

	def tearDown(self):
		frappe.set_user("Administrator")
		if hasattr(self, "assessment") and hasattr(self, "archived_assessment"):
			frappe.db.delete("Question", {"assessment": ["in", [self.assessment.name, self.archived_assessment.name]]})
			frappe.db.delete("Assessment", {"name": ["in", [self.assessment.name, self.archived_assessment.name]]})

	def test_unauthenticated_request_returns_401(self):
		frappe.set_user("Guest")
		res = list_assessments()
		self.assertEqual(res.status_code, 401)
		body = json.loads(res.data.decode("utf-8"))
		self.assertIn("errors", body)
		self.assertEqual(body["errors"][0]["code"], "UNAUTHORIZED")

	def test_role_authorization_forbidden_for_viewer_creating_question(self):
		frappe.set_user("viewer@test.com")
		res = create_question(
			assessment=self.assessment.name,
			content="Viewer attempting to create question"
		)
		self.assertEqual(res.status_code, 403)
		body = json.loads(res.data.decode("utf-8"))
		self.assertIn("errors", body)
		self.assertEqual(body["errors"][0]["code"], "FORBIDDEN")

	def test_create_question_atomic_transaction_success(self):
		frappe.set_user("manager@test.com")
		res = create_question(
			assessment=self.assessment.name,
			content="What is an Atomic Transaction?",
			sort_order=1,
			answers=[
				{"content": "All or nothing operation", "score": 10, "sort_order": 1},
				{"content": "Partial commit operation", "score": 0, "sort_order": 2}
			]
		)
		self.assertEqual(res.status_code, 201)
		body = json.loads(res.data.decode("utf-8"))
		self.assertIn("data", body)
		q_data = body["data"]
		self.assertEqual(q_data["assessment"], self.assessment.name)
		self.assertEqual(len(q_data["answers"]), 2)

		# Check database
		stored_q = frappe.get_doc("Question", q_data["id"])
		self.assertEqual(len(stored_q.answers), 2)

	def test_create_question_atomic_rollback_on_invalid_answer(self):
		frappe.set_user("manager@test.com")
		initial_count = frappe.db.count("Question")

		# Submit question with an invalid second answer (empty content)
		res = create_question(
			assessment=self.assessment.name,
			content="Question that should rollback",
			answers=[
				{"content": "Valid answer", "score": 5},
				{"content": "", "score": 0}  # Invalid empty content
			]
		)
		self.assertEqual(res.status_code, 400)
		body = json.loads(res.data.decode("utf-8"))
		self.assertIn("errors", body)
		self.assertEqual(body["errors"][0]["code"], "CREATE_QUESTION_FAILED")

		# Verify entire question was rolled back and not persisted in DB
		new_count = frappe.db.count("Question")
		self.assertEqual(new_count, initial_count)

	def test_cannot_create_question_for_archived_assessment(self):
		frappe.set_user("manager@test.com")
		res = create_question(
			assessment=self.archived_assessment.name,
			content="Question for archived assessment"
		)
		self.assertEqual(res.status_code, 400)
		body = json.loads(res.data.decode("utf-8"))
		self.assertIn("errors", body)
		self.assertEqual(body["errors"][0]["code"], "ASSESSMENT_ARCHIVED")

	def test_list_assessments_filters(self):
		frappe.set_user("viewer@test.com")

		# Filter by status
		res = list_assessments(status="Published")
		self.assertEqual(res.status_code, 200)
		body = json.loads(res.data.decode("utf-8"))
		self.assertIn("data", body)
		for item in body["data"]:
			self.assertEqual(item["status"], "Published")

		# Search by title
		res_search = list_assessments(title="API Test")
		self.assertEqual(res_search.status_code, 200)
		body_search = json.loads(res_search.data.decode("utf-8"))
		self.assertTrue(any(item["title"] == "API Test Assessment" for item in body_search["data"]))

	def test_get_assessment_with_and_without_questions(self):
		frappe.set_user("manager@test.com")
		# Create a question first
		create_question(
			assessment=self.assessment.name,
			content="Nested question",
			sort_order=1,
			answers=[{"content": "Nested answer", "score": 10}]
		)

		frappe.set_user("viewer@test.com")
		# 1. Without questions
		res_no_q = get_assessment(id=self.assessment.name, include_questions=0)
		self.assertEqual(res_no_q.status_code, 200)
		body_no_q = json.loads(res_no_q.data.decode("utf-8"))
		self.assertNotIn("questions", body_no_q["data"])

		# 2. With questions
		res_with_q = get_assessment(id=self.assessment.name, include_questions=1)
		self.assertEqual(res_with_q.status_code, 200)
		body_with_q = json.loads(res_with_q.data.decode("utf-8"))
		self.assertIn("questions", body_with_q["data"])
		self.assertEqual(len(body_with_q["data"]["questions"]), 1)
		self.assertEqual(len(body_with_q["data"]["questions"][0]["answers"]), 1)

	def test_list_questions_sorted_by_sort_order(self):
		frappe.set_user("manager@test.com")
		create_question(
			assessment=self.assessment.name,
			content="Second Question",
			sort_order=20
		)
		create_question(
			assessment=self.assessment.name,
			content="First Question",
			sort_order=5
		)

		frappe.set_user("viewer@test.com")
		res = list_questions(assessment_id=self.assessment.name)
		self.assertEqual(res.status_code, 200)
		body = json.loads(res.data.decode("utf-8"))
		questions = body["data"]
		self.assertGreaterEqual(len(questions), 2)
		# Verify sort_order ascending
		sort_orders = [q["sort_order"] for q in questions]
		self.assertEqual(sort_orders, sorted(sort_orders))

	def test_list_questions_filter_by_status(self):
		frappe.set_user("manager@test.com")
		create_question(
			assessment=self.assessment.name,
			content="Active Question for Filter",
			status="Active"
		)
		create_question(
			assessment=self.assessment.name,
			content="Inactive Question for Filter",
			status="Inactive"
		)

		frappe.set_user("viewer@test.com")

		# Filter Active
		res_active = list_questions(assessment_id=self.assessment.name, status="Active")
		self.assertEqual(res_active.status_code, 200)
		body_active = json.loads(res_active.data.decode("utf-8"))
		self.assertTrue(len(body_active["data"]) > 0)
		for q in body_active["data"]:
			self.assertEqual(q["status"], "Active")

		# Filter Inactive
		res_inactive = list_questions(assessment_id=self.assessment.name, status="Inactive")
		self.assertEqual(res_inactive.status_code, 200)
		body_inactive = json.loads(res_inactive.data.decode("utf-8"))
		self.assertTrue(len(body_inactive["data"]) > 0)
		for q in body_inactive["data"]:
			self.assertEqual(q["status"], "Inactive")

		# Filter with invalid status
		res_invalid = list_questions(assessment_id=self.assessment.name, status="InvalidStatus")
		self.assertEqual(res_invalid.status_code, 400)
		body_invalid = json.loads(res_invalid.data.decode("utf-8"))
		self.assertEqual(body_invalid["errors"][0]["code"], "INVALID_PARAM")
