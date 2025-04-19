# Tree Visualization

The vibe-scraping tool provides an interactive tree visualization that displays the crawled pages in a hierarchical structure with the start URL at the top and child pages below.

## Features

- Interactive upside-down tree structure
- Start URL at the top with child nodes expanding downward
- Zoom and pan capabilities
- Node expansion/collapse
- Search functionality
- Color-coded by depth
- Tooltips with detailed information

## Using the Tree Visualization

To generate the tree visualization, set `graph_type="tree"` when creating your WebCrawler instance:

```python
from vibe_scraping.crawler import WebCrawler

crawler = WebCrawler(
    start_url="https://example.com/",
    max_depth=2,
    max_pages=100,
    save_path="example_data",
    generate_graph=True,
    graph_type="tree",
    delay=0.5,
)

pages_crawled, graph_file = crawler.crawl()

if graph_file:
    print(f"Tree visualization saved to: {graph_file}")
```

The visualization will be saved as an HTML file in your output directory.

## Viewing the Visualization

Open the generated HTML file in any modern web browser to interact with the visualization. You can:

- Click on nodes to expand or collapse them
- Use the zoom in/out buttons
- Pan the view by dragging
- Search for specific URLs using the search box
- Reset the view with the reset button
- Expand or collapse all nodes at once

## Scrapy Compatibility

**Note**: The tree visualization is currently only fully supported with the default crawler. There is a known issue when using the Scrapy adapter:

- When using `use_scrapy=True`, the metadata format is different and may not properly populate the information needed for the tree visualization.

If you need to use the tree visualization, it's recommended to use the standard crawler:

```python
# Use the standard crawler for tree visualization
crawler = WebCrawler(
    start_url="https://example.com/",
    max_depth=2,
    max_pages=100,
    generate_graph=True,
    graph_type="tree",
    use_scrapy=False,  # Set to False for tree visualization
)
```

## Creating a Standalone Visualization

You can also create a tree visualization for existing crawl data:

```python
from vibe_scraping.visualizer import create_tree_visualization

# Path to your crawl data directory
crawl_data_path = "your_crawl_data"

# Generate the visualization
viz_file = create_tree_visualization(crawl_data_path)
print(f"Visualization created: {viz_file}")
```

The crawl data directory must contain a `metadata.json` file with information about the crawled pages.
