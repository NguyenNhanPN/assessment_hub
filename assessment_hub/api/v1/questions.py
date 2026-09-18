# Copyright (c) 2026, Frappe Developer and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.utils import cint, flt
from assessment_hub.api.v1.utils import partner_api, api_error, api_success


@frappe.whitelist(allow_guest=True, methods=["POST"])
@partner_api(allowed_roles=["Assessment Manager"])
def create_question(assessment=None, content=None, sort_order=0, status="Active", answers=None):
	"""
	POST /api/method/assessment_hub.api.v1.questions.create_question
	Creates a new Question with child answers atomically.
	If any answer is invalid, rolls back the entire transaction.
	"""
	# If request body is JSON, extract from frappe.request if needed
	if not assessment and frappe.request.data:
		try:
			payload = json.loads(frappe.request.data.decode("utf-8"))
			assessment = payload.get("assessment")
			content = payload.get("content")
			sort_order = payload.get("sort_order", 0)
			status = payload.get("status", "Active")
			answers = payload.get("answers")
		except Exception:
			pass

	if not assessment:
		return api_error("Missing required field: 'assessment'", "MISSING_PARAM", 400)
	if not content:
		return api_error("Missing required field: 'content'", "MISSING_PARAM", 400)

	# Validate Assessment
	if not frappe.db.exists("Assessment", assessment):
		return api_error(f"Assessment '{assessment}' not found.", "NOT_FOUND", 404)

	assessment_status = frappe.db.get_value("Assessment", assessment, "status")
	if assessment_status == "Archived":
		return api_error(
			f"Cannot add questions to an Archived Assessment ({assessment}).",
			"ASSESSMENT_ARCHIVED",
			400
		)

	# Parse answers if sent as JSON string
	if isinstance(answers, str):
		try:
			answers = json.loads(answers)
		except Exception:
			return api_error("Invalid JSON format in 'answers' field.", "INVALID_PARAM", 400)

	if answers is not None and not isinstance(answers, list):
		return api_error("'answers' must be a list of answer objects.", "INVALID_PARAM", 400)

	# Atomic Transaction with Savepoint
	savepoint_name = "create_question_sp"
	frappe.db.savepoint(savepoint_name)

	try:
		doc = frappe.get_doc({
			"doctype": "Question",
			"assessment": assessment,
			"content": content,
			"sort_order": cint(sort_order),
			"status": status or "Active",
			"answers": []
		})

		if answers:
			for idx, ans in enumerate(answers):
				if not isinstance(ans, dict):
					raise ValueError(f"Answer at index {idx} must be a dictionary/object.")
				ans_content = ans.get("content")
				if not ans_content or not str(ans_content).strip():
					raise ValueError(f"Answer at index {idx} requires non-empty 'content'.")

				try:
					score_val = flt(ans.get("score", 0))
				except (ValueError, TypeError):
					raise ValueError(f"Answer at index {idx} has invalid 'score'. Must be numeric.")

				doc.append("answers", {
					"content": str(ans_content).strip(),
					"score": score_val,
					"sort_order": cint(ans.get("sort_order", idx)),
				})

		doc.insert()
		frappe.db.commit()

		response_data = {
			"id": doc.name,
			"assessment": doc.assessment,
			"content": doc.content,
			"sort_order": doc.sort_order,
			"status": doc.status,
			"creation": doc.creation,
			"modified": doc.modified,
			"answers": [
				{
					"content": a.content,
					"score": a.score,
					"sort_order": a.sort_order
				}
				for a in doc.answers
			]
		}
		return api_success(response_data, status=201)

	except Exception as e:
		frappe.db.rollback(save_point=savepoint_name)
		return api_error(str(e), "CREATE_QUESTION_FAILED", 400)


@frappe.whitelist(allow_guest=True, methods=["GET"])
@partner_api(allowed_roles=["Assessment Viewer", "Assessment Manager"])
def list_questions(assessment_id=None, status=None):
	"""
	GET /api/method/assessment_hub.api.v1.questions.list_questions?assessment_id=<name>&status=Active
	Retrieves all questions for a given Assessment sorted by sort_order ascending.
	Supports filtering by question status ('Active', 'Inactive').
	"""
	assessment_id = assessment_id or frappe.form_dict.get("assessment_id")
	status = status or frappe.form_dict.get("status")

	if not assessment_id:
		return api_error("Missing required parameter: 'assessment_id'", "MISSING_PARAM", 400)

	if not frappe.db.exists("Assessment", assessment_id):
		return api_error(f"Assessment '{assessment_id}' not found.", "NOT_FOUND", 404)

	Question = frappe.qb.DocType("Question")
	query = (
		frappe.qb.from_(Question)
		.select(
			Question.name,
			Question.assessment,
			Question.content,
			Question.sort_order,
			Question.status,
			Question.creation,
			Question.modified,
		)
		.where(Question.assessment == assessment_id)
	)

	if status:
		if status not in ["Active", "Inactive"]:
			return api_error(f"Invalid status filter: {status}", "INVALID_PARAM", 400)
		query = query.where(Question.status == status)

	query = query.orderby(Question.sort_order, order=frappe.qb.asc)
	questions = query.run(as_dict=True)

	for q in questions:
		q["answers"] = frappe.get_all(
			"Assessment Answer",
			filters={"parent": q["name"], "parenttype": "Question", "parentfield": "answers"},
			fields=["content", "score", "sort_order"],
			order_by="sort_order asc"
		)

	return questions
