from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
import json
from payment_gateway_bidvest.payment_gateway_bidvest.doctype.bidvest_settings.bidvest_settings import *


no_cache = 1

def get_context(context):
	context.no_cache = 1
	data = frappe.form_dict
	context.payment_details = data
	print('Checkout data',data)
	gateway_doc = frappe.get_doc(data.get('gateway_doctype'), data.get('gateway_docname'))
	context.gateway_details=gateway_doc.as_dict()
	#context.gateway_details.merchant_key=gateway_doc.get_password('merchant_key')
	submission_data={
		'chargetotal':data.get('amount') or '',
		'custom_str1':data.get('integration_request_id'),
		'name_first':data.get('payer_name') or '',
		'email_address':data.get('payer_email') or '',
		'oid':data.get('order_id') or '',
		'storename':context.gateway_details.get('storename') or '',
		'return_url':context.gateway_details.get('return_url') or f"{frappe.utils.get_url()}/bidvest_success",
		'cancel_url':f"{frappe.utils.get_url()}/bidvest_cancel?integration_request_id={data.get('integration_request_id')}",
		#'cancel_url':data.get('redirect_to') or '',
		'notify_url':f"{frappe.utils.get_url()}/bidvest_notify",
		'notify_url':context.gateway_details.get('notify_url') or f"{frappe.utils.get_url()}/bidvest_notify",
		'txndatetime':f"{frappe.utils.now_datetime().strftime('yyyy:MM:dd-HH:mm:ss')}",
		'timezone':f"{frappe.get_doc('System Settings').time_zone}",
		'currency': data.get('currency'),
		#'sharedsecret': context.gateway_details.get('passphrase') or '',
	}
	submission_data=build_submission_data(submission_data)
	submission_data['hash'] = generateApiSignature(submission_data, passPhrase=gateway_doc.get_password('passphrase'))
	context.payment_details['hash']=submission_data['hash']
	context.submission_data=submission_data
	web_ref_doc =  frappe.get_doc(data.get('reference_doctype'), data.get('reference_docname'))
	context.reference_details = web_ref_doc.as_dict()
	
	if data.get('reference_doctype')=='Web Form':
		
		reference_doc = frappe.get_doc(web_ref_doc.doc_type, data.get('order_id'))
		meta = frappe.get_meta(web_ref_doc.doc_type)
		if meta.has_field('paid'):
			if reference_doc.paid:
				frappe.local.response["type"] = "redirect"
				frappe.local.response["location"] = data.get('redirect_to')
				raise frappe.Redirect
	return context




@frappe.whitelist(allow_guest=True)
def make_payment(payload_nonce, data, reference_doctype, reference_docname):
	data = json.loads(data)

	data.update({
		"payload_nonce": payload_nonce
	})

	gateway_controller = get_gateway_controller(reference_docname)
	data =  frappe.get_doc("Bidvest Settings", gateway_controller).create_payment_request(data)
	frappe.db.commit()
	return data
