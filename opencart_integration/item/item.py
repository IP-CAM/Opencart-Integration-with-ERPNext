import frappe
import requests
from frappe.utils.data import today
import requests
from opencart_integration.opencart_integration.doctype.opencart_log.opencart_log import make_opencart_log
import json
from datetime import datetime, timedelta
from erpnext import get_default_company
from frappe import _
from frappe.utils import (
    add_days,
    add_months,
    cint,
    date_diff,
    flt,
    get_first_day,
    get_last_day,
    get_link_to_form,
    getdate,
    rounded,
    today,
)

opencart_settings = frappe.get_doc("Opencart Settings")

@frappe.whitelist()
def fetch_oc_items():
    if opencart_settings.get("enable") == 1:
        oc = OpenCart_Items()
        oc.call()

class OpenCart_Items:
    def _init_(self):
        self.items = []

    def call(self):
        try:
            self.page = 1
            value = True
            while (value):
                self.get_items()
                if self.items:
                    for self.item in self.items:
                        if self.item_exist():
                            self.create_item()
                else:
                    value = False
                self.page += 1
        except Exception as err:
            make_opencart_log(status="Error", exception=str(err))
    
    def get_items(self):
        url = "{}/api/api.php"
        headers = {
            'signature': opencart_settings.signature,
            'token': opencart_settings.api_token,
            'Cookie': 'currency=INR; language=en-gb; currency=INR; language=en-gb'
        }
        params = {
            "rquest":"getproducts",
            "language_id":1,
            "page":self.page           
        }
        response = requests.get(url.format(opencart_settings.api_url), params=params, headers=headers)
        response = response.json()
        if response.get("status") == "200":
            self.items = response.get("products")
        else:
            make_opencart_log(status="Error", exception=str(response))
        return
    
    def item_exist(self):
        item_code = frappe.get_value("Item",{"name":self.item.get("model")},["name"])
        item_exists = True
        if item_code:            
            item_exists = False
        return item_exists
    
    def create_item(self):
        disable = 0
        if self.item.get("status") == 0:
            disable = 1
        try:
            item_doc = frappe.get_doc({
                "doctype": "Item",
                "item_code": self.item.get("model"),
                "disable": disable,
                "product_id": self.item.get("product_id"),
                "item_name": self.item.get("name"),
                "item_group": opencart_settings.item_group,
                "is_stock_item": 0,
                "stock_uom": opencart_settings.stock_uom,
                "standard_rate": self.item.get("price"),
                "hsn": self.item.get("hsn"),
                "description": self.item.get("email"),
                "date_available": self.item.get("date_available"),
                "length": self.item.get("length"),
                "width": self.item.get("width"),
                "height": self.item.get("height"),
                "weight": self.item.get("weight"),
                "weight_class": self.item.get("weight_class"),
                "length_class": self.item.get("length_class"),
                "stock_status": self.item.get("stock_status"),
                "brand":self.item.get("manufacturer"),
            })
            item_doc.insert(ignore_mandatory=True)
            frappe.db.commit()
        except Exception as err:
            make_opencart_log(status="Error", exception=str(err)+str( "Product ID: ",self.item.get("product_id")))
        return