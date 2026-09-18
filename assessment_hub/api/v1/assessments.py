# Copyright (c) 2026, Frappe Developer and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint
from assessment_hub.api.v1.utils import partner_api, api_error


@frappe.whitelist(allow_guest=True, methods=["GET"])
@partner_api(allowed_roles=["Assessment Viewer", "Assessment Manager"])
def list_assessments(page_length=20, start=0, page=None, status=None, title=None, updated_since=None):
	"""
	GET /api/method/assessment_hub.api.v1.assessments.list_assessments
	Lists assessments with pagination, status filter, title search, and updated_since filter.
	"""
	page_length = min(cint(page_length) or 20, 100)
	if page:
		start = max(0, (cint(page) - 1) * page_length)
	else:
		start = max(0, cint(start))

	Assessment = frappe.qb.DocType("Assessment")
	query = (
		frappe.qb.from_(Assessment)
		.select(
			Assessment.name,
			Assessment.title,
			Assessment.description,
			Assessment.status,
			Assessment.creation,
			Assessment.modified,
			Assessment.owner,
		)
	)

	if status:
		if status not in ["Draft", "Published", "Archived"]:
			return api_error(f"Invalid status filter: {status}", "INVALID_PARAM", 400)
		query = query.where(Assessment.status == status)

	if title:
		query = query.where(Assessment.title.like(f"%{title}%"))

	if updated_since:
		query = query.where(Assessment.modified >= updated_since)
		query = query.orderby(Assessment.modified, order=frappe.qb.asc)
	else:
		query = query.orderby(Assessment.creation, order=frappe.qb.desc)

	query = query.offset(start).limit(page_length)
	records = query.run(as_dict=True)

	return records


@frappe.whitelist(allow_guest=True, methods=["GET"])
@partner_api(allowed_roles=["Assessment Viewer", "Assessment Manager"])
def get_assessment(id=None, include_questions=0):
	"""
	GET /api/method/assessment_hub.api.v1.assessments.get_assessment?id=<name>&include_questions=1
	Returns details of a single assessment, optionally nested with questions and answers.
	"""
	if not id:
		return api_error("Missing required parameter: 'id'", "MISSING_PARAM", 400)

	if not frappe.db.exists("Assessment", id):
		return api_error(f"Assessment '{id}' not found.", "NOT_FOUND", 404)

	doc = frappe.get_doc("Assessment", id)
	data = {
		"id": doc.name,
		"title": doc.title,
		"description": doc.description,
		"status": doc.status,
		"creation": doc.creation,
		"modified": doc.modified,
		"owner": doc.owner,
	}

	include_questions = cint(include_questions)
	if include_questions == 1:
		Question = frappe.qb.DocType("Question")
		q_query = (
			frappe.qb.from_(Question)
			.select(
				Question.name,
				Question.content,
				Question.sort_order,
				Question.status,
				Question.creation,
				Question.modified,
			)
			.where(Question.assessment == id)
			.orderby(Question.sort_order, order=frappe.qb.asc)
		)
		questions = q_query.run(as_dict=True)

		for q in questions:
			q["answers"] = frappe.get_all(
				"Assessment Answer",
				filters={"parent": q["name"], "parenttype": "Question", "parentfield": "answers"},
				fields=["content", "score", "sort_order"],
				order_by="sort_order asc"
			)

		data["questions"] = questions

	return data
