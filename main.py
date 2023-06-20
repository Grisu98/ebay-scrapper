from search_refiner import SearchRefiner


def main():
    path = "searcher.yaml"
    global search 
    search = SearchRefiner(path)
    search.create_html()

if __name__ == "__main__":
    main()
