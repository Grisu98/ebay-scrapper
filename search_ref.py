import json
from ebay_searcher import EbaySearcher
import re
import os
import time

class SearchRefiner:

    def __init__(self, path: str, item_count: int, api_key):
        self.path = path
        self.api_key = api_key
        self.pages = item_count // 100
        self.api_caller = EbaySearcher
        self.last_item_id = self.find_last_endpoint()

    @property
    def strip_patterns(self):
        return [
            r"chromebook", r"celeron", r"2\s{,4}gb", r"1\s{,4}gb", r"ddr\s{,4}3",
            r"ddr\s{,4}2", r"retro", r"konvolut", r"retro", r"athlon", r"pentium",
            r"core\s{,4}2\s{,4}Duo", r"siemens"
        ]

    def make_search(self):
        complete_items = self._make_search()

        print(f"{len(complete_items)} items found")

        for index, item in enumerate(complete_items):
            if item["itemId"] == self.last_item_id:
                complete_items = complete_items[index:]
                break

        print(f"{len(complete_items)} items after removing already viewed")

        stripped_info_items = self.strip_data(complete_items)

        stripped_items = self.strip_useless(stripped_info_items)
        print(f"{len(stripped_items)} items after removing patterns")

        self.create_html(stripped_items)

    def find_last_endpoint(self):

        exists = os.path.isfile("outputs/clean_output.html")

        if not exists:
            return 0

        with open("outputs/clean_output.html", "r", encoding="utf-8") as file:
            html_string = file.read()
            last_href = html_string.rfind("href")
            first_dq = html_string.find('"',last_href)
            second_dq = html_string.find('"',first_dq + 1)
            item_link = html_string[first_dq+1:second_dq]
            last_slash = item_link.rfind("/")
            last_item_id = item_link[last_slash+1:]
        
            return last_item_id
    

    def _make_search(self):
        """
        api can only return 100 max items so this will split it into
        multiple calls 
        """

        page_number = 1
        all_items = []
        while True:
            page_filter = {"paginationInput": {"pageNumber": page_number}}
            call = self.api_caller("data/input.json", filters=page_filter, api_key=self.api_key)
            response = call.create()
            all_items.extend(response)
            if (page_number >= self.pages):
                break
            page_number += 1
            print(f"we are on page {page_number}, sleeping 2 sec for next call")
            time.sleep(2)
        return all_items

    def strip_data(self, data):
        stripped_arr = []

        for item in data:
            watchers = item["listingInfo"].get("watchCount", "0")
            img_link: str = item["galleryURL"]
            size = img_link.find("s-l140")

            if size:
                img_link = img_link.replace("s-l140", "s-l500")

            item_data = {
                "title": item["title"],
                "image": img_link,
                "price": item["sellingStatus"]["convertedCurrentPrice"]["#text"],
                "URL": item["viewItemURL"],
                "bids": item["sellingStatus"]["bidCount"],
                "current_price": item["sellingStatus"]["currentPrice"]["#text"],
                "category": item["primaryCategory"]["categoryName"],
                "watchers": watchers

            }
            stripped_arr.append(item_data)

        return stripped_arr

    def strip_useless(self, data):

        for index, item in enumerate(data):
            for pattern in self.strip_patterns:
                match = re.search(pattern, item["title"], re.IGNORECASE)
                if match:
                    data.pop(index)

        return data

    def create_html(self, data):
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
        html_header = '''
        <head>
            <title>JSON to HTML</title>
                <link rel="stylesheet" type="text/css" href="styles.css">
        </head>
        '''

        with open('outputs/clean_output.html', 'w', encoding="utf-8") as file:

            file.write(html_header)

            for item in data:
                text = item['title']
                image_link = item['image']
                url = item["URL"]

                # Create HTML content
                html_content = html_template.format(
                    text=text, image_link=image_link, url=url)

                # Write HTML content to the file
                file.write(html_content)