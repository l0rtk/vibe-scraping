# Vibe Scraping

A sophisticated web crawler and scraper with interactive visualizations.

## Features

- Configurable web crawler with depth-first or breadth-first strategies
- Respects robots.txt and implements responsible crawling policies
- Multiple visualization options including interactive tree visualization
- Support for both standard crawler and Scrapy for high-performance crawling
- Selenium integration for JavaScript-heavy sites

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/vibe-scraping.git
cd vibe-scraping

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

## Basic Usage

```python
from vibe_scraping.crawler import WebCrawler

# Create and configure the crawler
crawler = WebCrawler(
    start_url="https://example.com/",
    max_depth=2,
    max_pages=100,
    save_path="example_data",
    generate_graph=True,
    graph_type="tree",  # Use the tree visualization
)

# Start the crawl
pages_crawled, graph_file = crawler.crawl()

print(f"Crawl completed. Processed {pages_crawled} pages.")
if graph_file:
    print(f"Visualization saved to: {graph_file}")
```

## Interactive Tree Visualization

The project includes a state-of-the-art interactive tree visualization that displays crawled pages in a hierarchical structure:

- Upside-down tree layout with the start URL at the top
- Interactive features including zoom, pan, and node expansion/collapse
- Search functionality to find specific URLs
- Color-coded by depth for better understanding
- Tooltips with detailed page information

To generate a tree visualization, set `graph_type="tree"` and `generate_graph=True` when creating your crawler instance.

For more details, see [Tree Visualization Documentation](docs/visualization.md).

## Command Line Usage

The package can also be used from the command line:

```bash
# Basic usage
python -m vibe_scraping.cli crawl https://example.com/ --output example_data --depth 2 --graph --graph-type tree

# For help
python -m vibe_scraping.cli --help
```

## Examples

Check the `examples/` directory for sample scripts:

- `basic_crawler.py`: Simple crawler with tree visualization
- `tree_visualization_example.py`: Test script for standalone visualization
- `basic_tree_crawler.py`: Demonstrates using the tree visualization

## License

MIT License
