import requests
import xmltodict
from dict2xml import dict2xml
from typing import Any, Union


class EbaySearcher:

    def __init__(self, request: dict[Any, Any], ignore_errors: bool = True):
        self.header: dict = request["header"]
        self.body = self.create_body(request["body"])
        self.ignore = ignore_errors

    def create_body(self, body_dict):
        xml = dict2xml(body_dict)

        starter = '<?xml version="1.0" encoding="UTF-8"?><findItemsAdvancedRequest xmlns="http://www.ebay.com/marketplace/search/v1/services">'
        ender = '</findItemsAdvancedRequest>'
        xml = starter + xml + ender
        xml = xml.replace("\n","")
        return xml

    def make_api_call(self)-> list:
        """
        making the actual call to the ebay api. Returns a list of all found items
        """

        try:
            response = requests.post(
                "https://svcs.ebay.com/services/search/FindingService/v1",
                data=self.body,
                headers=self.header
            )
        except Exception as e:
            print("failed at making the api call", e)
            if self.ignore:
                print("skipping over this response")
                return []
            else:
                raise Exception(e)
            
        if response is not None:
            response_dict = xmltodict.parse(response.text)

            if response.status_code == 200 or response_dict["findItemsAdvancedResponse"]["ack"] != "Failure":
                item_count = response_dict["findItemsAdvancedResponse"]["searchResult"].get(
                    "@count")
                if self.ignore and item_count == "0":
                    items = []
                    return items
                else:
                    items:list = response_dict["findItemsAdvancedResponse"]["searchResult"]["item"]
                    return items

            else:
                raise ConnectionError(
                    "got following code", response.status_code)
        else:
            return []
