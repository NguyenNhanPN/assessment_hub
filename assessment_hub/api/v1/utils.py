# Copyright (c) 2026, Frappe Developer and contributors
# For license information, please see license.txt

import json
from datetime import date, datetime
from functools import wraps
import frappe
from frappe import _
from werkzeug.wrappers import Response


def json_serializer(obj):
	if isinstance(obj, (datetime, date)):
		return str(obj)
	return str(obj)


def api_success(data, status=200):
	payload = json.dumps({"data": data}, default=json_serializer)
	return Response(payload, status=status, mimetype="application/json")


def api_error(message, code="ERROR", status=400):
	payload = json.dumps({
		"errors": [
			{
				"message": str(message),
				"code": str(code)
			}
		]
	})
	return Response(payload, status=status, mimetype="application/json")


def partner_api(allowed_roles=None):
	"""
	Decorator for Partner REST API endpoints:
	- Verifies Token Authentication / Session
	- Validates User Roles
	- Enforces unified response contract:
	  Success: {"data": ...}
	  Failure: {"errors": [{"message": "...", "code": "..."}]}
	"""
	if allowed_roles is None:
		allowed_roles = ["Assessment Viewer", "Assessment Manager"]

	def decorator(fn):
		@wraps(fn)
		def wrapper(*args, **kwargs):
			# 1. Authentication check
			if frappe.session.user == "Guest":
				return api_error("Authentication required. Please provide valid API credentials.", "UNAUTHORIZED", 401)

			# 2. Authorization / Role check
			user_roles = frappe.get_roles(frappe.session.user)
			if "System Manager" not in user_roles and frappe.session.user != "Administrator":
				has_role = any(role in user_roles for role in allowed_roles)
				if not has_role:
					return api_error(
						f"Permission denied. Required roles: {', '.join(allowed_roles)}",
						"FORBIDDEN",
						403
					)

			# 3. Execution & Exception handling
			try:
				result = fn(*args, **kwargs)
				if isinstance(result, Response):
					return result
				return api_success(result)
			except frappe.DoesNotExistError as e:
				return api_error(str(e) or "Resource not found.", "NOT_FOUND", 404)
			except frappe.PermissionError as e:
				return api_error(str(e) or "Permission denied.", "FORBIDDEN", 403)
			except frappe.ValidationError as e:
				return api_error(str(e) or "Validation failed.", "VALIDATION_ERROR", 400)
			except ValueError as e:
				return api_error(str(e), "BAD_REQUEST", 400)
			except Exception as e:
				frappe.log_error(title="Partner API Error", message=frappe.get_traceback())
				return api_error(str(e) or "Internal server error.", "INTERNAL_SERVER_ERROR", 500)

		return wrapper
	return decorator


def create_test_credentials():
	"""
	Helper to generate API Key & Secret for testing partner roles.
	"""
	from assessment_hub.setup import setup_roles
	setup_roles()

	credentials = {}
	users_to_setup = [
		{"email": "partner_manager@example.com", "role": "Assessment Manager", "first_name": "Partner Manager"},
		{"email": "partner_viewer@example.com", "role": "Assessment Viewer", "first_name": "Partner Viewer"},
	]

	for uinfo in users_to_setup:
		email = uinfo["email"]
		if not frappe.db.exists("User", email):
			user = frappe.get_doc({
				"doctype": "User",
				"email": email,
				"first_name": uinfo["first_name"],
				"roles": [{"role": uinfo["role"]}],
				"send_welcome_email": 0,
			}).insert(ignore_permissions=True)
		else:
			user = frappe.get_doc("User", email)

		# Generate API key & secret
		if not user.api_key:
			user.api_key = frappe.generate_hash(length=16)

		api_secret = frappe.generate_hash(length=16)
		user.api_secret = api_secret
		user.save(ignore_permissions=True)

		credentials[uinfo["role"]] = {
			"email": email,
			"api_key": user.api_key,
			"api_secret": api_secret,
			"token": f"{user.api_key}:{api_secret}"
		}

	frappe.db.commit()
	print(json.dumps(credentials, indent=2))
	return credentials

