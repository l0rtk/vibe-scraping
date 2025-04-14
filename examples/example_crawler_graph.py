"""
Example script demonstrating the WebCrawler's built-in graph visualization capability.

This script shows how to use the WebCrawler directly with graph visualization enabled.
"""

import argparse
import os
from vibe_scraping import WebCrawler

def main():
    parser = argparse.ArgumentParser(description="Web crawler with graph visualization")
    parser.add_argument("url", help="URL to start crawling from")
    parser.add_argument("--output", default="crawled_data", help="Output directory")
    parser.add_argument("--depth", type=int, default=2, help="Maximum crawl depth")
    parser.add_argument("--pages", type=int, default=20, help="Maximum number of pages to crawl")
    parser.add_argument("--method", choices=["breadth", "depth"], default="breadth", help="Crawling method")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds")
    parser.add_argument(
        "--auto-graph",
        action="store_true",
        help="Generate graph automatically after crawling"
    )
    parser.add_argument(
        "--graph-type", 
        choices=["page", "domain", "interactive", "all"], 
        default="page", 
        help="Type of graph to generate (all = generate all types)"
    )
    parser.add_argument("--title", help="Custom title for the graph")
    args = parser.parse_args()
    
    print(f"Crawling {args.url} with {args.method}-first search")
    print(f"Maximum depth: {args.depth}, Maximum pages: {args.pages}")
    
    if args.auto_graph:
        print(f"Automatically generating a {args.graph_type} graph after crawling")
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Create crawler with optional automatic graph visualization
    crawler = WebCrawler(
        start_url=args.url,
        max_depth=args.depth,
        max_pages=args.pages,
        delay=args.delay,
        save_path=args.output,
        crawl_method=args.method,
        respect_robots_txt=True,
        generate_graph=args.auto_graph,  # Enable automatic graph visualization
        graph_type=args.graph_type if args.graph_type != "all" else "page",
        graph_title=args.title
    )
    
    # Start crawling
    pages_crawled, auto_graph_file = crawler.crawl()
    
    # Print crawl results
    print(f"\nCrawl completed: {pages_crawled} pages crawled")
    if auto_graph_file:
        print(f"Automatic graph visualization saved to: {auto_graph_file}")
    
    # Manually generate specific graph types if not generated automatically
    # or if "all" was specified
    if not args.auto_graph or args.graph_type == "all":
        print("\nGenerating graph visualizations:")
        
        # Create a visualizations directory
        vis_dir = os.path.join(args.output, "visualizations")
        os.makedirs(vis_dir, exist_ok=True)
        
        if args.graph_type == "page" or args.graph_type == "all":
            page_graph = crawler.generate_page_graph(
                title=args.title or f"Page Graph - {args.url}",
                output_file=os.path.join(vis_dir, "page_graph.png")
            )
            if page_graph:
                print(f"Page-level graph saved to: {page_graph}")
        
        if args.graph_type == "domain" or args.graph_type == "all":
            domain_graph = crawler.generate_domain_graph(
                title=args.title or f"Domain Graph - {args.url}",
                output_file=os.path.join(vis_dir, "domain_graph.png")
            )
            if domain_graph:
                print(f"Domain-level graph saved to: {domain_graph}")
        
        if args.graph_type == "interactive" or args.graph_type == "all":
            interactive_graph = crawler.generate_interactive_graph(
                output_file=os.path.join(vis_dir, "interactive_graph.html")
            )
            if interactive_graph:
                print(f"Interactive graph saved to: {interactive_graph}")
                print("Open this HTML file in a web browser to explore the visualization")

if __name__ == "__main__":
    main() 