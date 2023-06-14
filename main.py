from search_ref import SearchRefiner
import json


with open("data/api.txt") as file:
    api_key = file.read()

refiner = SearchRefiner("data/input.json", 500, api_key=api_key)

all_items = refiner.make_search()



with open("data/final_out.json", "w") as file:
    json.dump(all_items,file)

