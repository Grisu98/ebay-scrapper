import json
import requests
from ebaysdk.finding import Connection as finding
from dict2xml import dict2xml
import xml.etree.ElementTree as ET
import xmltodict


class EbaySearcher:
    """
    file_path (str): The path to the file.
    api (dict, optional): The API settings for the searcher. Defaults to None.
    filters (dict, optional): The filters for the searcher. Defaults to None.
    debug (bool, optional): Debug mode flag. Defaults to False.
    """

    def __init__(self, file_path: str, api_key, filters: dict = None,force: bool = True) -> None:
        self.file_path = file_path
        self.filters = filters
        self.api_key = api_key
        self.api_settings = self.default_api
        self.xml = self.create_xml(file_path)
        self.force = force

    @property
    def default_api(self):
        return {
            "api_endpoint": "findItemsAdvanced",
            "api_url": "http://www.ebay.com/marketplace/search/v1/services",
        }

    def create(self):

        html_response = self.makeApiCall()

        if not html_response:
                if not self.force:
                    raise Exception("response was empty")
                return []

        self.html_response = html_response
        response = self.handleResponse(html_response)
        self.response = response
        tester = response["findItemsAdvancedResponse"]["searchResult"].get("@count")
        if not int(tester):
            if not self.force:
                raise Exception("didnt get any items back. Probably ebay api problem")
            self.items = []
            print("response had no items")
        else:
            self.items = response["findItemsAdvancedResponse"]["searchResult"]["item"]

        return self.items

    def create_xml(self, path):
        """
        reads the provided data in and parses it in a xml for
        the body of the api call
        """

        with open(path, "r") as file:
            raw_xml = json.load(file)

        if self.filters:
            raw_xml |= self.filters

        xml = dict2xml(raw_xml)
        # trow starting and ending on it
        starter = f'<?xml version="1.0" encoding="UTF-8"?><{self.api_settings["api_endpoint"]}Request xmlns="{self.api_settings["api_url"]}">'
        ender = f'</{self.api_settings["api_endpoint"]}Request>'
        xml = starter + xml + ender

        with open("data/out.xml", "w")as f:
            f.write(xml)

        return xml

    def makeApiCall(self):
        """
        making the actual call to the ebay api
        TODO: remove hardcoded api key
        """

        api_url = "https://svcs.ebay.com/services/search/FindingService/v1"
        headers = {"Content-Type": "text/xml",
                   "X-EBAY-SOA-SECURITY-APPNAME": self.api_key,
                   'X-EBAY-SOA-SERVICE-NAME': 'FindingService',
                   'X-EBAY-SOA-GLOBAL-ID': 'EBAY-DE',
                   'X-EBAY-SOA-OPERATION-NAME': 'findItemsAdvanced'
                   }

        response = requests.post(api_url, data=self.xml, headers=headers)

        return response

    def handleResponse(self, response):
        """
        look if the call failed or not and return the found items
        """

        if not response.status_code == 200:
            raise Exception("api call failed" + str(response.status_code))

        body = response.text
        body = xmltodict.parse(body)

        return body

    # TODO: factor this out
    def strip_data(self, response):
        stripped_arr = []

        for item in response:
            watchers = item["listingInfo"].get("watchCount", "0")
            img_link: str = item["galleryURL"]
            size = img_link.find("s-l140")

            if size:
                img_link = img_link.replace("s-l140", "s-l500")

            data = {
                "title": item["title"],
                "image": img_link,
                "price": item["sellingStatus"]["convertedCurrentPrice"]["#text"],
                "URL": item["viewItemURL"],
                "bids": item["sellingStatus"]["bidCount"],
                "current_price": item["sellingStatus"]["currentPrice"]["#text"],
                "category": item["primaryCategory"]["categoryName"],
                "watchers": watchers

            }
            stripped_arr.append(data)

        return stripped_arr
