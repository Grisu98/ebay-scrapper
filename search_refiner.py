from ebay_searcher import EbaySearcher
import yaml
from yaml import FullLoader
import re
import os
import time


class SearchRefiner:

    def __init__(self, data_path: str, verbose: bool = True):
        self.api_caller = EbaySearcher
        self._handle_settings(data_path)
        self.verbose = verbose

    def _handle_settings(self, data_path):

        with open(data_path, "r") as file:
            yaml_dict = yaml.load(file, FullLoader)

        class_settings, search_settings, advanced_settings = yaml_dict.values()

        self.request = self._create_api_request(
            class_settings, search_settings)
        self.settings = class_settings
        self.advanced_settings = advanced_settings

    def _create_api_request(self, class_settings, search_settings: dict):

        # make body
        body = {"itemFilter": []}
        for filter in search_settings["itemFilter"]:
            body["itemFilter"].append({"name": filter[0], "value": filter[1]})
        del search_settings["itemFilter"]
        tester = search_settings.get("keywords")
        if not search_settings.get("keywords"):
            del search_settings["keywords"]
        body |= search_settings

        # make header
        headers = {"Content-Type": "text/xml",
                   "X-EBAY-SOA-SECURITY-APPNAME": class_settings["api_key"],
                   'X-EBAY-SOA-SERVICE-NAME': 'FindingService',
                   'X-EBAY-SOA-GLOBAL-ID': 'EBAY-DE',
                   'X-EBAY-SOA-OPERATION-NAME': 'findItemsAdvanced'
                   }

        return {"header": headers, "body": body}

    def make_search(self):

        page_number = 1
        all_items = []

        # how often do we need to call?
        while page_number <= self.settings["pages"]:
            time.sleep(2)
            self.request["body"]["paginationInput"] = {"pageNumber": page_number}
            call = self.api_caller(self.request)
            response = call.make_api_call()
            page_number += 1
            all_items.extend(response)
            

        return all_items

    def get_cleaned_items(self):
        """ TODO: implement removing my id"""
        items = self.make_search()
        all_items_len = len(items)
        if self.verbose:
            print(
                f"requested to get {self.settings['pages']} pages a 100 items. Got {all_items_len}")
        settings = self.advanced_settings
        # remove patterns
        if settings["remove_patterns"]:
            for index, item in enumerate(items):
                for pattern in self.advanced_settings["remove_patterns"]:
                    match = re.search(pattern, item["title"], re.IGNORECASE)
                    if match:
                        items.pop(index)
            if self.verbose:
                after_patterns_len = len(items)
                print(
                    f"{all_items_len - after_patterns_len} removed because of matching remove_pattern")

        return items

        # remove by id
        if len(self.advanced_settings["remove_id"]):
            for index, item in enumerate(items):
                if item["primaryCategory"]["categoryId"] == self.advanced_settings.remove_id:
                    items.pop(index)
            if self.verbose:

                print(
                    f"{ after_patterns_len - len(items)} removed because of matchin remove_id")  # type:ignore

    def remove_useless_data(self, items: list):

        stripped_items = []
        non_auction_counter = 0
        for item in items:
            watchers = item["listingInfo"].get("watchCount", "0")
            img_link = item["galleryURL"]
            size = img_link.find("s-l140")

            if size:
                img_link = img_link.replace("s-l140", "s-l400")
            
            if item["listingInfo"]["listingType"] != "Auction":
                non_auction_counter +=1
            data = {
                "title": item["title"],
                "image": img_link,
                "price": item["sellingStatus"]["convertedCurrentPrice"]["#text"],
                "URL": item["viewItemURL"],
                "current_price": item["sellingStatus"]["currentPrice"]["#text"],
                "category": item["primaryCategory"]["categoryName"],
                "watchers": watchers,
                "id": item["itemId"],
                # "bids": item["sellingStatus"]["bidCount"],

            }
            stripped_items.append(data)
        print(f"{non_auction_counter} where not auctions")
        return stripped_items

    def create_html(self):
        bloated_items = self.get_cleaned_items()
        items = self.remove_useless_data(bloated_items)
        last_seen_id = self._get_last_item()

        if last_seen_id:
            for index, item in enumerate(items):
                if item["id"] == last_seen_id:
                    items = items[index+1:]
                    if self.verbose:
                        print(f"{len(items)} left after removing already viewed")

        html_template = '''
        <div class="item-container">
            <div class="item-name">
                <a href="{url}">{text}</a>
            </div>
            <div class="item-image">
                <img loading="lazy" src="{image_link}">
            </div>    
        </div>
        '''
        html_header = f'''
            <head>
                <title>{self.settings['name']}</title>
                    <link rel="stylesheet" type="text/css" href="styles.css">
            </head>
            '''
        with open(f"outputs/{self.settings['name']}.html", 'w', encoding="utf-8") as file:
            file.write(html_header)

            for item in items:
                text = item['title']
                image_link = item['image']
                url = item["URL"]

                # Create HTML content
                html_content = html_template.format(
                    text=text, image_link=image_link, url=url)

                # Write HTML content to the file
                file.write(html_content)

    def _get_last_item(self) -> str:

        exists = os.path.isfile(f"outputs/{self.settings['name']}.html")

        if exists:
            with open(f"outputs/{self.settings['name']}.html", "r", encoding="utf-8") as file:
                html_string = file.read()
                last_href = html_string.rfind("href")
                first_dq = html_string.find('"', last_href)
                second_dq = html_string.find('"', first_dq + 1)
                item_link = html_string[first_dq+1:second_dq]
                last_slash = item_link.rfind("/")
                last_item_id = item_link[last_slash+1:]
            return last_item_id

        return ""
