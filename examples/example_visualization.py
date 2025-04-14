"""
Example script demonstrating the graph visualization functionality.

This script shows how to generate different types of graph visualizations
from crawler data or by running a crawler with visualization enabled.
"""

import os
import argparse
from vibe_scraping import (
    crawl_site,
    generate_crawl_graph,
    generate_domain_graph,
    create_dynamic_graph
)

def visualize_existing_data(args):
    """Generate visualizations from existing crawler data."""
    print(f"Generating visualizations from data in: {args.data_path}")
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate page-level graph
    page_graph = generate_crawl_graph(
        args.data_path,
        output_file=os.path.join(args.output_dir, "page_graph.png"),
        max_nodes=args.max_nodes,
        title=f"Page-Level Graph - {os.path.basename(args.data_path)}",
        with_labels=True
    )
    if page_graph:
        print(f"Page-level graph saved to: {page_graph}")
    
    # Generate domain-level graph
    domain_graph = generate_domain_graph(
        args.data_path,
        output_file=os.path.join(args.output_dir, "domain_graph.png"),
        title=f"Domain-Level Graph - {os.path.basename(args.data_path)}",
        node_size_factor=100
    )
    if domain_graph:
        print(f"Domain-level graph saved to: {domain_graph}")
    
    # Try to generate interactive graph
    try:
        interactive_graph = create_dynamic_graph(
            args.data_path,
            output_file=os.path.join(args.output_dir, "interactive_graph.html")
        )
        if interactive_graph:
            print(f"Interactive graph saved to: {interactive_graph}")
            print("Open this file in a web browser to explore the interactive visualization.")
    except ImportError:
        print("Could not create interactive graph. Install pyvis with: pip install pyvis")
    except Exception as e:
        print(f"Error creating interactive graph: {str(e)}")

def crawl_and_visualize(args):
    """Run a crawl and generate visualizations."""
    print(f"Crawling {args.url} and generating visualizations")
    
    # Run the crawler with graph generation enabled
    stats = crawl_site(
        start_url=args.url,
        output_dir=args.output_dir,
        max_depth=args.depth,
        max_pages=args.max_pages,
        crawl_method=args.method,
        delay=args.delay,
        follow_subdomains=args.subdomains,
        use_selenium=args.selenium,
        generate_graph=True,
        graph_type="page"  # Start with page-level graph
    )
    
    print(f"\nCrawl completed. Crawled {stats['pages_crawled']} pages.")
    
    if 'graph_file' in stats:
        print(f"Page-level graph saved to: {stats['graph_file']}")
    
    # Now generate additional visualizations
    try:
        # Generate domain-level graph
        domain_graph = generate_domain_graph(
            args.output_dir,
            title=f"Domain-Level Graph - {args.url}"
        )
        if domain_graph:
            print(f"Domain-level graph saved to: {domain_graph}")
        
        # Try to generate interactive graph
        interactive_graph = create_dynamic_graph(args.output_dir)
        if interactive_graph:
            print(f"Interactive graph saved to: {interactive_graph}")
            print("Open this file in a web browser to explore the interactive visualization.")
    except Exception as e:
        print(f"Error generating additional visualizations: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Graph visualization example")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Visualization from existing data
    visualize_parser = subparsers.add_parser(
        "visualize", 
        help="Generate visualizations from existing crawler data"
    )
    visualize_parser.add_argument(
        "data_path", 
        help="Path to the directory containing crawl data"
    )
    visualize_parser.add_argument(
        "--output-dir", 
        default="visualizations",
        help="Directory to save visualizations"
    )
    visualize_parser.add_argument(
        "--max-nodes", 
        type=int, 
        default=100,
        help="Maximum number of nodes in page-level graph"
    )
    
    # Crawl and visualize
    crawl_parser = subparsers.add_parser(
        "crawl", 
        help="Crawl a website and generate visualizations"
    )
    crawl_parser.add_argument(
        "url", 
        help="URL to start crawling from"
    )
    crawl_parser.add_argument(
        "--output-dir", 
        default="crawled_data",
        help="Directory to save crawl data and visualizations"
    )
    crawl_parser.add_argument(
        "--depth", 
        type=int, 
        default=2,
        help="Maximum crawl depth"
    )
    crawl_parser.add_argument(
        "--max-pages", 
        type=int, 
        default=50,
        help="Maximum number of pages to crawl"
    )
    crawl_parser.add_argument(
        "--method", 
        choices=["breadth", "depth"], 
        default="breadth",
        help="Crawling method"
    )
    crawl_parser.add_argument(
        "--delay", 
        type=float, 
        default=1.0,
        help="Delay between requests in seconds"
    )
    crawl_parser.add_argument(
        "--subdomains", 
        action="store_true",
        help="Follow links to subdomains"
    )
    crawl_parser.add_argument(
        "--selenium", 
        action="store_true",
        help="Use Selenium for JavaScript rendering"
    )
    
    args = parser.parse_args()
    
    if args.command == "visualize":
        visualize_existing_data(args)
    elif args.command == "crawl":
        crawl_and_visualize(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 