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
    
    # Get the start URL from metadata
    start_url = metadata.get("start_url")
    if not start_url and "crawl_stats" in metadata and "start_url" in metadata["crawl_stats"]:
        start_url = metadata["crawl_stats"]["start_url"]
    
    # Add the start URL as the root node if it exists
    if start_url:
        G.add_node(start_url)
    
    # Add nodes and edges from the metadata
    for url, data in crawled_urls.items():
        G.add_node(url)
        # Add edges from this URL to all the links it contains
        if "links" in data:
            for link in data["links"]:
                if link in crawled_urls:  # Only add edges to URLs that were also crawled
                    G.add_edge(url, link)
    
    # If start_url is not directly connected to any node and other nodes exist,
    # connect it to nodes with depth 1 or the lowest depth
    if start_url and G.number_of_nodes() > 1:
        # If start_url has no outgoing edges, connect it to first-level nodes
        if G.out_degree(start_url) == 0:
            # Find nodes at depth 1 or lowest available depth
            depth_nodes = {}
            for url, data in crawled_urls.items():
                if url != start_url:
                    depth = data.get("depth", float('inf'))
                    if depth not in depth_nodes:
                        depth_nodes[depth] = []
                    depth_nodes[depth].append(url)
            
            # Get the min depth available
            if depth_nodes:
                min_depth = min(depth_nodes.keys())
                
                # Connect start_url to nodes at min_depth
                for node in depth_nodes[min_depth]:
                    if not G.has_edge(start_url, node):
                        G.add_edge(start_url, node)
    
    # If the graph is too large, take a subset
    if len(G) > max_nodes:
        logger.info(f"Graph has {len(G)} nodes, limiting to {max_nodes}")
        # Ensure start_url is kept if it exists
        nodes_to_keep = [start_url] if start_url and start_url in G.nodes() else []
        
        # Get the largest connected component
        largest_cc = max(nx.weakly_connected_components(G), key=len)
        
        # If start_url is in this component, prioritize nodes from it
        if start_url in largest_cc:
            # Get nodes from largest component, prioritizing those connected to start_url
            remainder = list(largest_cc - {start_url})
            nodes_to_keep.extend(remainder[:max_nodes - len(nodes_to_keep)])
        else:
            # Take all nodes from the largest component and some additional nodes
            remaining_nodes = list(largest_cc)
            nodes_to_keep.extend(remaining_nodes[:max_nodes - len(nodes_to_keep)])
            
            # If we still have room and start_url wasn't in the component, add it back
            if len(nodes_to_keep) < max_nodes and start_url not in nodes_to_keep and start_url in G.nodes():
                nodes_to_keep.append(start_url)
        
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
        root_url = start_url or next(iter(crawled_urls.keys()), "Unknown")
        plt.title(f"Web Crawl Graph - {root_url}")
    
    # Draw the graph
    pos = nx.spring_layout(G, seed=42)  # For reproducibility
    
    # Highlight the start URL if it exists in the graph
    if start_url and start_url in G.nodes():
        nx.draw_networkx_nodes(G, pos, nodelist=[start_url], node_size=node_size*1.5, 
                               node_color='red', alpha=0.8)
        remaining_nodes = [node for node in G.nodes() if node != start_url]
        if remaining_nodes:
            if isinstance(node_colors, list):
                remaining_colors = [c for i, c in enumerate(node_colors) 
                                   if list(G.nodes())[i] != start_url]
                nx.draw_networkx_nodes(G, pos, nodelist=remaining_nodes, 
                                      node_size=node_size, node_color=remaining_colors, alpha=0.8)
            else:
                nx.draw_networkx_nodes(G, pos, nodelist=remaining_nodes, 
                                      node_size=node_size, node_color=node_colors, alpha=0.8)
    else:
        # Draw all nodes with the same style if no start_url
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
            if url == start_url:
                # Make the start URL label more noticeable
                labels[url] = f"{parsed.netloc}{path} (START)"
            else:
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
    
    # Get the start URL from metadata
    start_url = metadata.get("start_url")
    if not start_url and "crawl_stats" in metadata and "start_url" in metadata["crawl_stats"]:
        start_url = metadata["crawl_stats"]["start_url"]
    
    # Create a network with appropriate settings for a directed graph
    net = Network(
        height="750px", 
        width="100%", 
        directed=True, 
        notebook=False, 
        cdn_resources="remote",
        heading=f"Web Crawl Graph - {start_url}"
    )
    
    # Add custom options for better visualization
    net.set_options("""
    {
      "nodes": {
        "font": {
          "size": 12,
          "face": "Arial"
        },
        "shape": "dot",
        "borderWidth": 1,
        "borderWidthSelected": 3,
        "scaling": {
          "min": 10,
          "max": 30
        }
      },
      "edges": {
        "color": {
          "color": "#1976D2",
          "highlight": "#03A9F4"
        },
        "smooth": {
          "type": "continuous",
          "forceDirection": "none"
        },
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.5
          }
        }
      },
      "physics": {
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "minVelocity": 0.75,
        "solver": "hierarchicalRepulsion",
        "hierarchicalRepulsion": {
          "centralGravity": 0.1,
          "springLength": 100,
          "springConstant": 0.05,
          "nodeDistance": 120
        }
      },
      "interaction": {
        "navigationButtons": true,
        "hover": true
      }
    }
    """)
    
    # URL depth tracking
    url_depths = {}
    
    # Process crawled URLs to get depth information
    for url, data in crawled_urls.items():
        url_depths[url] = data.get('depth', float('inf'))
    
    # Add nodes to the network
    for url, data in crawled_urls.items():
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path[:25] + "..." if len(parsed.path) > 25 else parsed.path
        depth = data.get('depth', 'unknown')
        
        label = f"{domain}{path}"
        title = f"{url}<br>Depth: {depth}"
        
        # Special formatting for the start URL
        if url == start_url:
            net.add_node(
                url, 
                title=title, 
                label="START: " + label, 
                color="#E53935",  # Red
                size=30,
                borderWidth=3,
                font={"size": 14, "bold": True}
            )
        else:
            # Color nodes based on depth if available
            if isinstance(depth, (int, float)) and depth != float('inf'):
                # Gradient from blue (depth 1) to green (deeper)
                colors = ["#2196F3", "#03A9F4", "#00BCD4", "#009688", "#4CAF50", "#8BC34A"]
                color = colors[min(depth, len(colors)-1)]
                net.add_node(
                    url, 
                    title=title, 
                    label=label, 
                    color=color,
                    size=25 - (depth * 2) if isinstance(depth, (int, float)) else 20  # Size decreases with depth
                )
            else:
                net.add_node(url, title=title, label=label)
    
    # First, add all explicit edges from the metadata
    for url, data in crawled_urls.items():
        if "links" in data:
            for link in data["links"]:
                if link in crawled_urls:  # Only add edges to URLs that were crawled
                    net.add_edge(url, link, title=f"From: {url}<br>To: {link}")
    
    # Now make sure all nodes are connected to the graph
    all_nodes = set(crawled_urls.keys())
    
    # Check if start_url is in crawled_urls
    start_url_in_data = start_url and start_url in crawled_urls
    
    # Find nodes that don't have any incoming edges
    orphan_nodes = set()
    connected_nodes = set()
    
    # Check the connections in the network
    for edge in net.get_edges():
        connected_nodes.add(edge['to'])
    
    # Find nodes without incoming connections (except start_url)
    for node in all_nodes:
        if node != start_url and node not in connected_nodes:
            orphan_nodes.add(node)
    
    # Connect orphan nodes to the start_url or to their most likely parent
    if start_url_in_data:
        for node in orphan_nodes:
            # Try to find the most logical parent based on depth
            node_depth = url_depths.get(node, float('inf'))
            
            if node_depth == 1:  # Depth 1 nodes should connect directly to start_url
                net.add_edge(
                    start_url, 
                    node, 
                    title=f"Inferred connection from start URL",
                    dashes=True,  # Use dashed line for inferred connections
                    color={"color": "#9E9E9E", "opacity": 0.6}  # Lighter gray color
                )
            else:
                # Try to find a parent node with depth one less than this node
                potential_parents = [
                    url for url, depth in url_depths.items() 
                    if depth == node_depth - 1 and url != node
                ]
                
                if potential_parents:
                    # Choose the first potential parent
                    parent = potential_parents[0]
                    net.add_edge(
                        parent, 
                        node, 
                        title=f"Inferred connection based on depth",
                        dashes=True,
                        color={"color": "#9E9E9E", "opacity": 0.6}
                    )
                else:
                    # If no logical parent found, connect to start_url if it exists in the data
                    net.add_edge(
                        start_url, 
                        node, 
                        title=f"Inferred connection from start URL",
                        dashes=True,
                        color={"color": "#9E9E9E", "opacity": 0.6}
                    )
    elif orphan_nodes and all_nodes:
        # If start_url is not in the data but we have orphan nodes,
        # connect them to the first node in url_depths with the lowest depth
        if url_depths:
            min_depth = min(url_depths.values())
            potential_roots = [url for url, depth in url_depths.items() if depth == min_depth]
            
            if potential_roots:
                root_node = potential_roots[0]
                for node in orphan_nodes:
                    if node != root_node:
                        net.add_edge(
                            root_node, 
                            node, 
                            title=f"Inferred connection from root node",
                            dashes=True,
                            color={"color": "#9E9E9E", "opacity": 0.6}
                        )
    
    # Save the visualization
    net.save_graph(output_file)
    
    logger.info(f"Interactive graph saved to {output_file}")
    return output_file 