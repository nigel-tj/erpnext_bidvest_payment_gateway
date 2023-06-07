# Copyright (c) 2022, Alberto Gutierrez and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import json
from datetime import datetime
import urllib.parse
import hashlib
import requests
import socket
from urllib.parse import urlencode
from frappe.utils import get_url, call_hook_method, cint, flt, format_datetime
from frappe.integrations.utils import make_get_request, make_post_request, create_request_log
from payments.utils import create_payment_gateway

class BidvestSettings(Document):
	supported_currencies = [
		"ZAR"
	]

	currency_wise_minimum_charge_amount = {
		'ZAR': 5
	}

	def on_update(self):
		create_payment_gateway('Bidvest-' + self.gateway_name, settings='Bidvest Settings', controller=self.gateway_name)
		call_hook_method('payment_gateway_enabled', gateway='Bidvest-' + self.gateway_name)

	def validate_transaction_currency(self, currency):
		if currency not in self.supported_currencies:
			frappe.throw(_("Please select another payment method. Bidvest does not support transactions in currency '{0}'").format(currency))

	def validate_minimum_transaction_amount(self, currency, amount):
		if currency in self.currency_wise_minimum_charge_amount:
			if flt(amount) < self.currency_wise_minimum_charge_amount.get(currency, 0.0):
				frappe.throw(_("For currency {0}, the minimum transaction amount should be {1}").format(currency,
					self.currency_wise_minimum_charge_amount.get(currency, 0.0)))

	def get_payment_url(self, **kwargs):
		# add payment gateway details, don't send secrets in url
		kwargs['bidvest_url']=f"{environment_url(self.environment)}/connect/gateway/processing"
		kwargs['bidvest_domain']=f"{environment_url(self.environment)}"
		kwargs['gateway_docname']=self.gateway_name
		kwargs['gateway_doctype']='Bidvest Settings'
		self.integration_request = create_request_log(kwargs, "Host", "Bidvest")
		# bidvest allows for up to 5 custom string fields. We can pass the integration request id 
		kwargs['integration_request_id']=self.integration_request.name
		print("***** paypent kwargs : get_payment_url ****** ", kwargs)
		return get_url("./bidvest_checkout?{0}".format(urlencode(kwargs)))

def get_gateway_controller(doc):
	payment_request = frappe.get_doc("Payment Request", doc)
	gateway_controller = frappe.db.get_value("Payment Gateway", payment_request.payment_gateway, "gateway_controller")
	return gateway_controller

def get_ordered_fields():
	# bidvest validates against a particular order before processing for payment
	ordered_fields = [
		'storename', 'txndatetime', 'chargetotal', 'currency', 'sharedsecret','return_url','cancel_url','notify_url', # merchant details
		'name_first','name_last','email_address','cell_number', # customer details
		'm_payment_id','item_name','item_description', # transaction details
		'custom_str4','custom_str5', # transaction custom details
		'custom_int1','custom_int2','custom_int3','custom_int4','custom_int5', # transaction custom details
		
		'email_confirmation','confirmation_address', # transaction options
	]
	return ordered_fields

def build_submission_data(data):
	submission_data={
		key:data.get(key) or '' for key in data.keys()
	}
	return submission_data

def generateApiSignature(dataArray, passPhrase = ''):
	payload = "" 
	print('passed array',get_ordered_fields())
	for key in get_ordered_fields():
		if dataArray.get(key):
			print('key in get_ordered_fields', key)
			payload += key + "=" + urllib.parse.quote_plus(dataArray[key].replace("+", " ")) + "&"
	# After looping through, cut the last & or append your passphrase
	payload = payload[:-1]
	if passPhrase!='': payload += f"&passphrase={passPhrase}"

	# Concatenate the fields in the specified order
	message = dataArray['storename'] + dataArray['txndatetime'] + dataArray['chargetotal'] + dataArray['currency'] + passPhrase
	#message = '17221439602013:07:16-09:57:081.00826Sharedsecret'
	print('**** message ****', message)
	
	#convert to hexadecimal
	hexadecimal_string = convert_string_to_ascii(message)
	print('**** hexadecimal_string *****', hexadecimal_string)
	
	# Generate the SHA-256 hash of the message
	hash_object = hashlib.sha256(hexadecimal_string.encode('utf-8'))

	return hash_object.hexdigest()

def environment_url(env):
	if env=='Live': return 'https://www.ipg-online.com/'
	return 'https://www.ipg-online.com/'

def validate_bidvest_signature(pfData, pfParamString):
	# Generate our signature from bidvest parameters
	signature = hashlib.md5(pfParamString.encode()).hexdigest()
	return (pfData.get('signature') == signature)

def validate_bidvest_host(host=''):    
	valid_hosts = [
		'192.168.100.30',
		'erp.stokdirect.africa'
    ]
	valid_ips = []

	for item in valid_hosts:
		ips = socket.gethostbyname_ex(item)
		if ips:
			for ip in ips:
				if ip:
					valid_ips.append(ip)
    # Remove duplicates from array
	clean_valid_ips = []
	for item in valid_ips:
		# Iterate through each variable to create one list
		if isinstance(item, list):
			for prop in item:
				if prop not in clean_valid_ips:
					clean_valid_ips.append(prop)
		else:
			if item not in clean_valid_ips:
				clean_valid_ips.append(item)

    # Security Step 3, check if referrer is valid
	if host not in clean_valid_ips:
		return False
	else:
		return True 

def validate_bidvest_payment_amount(amount, pfData):
    return not (abs(float(amount)) - float(pfData.get('amount_gross'))) > 0.01

def validate_bidvest_transaction(pfParamString, pfHost = 'https://www.ipg-online.com'):
    url = f"{pfHost}/eng/query/validate"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
        }
    response = requests.post(url, data=pfParamString, headers=headers)
    return response.text == 'VALID'

def convert_string_to_ascii(my_string):
  hex_representation = []

  for char in my_string:
    ascii_value = ord(char)
    hex_value = hex(ascii_value)[2:].zfill(2)
    hex_representation.append(hex_value)

  ascii_hex_representation = ''.join(hex_representation)

  return ascii_hex_representation


@frappe.whitelist()
def test_connection(data):
	data = json.loads(data)
	my_datetime = datetime.now()
	timestamp_var = format_datetime(my_datetime, "yyyy:MM:dd-HH:mm:ss")
	env = data.get('environment') or 'Sandbox'
	data.pop('environment', None)
	passphrase = data.get('passphrase') or ''
	data.pop('passphrase', None)
	data['storename']= data['storename']
	data['txndatetime']=timestamp_var
	data['chargetotal']='15.00'
	data['currency']='710'
	data['hash_algorithm']='SHA256'
	data['timezone']='Africa/Johannesburg'
	data['mode']='payonly'
	data['txntype']='sale'
	data['oid']='Test2-43662198'
	data['checkoutoption'] = 'combinedpage'
	data['responseSuccessURL'] = data['return_url']
	data['responseFailURL'] = data['cancel_url']
	signature = generateApiSignature(data, passPhrase=passphrase)
	data['hash']=signature
	print('test connection data', data)
	response = requests.post(f"{environment_url(env)}/connect/gateway/processing", 
		params=data,
		headers={
			'Accept': 'application/json',
			'Content-Type': 'application/json',
			'observe':'response',
			
		},
	)
	message = response.text
	message = response.text.replace('/connect/',f"{environment_url(env)}/connect/")
	#message = message.replace('/connect/',f"{environment_url(env)}/connect/")
	#message = message.replace('/connect/images/',f"{environment_url(env)}/connect/images/")
	#message = message.replace('/connect/js/',f"{environment_url(env)}/connect/js/")
	print('******response detail:', response.request.url)
	if env=='Live':
		message = 'Store ID and/or Merchant Key and/or Sharedphrase are either incorrect or does not exist in the bidvest Live environment. Please ensure that these are configured in the Developer Settings.'
		if response.status_code==200:
			message = 'Connection was successful.'
	return {'status_code':response.status_code, 'message': message}
	

