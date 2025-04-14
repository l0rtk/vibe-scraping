from vibe_scraping.crawler import WebCrawler

crawler = WebCrawler(
    start_url="https://www.radiotavisupleba.ge/",
    max_depth=1,
    max_pages=10,
    save_path="radiotavisupleba",
    generate_graph=True,
    graph_type="interactive",
)

crawler.crawl()

"""
This will crawl the website and save the content to the "radiotavisupleba" directory.

"""