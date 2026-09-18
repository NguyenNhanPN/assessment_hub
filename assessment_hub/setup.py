# Copyright (c) 2026, Frappe Developer and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def after_install():
	setup_roles()
	setup_number_cards()
	frappe.db.commit()


def setup_roles():
	roles = [
		{"role_name": "Assessment Manager", "desk_access": 1},
		{"role_name": "Assessment Viewer", "desk_access": 1},
	]
	for r in roles:
		if not frappe.db.exists("Role", r["role_name"]):
			role_doc = frappe.get_doc({
				"doctype": "Role",
				"role_name": r["role_name"],
				"desk_access": r["desk_access"],
			})
			role_doc.insert(ignore_permissions=True)


def setup_number_cards():
	cards = [
		{
			"name": "Total Assessments",
			"label": "Total Assessments",
			"document_type": "Assessment",
			"function": "Count",
			"is_public": 1,
			"module": "Assessment Hub",
			"color": "#2490EF",
		},
		{
			"name": "Total Questions",
			"label": "Total Questions",
			"document_type": "Question",
			"function": "Count",
			"is_public": 1,
			"module": "Assessment Hub",
			"color": "#28A745",
		},
	]
	for card in cards:
		if not frappe.db.exists("Number Card", card["name"]):
			doc = frappe.get_doc({
				"doctype": "Number Card",
				**card
			})
			doc.insert(ignore_permissions=True)

