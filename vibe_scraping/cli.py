#!/usr/bin/env python3
import argparse
import os
import json
import sys
from .main import process_product_page, MODEL_PRICING, scrape_webpage, extract_product_info, calculate_cost, print_results
from .crawler import crawl_site
from .visualizer import generate_crawl_graph, generate_domain_graph, create_dynamic_graph

def run_product_extraction(args):
    """Run the product extraction command"""
    # Check for conflicting options
    if args.selenium and args.no_selenium:
        print("Error: Cannot use both --selenium and --no-selenium options")
        return
    
    # Check if using saved content
    if args.use_saved:
        if not os.path.exists(args.use_saved):
            print(f"Error: Saved content file '{args.use_saved}' not found")
            return
        
        try:
            with open(args.use_saved, 'r', encoding='utf-8') as f:
                text = f.read()
            
            print(f"Loaded {len(text)} characters from '{args.use_saved}'")
            
            # Process the text through the model
            try:
                product_info = extract_product_info(text, args.model, args.prompt, max_retries=args.max_retries)
                cost_info = calculate_cost(product_info["usage"], args.model)
                
                # Print results
                if args.quiet:
                    print(product_info["content"])
                else:
                    print_results(product_info, cost_info, args.model)
            except Exception as e:
                print(f"Error processing content with LLM: {str(e)}")
                print("Content was loaded but could not be processed by the model.")
        except Exception as e:
            print(f"Error reading saved content: {str(e)}")
        
        return
    
    # Process with web scraping
    text = None
    
    if args.selenium:
        # Import selenium_scraper only when needed
        try:
            from .selenium_scraper import scrape_with_selenium
            from bs4 import BeautifulSoup
            
            print(f"Scraping {args.url} with Selenium {'(headless)' if args.headless else '(with browser window)'}...")
            html_content = scrape_with_selenium(args.url, headless=args.headless)
            
            if html_content:
                # Parse the HTML with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Clean up the content
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Extract text
                text = soup.get_text(separator=' ', strip=True)
                print(f"Successfully retrieved {len(text)} characters using Selenium")
                
                # Save content if requested
                if args.save_content:
                    try:
                        with open(args.save_content, 'w', encoding='utf-8') as f:
                            f.write(text)
                        print(f"Saved scraped content to '{args.save_content}'")
                    except Exception as e:
                        print(f"Error saving content: {str(e)}")
                
                # Process the text through the model
                try:
                    product_info = extract_product_info(text, args.model, args.prompt, max_retries=args.max_retries)
                    cost_info = calculate_cost(product_info["usage"], args.model)
                    
                    # Print results
                    if args.quiet:
                        print(product_info["content"])
                    else:
                        print_results(product_info, cost_info, args.model)
                except Exception as e:
                    print(f"Error processing content with LLM: {str(e)}")
                    if args.save_content:
                        print(f"Content was saved to '{args.save_content}' but could not be processed by the model.")
                        print(f"You can try again later using: --use-saved {args.save_content}")
            else:
                print("Failed to retrieve content with Selenium")
        except ImportError:
            print("Error: Selenium is not installed. Run 'pip install selenium webdriver-manager' to use this feature.")
        except Exception as e:
            print(f"Error during Selenium scraping: {str(e)}")
    else:
        # Use standard process_product_page with optional selenium fallback
        try:
            # First just get the text content
            text = scrape_webpage(args.url, use_selenium_fallback=not args.no_selenium)
            
            if not text:
                print("Failed to retrieve the page content")
                return
            
            # Save content if requested
            if args.save_content:
                try:
                    with open(args.save_content, 'w', encoding='utf-8') as f:
                        f.write(text)
                    print(f"Saved scraped content to '{args.save_content}'")
                except Exception as e:
                    print(f"Error saving content: {str(e)}")
            
            # Now process with the LLM
            try:
                product_info = extract_product_info(text, args.model, args.prompt, max_retries=args.max_retries)
                cost_info = calculate_cost(product_info["usage"], args.model)
                
                # Print results
                if args.quiet:
                    print(product_info["content"])
                else:
                    print_results(product_info, cost_info, args.model)
            except Exception as e:
                print(f"Error processing content with LLM: {str(e)}")
                if args.save_content:
                    print(f"Content was saved to '{args.save_content}' but could not be processed by the model.")
                    print(f"You can try again later using: --use-saved {args.save_content}")
        except Exception as e:
            print(f"Error during scraping process: {str(e)}")

def run_crawler(args):
    """Run the web crawler command"""
    try:
        print(f"Starting crawl from {args.url}")
        print(f"Max depth: {args.depth}, Max pages: {args.pages}")
        print(f"Method: {args.method}, Delay: {args.delay}s")
        print(f"Output directory: {args.output}")
        
        if args.scrapy:
            print("Using Scrapy for faster parallel crawling")
        
        if args.graph:
            print(f"Will generate {args.graph_type} graph after crawling")
        
        # Run the crawler
        stats = crawl_site(
            start_url=args.url,
            output_dir=args.output,
            max_depth=args.depth,
            max_pages=args.pages,
            crawl_method=args.method,
            delay=args.delay,
            follow_subdomains=args.subdomains,
            use_selenium=args.selenium,
            use_scrapy=args.scrapy,
            url_filter=args.filter,
            generate_graph=args.graph,
            graph_type=args.graph_type,
            graph_title=args.graph_title
        )
        
        # Print statistics
        print("\nCrawl completed:")
        print(f"Pages crawled: {stats['pages_crawled']}")
        print(f"Domain: {stats['domain']}")
        
        # Print graph information if generated
        if args.graph and 'graph_file' in stats:
            print(f"\nGraph visualization created: {stats['graph_file']}")
            if args.graph_type == 'interactive':
                print("Open this file in a web browser to view the interactive visualization.")
        
        # Save stats to a JSON file
        stats_file = os.path.join(args.output, "crawl_stats.json")
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"Statistics saved to: {stats_file}")
        
    except Exception as e:
        print(f"Error during crawling: {str(e)}")
        return 1
    
    return 0

def run_visualize(args):
    """Run the visualization command"""
    try:
        print(f"Generating visualization for crawl data in {args.data_path}")
        
        if args.type == "page":
            print("Generating page-level graph visualization...")
            graph_file = generate_crawl_graph(
                args.data_path,
                output_file=args.output,
                max_nodes=args.max_nodes,
                title=args.title,
                with_labels=not args.no_labels
            )
            if graph_file:
                print(f"Graph visualization saved to: {graph_file}")
            else:
                print("Failed to generate graph visualization")
                return 1
                
        elif args.type == "domain":
            print("Generating domain-level graph visualization...")
            graph_file = generate_domain_graph(
                args.data_path,
                output_file=args.output,
                title=args.title,
                node_size_factor=args.node_size,
                with_labels=not args.no_labels
            )
            if graph_file:
                print(f"Domain graph visualization saved to: {graph_file}")
            else:
                print("Failed to generate domain graph visualization")
                return 1
                
        elif args.type == "interactive":
            print("Generating interactive graph visualization...")
            try:
                graph_file = create_dynamic_graph(
                    args.data_path,
                    output_file=args.output
                )
                if graph_file:
                    print(f"Interactive graph visualization saved to: {graph_file}")
                    print("Open this file in a web browser to view the interactive graph.")
                else:
                    print("Failed to generate interactive graph visualization")
                    return 1
            except Exception as e:
                print(f"Error generating interactive graph: {str(e)}")
                print("To use interactive graphs, you need to install additional dependencies:")
                print("pip install pyvis networkx")
                return 1
                
    except Exception as e:
        print(f"Error during visualization: {str(e)}")
        return 1
    
    return 0

def main():
    # Create the top-level parser
    parser = argparse.ArgumentParser(description="Vibe Scraping - Web scraping and product information extraction")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Parser for the 'extract' command (original functionality)
    extract_parser = subparsers.add_parser("extract", help="Extract product information from a single URL")
    extract_parser.add_argument("url", help="URL of the product page to scrape")
    extract_parser.add_argument(
        "--model", 
        default="meta-llama/llama-4-scout-17b-16e-instruct",
        choices=list(MODEL_PRICING.keys()), 
        help="Model to use for extraction"
    )
    extract_parser.add_argument(
        "--quiet", 
        action="store_true", 
        help="Only output the extracted product information"
    )
    extract_parser.add_argument(
        "--prompt",
        help="Custom prompt to use for extraction. Default is to extract product name, price, description and attributes."
    )
    extract_parser.add_argument(
        "--selenium",
        action="store_true",
        help="Force using Selenium for scraping (for JavaScript-heavy sites)"
    )
    extract_parser.add_argument(
        "--no-selenium",
        action="store_true",
        help="Disable Selenium fallback (use only regular requests)"
    )
    extract_parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Selenium in headless mode (no visible browser window)"
    )
    extract_parser.add_argument(
        "--save-content",
        help="Save the scraped content to the specified file"
    )
    extract_parser.add_argument(
        "--use-saved",
        help="Use content from a previously saved file instead of scraping"
    )
    extract_parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retries for API calls (default: 3)"
    )
    
    # Parser for the 'crawl' command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl a website and collect pages")
    crawl_parser.add_argument("url", help="URL to start crawling from")
    crawl_parser.add_argument("--output", default="crawled_data", help="Directory to save the crawled data")
    crawl_parser.add_argument("--depth", type=int, default=2, help="Maximum crawl depth")
    crawl_parser.add_argument("--pages", type=int, default=100, help="Maximum number of pages to crawl")
    crawl_parser.add_argument("--method", choices=["breadth", "depth"], default="breadth", help="Crawling method")
    crawl_parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds")
    crawl_parser.add_argument("--subdomains", action="store_true", help="Follow links to subdomains")
    crawl_parser.add_argument("--selenium", action="store_true", help="Use Selenium for JavaScript rendering if needed")
    crawl_parser.add_argument("--scrapy", action="store_true", help="Use Scrapy for faster parallel crawling")
    crawl_parser.add_argument("--filter", help="Regular expression pattern for URLs to follow")
    
    # Graph visualization options for crawl command
    crawl_parser.add_argument("--graph", action="store_true", help="Generate a graph visualization after crawling")
    crawl_parser.add_argument("--graph-type", choices=["page", "domain", "interactive"], default="page", 
                            help="Type of graph to generate (default: page)")
    crawl_parser.add_argument("--graph-title", help="Title for the graph visualization")
    
    # Parser for the 'visualize' command (new functionality)
    visualize_parser = subparsers.add_parser("visualize", help="Visualize crawl results as graphs")
    visualize_parser.add_argument(
        "data_path", 
        help="Path to the directory containing crawl data"
    )
    visualize_parser.add_argument(
        "--type", 
        choices=["page", "domain", "interactive"], 
        default="page",
        help="Type of visualization to generate (default: page)"
    )
    visualize_parser.add_argument(
        "--output", 
        help="Output file path for the graph image or HTML file"
    )
    visualize_parser.add_argument(
        "--title", 
        help="Title for the graph visualization"
    )
    visualize_parser.add_argument(
        "--max-nodes", 
        type=int, 
        default=100,
        help="Maximum number of nodes to include in the page-level graph (default: 100)"
    )
    visualize_parser.add_argument(
        "--node-size", 
        type=int, 
        default=100,
        help="Node size factor for domain-level graph (default: 100)"
    )
    visualize_parser.add_argument(
        "--no-labels", 
        action="store_true",
        help="Don't show labels on graph nodes"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle case where no command is specified
    if not args.command:
        # For backward compatibility, default to extract command if a URL is provided directly
        if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
            # Check if the first argument appears to be a URL
            potential_url = sys.argv[1]
            if potential_url.startswith(('http://', 'https://')):
                # Invoke the extract command with the arguments
                args = parser.parse_args(['extract'] + sys.argv[1:])
            else:
                parser.print_help()
                return 1
        else:
            parser.print_help()
            return 1
    
    # Dispatch to the appropriate command
    if args.command == "extract":
        sys.exit(run_product_extraction(args))
    elif args.command == "crawl":
        sys.exit(run_crawler(args))
    elif args.command == "visualize":
        sys.exit(run_visualize(args))
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 