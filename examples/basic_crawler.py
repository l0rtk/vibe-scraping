from vibe_scraping.crawler import WebCrawler

crawler = WebCrawler(
    start_url="https://www.radiotavisupleba.ge/",
    max_depth=1,
    max_pages=10,
)

crawler.crawl()

"""
This will crawl the website and save the content to the "radiotavisupleba" directory.

"""