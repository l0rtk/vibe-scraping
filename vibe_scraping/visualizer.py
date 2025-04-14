"""
Visualization utilities for the web crawler.

This module provides functions to create visual representations of web crawling operations,
including network graphs of crawled pages and their relationships.
"""

import os
import json
import networkx as nx
import matplotlib.pyplot as plt
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_crawl_graph(crawl_data_path, output_file=None, max_nodes=100, title=None, 
                        node_size=300, width=12, height=8, with_labels=True, 
                        use_domain_colors=True, edge_color='gray'):
    """
    Generate a network graph visualization of a web crawl.
    
    Args:
        crawl_data_path: Path to the crawl data directory
        output_file: Path to save the graph image (default: crawl_graph.png in crawl_data_path)
        max_nodes: Maximum number of nodes to include in the graph (default: 100)
        title: Title for the graph (default: "Web Crawl Graph")
        node_size: Size of the nodes (default: 300)
        width: Width of the figure in inches (default: 12)
        height: Height of the figure in inches (default: 8)
        with_labels: Whether to show labels on nodes (default: True)
        use_domain_colors: Whether to color nodes by domain (default: True)
        edge_color: Color for the edges (default: 'gray')
        
    Returns:
        Path to the generated graph image
    """
    # Check if the crawl data directory exists
    if not os.path.exists(crawl_data_path):
        logger.error(f"Crawl data directory not found: {crawl_data_path}")
        return None
    
    # Load the metadata file
    metadata_file = os.path.join(crawl_data_path, "metadata.json")
    if not os.path.exists(metadata_file):
        logger.error(f"Metadata file not found: {metadata_file}")
        return None
    
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    except Exception as e:
        logger.error(f"Error loading metadata: {str(e)}")
        return None
    
    # Get the links data
    links_data = {}
    crawled_urls = metadata.get("crawled_urls", {})
    
    # Check if we have any crawled URLs
    if not crawled_urls:
        logger.error("No crawled URLs found in metadata")
        return None
    
    # Ensure output file path
    if not output_file:
        output_file = os.path.join(crawl_data_path, "crawl_graph.png")
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add nodes and edges from the metadata
    for url, data in crawled_urls.items():
        G.add_node(url)
        # Add edges from this URL to all the links it contains
        if "links" in data:
            for link in data["links"]:
                if link in crawled_urls:  # Only add edges to URLs that were also crawled
                    G.add_edge(url, link)
    
    # If the graph is too large, take a subset
    if len(G) > max_nodes:
        logger.info(f"Graph has {len(G)} nodes, limiting to {max_nodes}")
        # Get the largest connected component
        largest_cc = max(nx.weakly_connected_components(G), key=len)
        if len(largest_cc) > max_nodes:
            # Take the first max_nodes nodes from the largest component
            nodes_to_keep = list(largest_cc)[:max_nodes]
        else:
            # Take all nodes from the largest component and some additional nodes
            nodes_to_keep = list(largest_cc)
            remaining_nodes = list(set(G.nodes()) - set(nodes_to_keep))
            nodes_to_keep.extend(remaining_nodes[:max_nodes - len(nodes_to_keep)])
        
        G = G.subgraph(nodes_to_keep).copy()
    
    # Create node colors based on domain
    if use_domain_colors:
        domains = {}
        colors = plt.cm.tab20(range(20))  # Use a colormap with 20 distinct colors
        domain_to_color = {}
        
        for url in G.nodes():
            domain = urlparse(url).netloc
            if domain not in domain_to_color:
                color_index = len(domain_to_color) % 20
                domain_to_color[domain] = colors[color_index]
            
            domains[url] = domain
        
        node_colors = [domain_to_color[domains[url]] for url in G.nodes()]
    else:
        node_colors = "skyblue"
    
    # Create the figure
    plt.figure(figsize=(width, height))
    
    # Set the title
    if title:
        plt.title(title)
    else:
        start_url = metadata.get("start_url", "Unknown")
        plt.title(f"Web Crawl Graph - Starting URL: {start_url}")
    
    # Draw the graph
    pos = nx.spring_layout(G, seed=42)  # For reproducibility
    
    # Draw the nodes
    nx.draw_networkx_nodes(G, pos, node_size=node_size, node_color=node_colors, alpha=0.8)
    
    # Draw the edges
    nx.draw_networkx_edges(G, pos, alpha=0.5, arrows=True, edge_color=edge_color)
    
    # Draw the labels if requested
    if with_labels:
        # Create shorter labels for better readability
        labels = {}
        for url in G.nodes():
            parsed = urlparse(url)
            path = parsed.path[:20] + "..." if len(parsed.path) > 20 else parsed.path
            labels[url] = f"{parsed.netloc}{path}"
        
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=8)
    
    # Save the figure
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Graph saved to {output_file}")
    return output_file

def generate_domain_graph(crawl_data_path, output_file=None, title=None, 
                         node_size_factor=100, width=10, height=8, with_labels=True):
    """
    Generate a domain-level graph visualization of a web crawl.
    
    Args:
        crawl_data_path: Path to the crawl data directory
        output_file: Path to save the graph image (default: domain_graph.png in crawl_data_path)
        title: Title for the graph (default: "Domain-Level Web Crawl Graph")
        node_size_factor: Factor to multiply node sizes by based on page count (default: 100)
        width: Width of the figure in inches (default: 10)
        height: Height of the figure in inches (default: 8)
        with_labels: Whether to show labels on nodes (default: True)
        
    Returns:
        Path to the generated graph image
    """
    # Check if the crawl data directory exists
    if not os.path.exists(crawl_data_path):
        logger.error(f"Crawl data directory not found: {crawl_data_path}")
        return None
    
    # Load the metadata file
    metadata_file = os.path.join(crawl_data_path, "metadata.json")
    if not os.path.exists(metadata_file):
        logger.error(f"Metadata file not found: {metadata_file}")
        return None
    
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    except Exception as e:
        logger.error(f"Error loading metadata: {str(e)}")
        return None
    
    # Get the crawled URLs
    crawled_urls = metadata.get("crawled_urls", {})
    
    # Check if we have any crawled URLs
    if not crawled_urls:
        logger.error("No crawled URLs found in metadata")
        return None
    
    # Ensure output file path
    if not output_file:
        output_file = os.path.join(crawl_data_path, "domain_graph.png")
    
    # Create a directed graph for domains
    G = nx.DiGraph()
    
    # Track domains and their connections
    domain_counts = {}
    domain_connections = {}
    
    # Process URLs and build domain-level graph
    for url, data in crawled_urls.items():
        source_domain = urlparse(url).netloc
        
        # Count domains
        if source_domain not in domain_counts:
            domain_counts[source_domain] = 0
        domain_counts[source_domain] += 1
        
        # Track domain connections
        if source_domain not in domain_connections:
            domain_connections[source_domain] = {}
        
        # Add edges from this domain to target domains
        if "links" in data:
            for link in data["links"]:
                if link in crawled_urls:  # Only count links that were crawled
                    target_domain = urlparse(link).netloc
                    if target_domain not in domain_connections[source_domain]:
                        domain_connections[source_domain][target_domain] = 0
                    domain_connections[source_domain][target_domain] += 1
    
    # Add nodes and edges to the graph
    for domain, count in domain_counts.items():
        G.add_node(domain, weight=count)
    
    for source_domain, targets in domain_connections.items():
        for target_domain, weight in targets.items():
            if G.has_node(target_domain):  # Only add edges between domains in the graph
                G.add_edge(source_domain, target_domain, weight=weight)
    
    # Get node sizes based on page count
    node_sizes = [domain_counts[domain] * node_size_factor for domain in G.nodes()]
    
    # Create the figure
    plt.figure(figsize=(width, height))
    
    # Set the title
    if title:
        plt.title(title)
    else:
        plt.title("Domain-Level Web Crawl Graph")
    
    # Draw the graph
    pos = nx.spring_layout(G, seed=42)  # For reproducibility
    
    # Draw the nodes with sizes based on page count
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color="skyblue", alpha=0.8)
    
    # Draw the edges with width based on connection count
    for (u, v, d) in G.edges(data=True):
        width = 0.5 + (d['weight'] / 5.0)  # Adjust width based on connection count
        nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], width=width, alpha=0.7)
    
    # Draw the labels if requested
    if with_labels:
        nx.draw_networkx_labels(G, pos, font_size=10)
    
    # Save the figure
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Domain graph saved to {output_file}")
    return output_file

def create_dynamic_graph(crawl_data_path, output_file=None):
    """
    Create an interactive HTML visualization of the crawl graph using Pyvis.
    
    Args:
        crawl_data_path: Path to the crawl data directory
        output_file: Path to save the HTML file (default: interactive_graph.html in crawl_data_path)
        
    Returns:
        Path to the generated HTML file
    """
    try:
        # Try to import pyvis, which is optional
        from pyvis.network import Network
    except ImportError:
        logger.error("Pyvis is not installed. Run 'pip install pyvis' to use this feature.")
        return None
    
    # Check if the crawl data directory exists
    if not os.path.exists(crawl_data_path):
        logger.error(f"Crawl data directory not found: {crawl_data_path}")
        return None
    
    # Load the metadata file
    metadata_file = os.path.join(crawl_data_path, "metadata.json")
    if not os.path.exists(metadata_file):
        logger.error(f"Metadata file not found: {metadata_file}")
        return None
    
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    except Exception as e:
        logger.error(f"Error loading metadata: {str(e)}")
        return None
    
    # Get the crawled URLs
    crawled_urls = metadata.get("crawled_urls", {})
    
    # Check if we have any crawled URLs
    if not crawled_urls:
        logger.error("No crawled URLs found in metadata")
        return None
    
    # Ensure output file path
    if not output_file:
        output_file = os.path.join(crawl_data_path, "interactive_graph.html")
    
    # Create a network
    net = Network(height="750px", width="100%", directed=True, notebook=False)
    
    # Add nodes
    for url, data in crawled_urls.items():
        parsed = urlparse(url)
        domain = parsed.netloc
        title = f"{url}\nDepth: {data.get('depth', 'unknown')}"
        
        # Add the node with domain-based color and hover information
        net.add_node(url, title=title, label=domain)
    
    # Add edges
    for url, data in crawled_urls.items():
        if "links" in data:
            for link in data["links"]:
                if link in crawled_urls:  # Only add edges to URLs that were crawled
                    net.add_edge(url, link)
    
    # Set physics layout options
    net.barnes_hut(spring_length=200)
    
    # Save the visualization
    net.save_graph(output_file)
    
    logger.info(f"Interactive graph saved to {output_file}")
    return output_file 