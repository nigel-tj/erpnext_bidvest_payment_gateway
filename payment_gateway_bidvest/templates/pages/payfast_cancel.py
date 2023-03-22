from __future__ import unicode_literals
import socket
from werkzeug.urls import url_parse
import frappe
from frappe import _
from frappe.utils import flt
from urllib.parse import parse_qsl, quote_plus, urlparse
import hashlib
import json
from payment_gateway_bidvest.payment_gateway_bidvest.doctype.bidvest_settings.bidvest_settings import validate_bidvest_host, validate_bidvest_signature, validate_bidvest_payment_amount, validate_bidvest_transaction

def get_context(context):
    # make sure that only bidvest host can update docs with url query
    is_valid_bidvest_host = validate_bidvest_host(url_parse(frappe.request.headers.get("Referer") or '').host or '')
    if is_valid_bidvest_host:
        bidvest_cancel_request = urlparse(frappe.request.url)
        bidvest_cancel_data = dict(parse_qsl(bidvest_cancel_request.query))
        print('bidvest_cancel_data', bidvest_cancel_data)
        integration_request = frappe.get_doc("Integration Request", bidvest_cancel_data.get('integration_request_id'))
        integration_data = frappe._dict(json.loads(integration_request.data))
        print('integration_data', integration_request.status)
        integration_request.db_set('status', 'Cancelled')
        integration_request.save(
            ignore_permissions=True, # ignore write permissions during insert
            ignore_version=True # do not create a version record
        )
        frappe.db.commit()
        integration_request.reload()
        integration_data = frappe._dict(json.loads(integration_request.data))
        print('integration_data', integration_request.status)
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = integration_data.get('redirect_to')
        raise frappe.Redirect
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = frappe.utils.get_url()
    raise frappe.Redirect
