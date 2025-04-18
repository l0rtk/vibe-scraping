from vibe_scraping.crawler import WebCrawler

crawler = WebCrawler(
    start_url="https://www.radiotavisupleba.ge/",
    max_depth=2,
    max_pages=10000,
    save_path="radiotavisupleba",
    generate_graph=True,
    graph_type="page",
    delay=0.1,
    use_scrapy=True,
)

crawler.crawl()

"""
This will crawl the website and save the content to the "radiotavisupleba" directory.

"""