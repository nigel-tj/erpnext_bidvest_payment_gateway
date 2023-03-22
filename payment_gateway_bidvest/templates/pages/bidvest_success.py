from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
import json
from payment_gateway_bidvest.payment_gateway_bidvest.doctype.bidvest_settings.bidvest_settings import *

def get_context(context):
	# print(context)
	return context