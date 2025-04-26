#!/usr/bin/env python3
"""
Simple pipeline for crawling a website and processing the HTML content.
And analyzing content with Groq to identify article pages.
"""

from vibe_scraping.crawler import WebCrawler
from vibe_scraping.html_processor import process_html_content
from bs4 import BeautifulSoup
import json
import os
import groq
from dotenv import load_dotenv

load_dotenv()

def clean_html(html_content, keep_only_body=False):
    """
    Clean HTML by removing all attributes and classes while keeping the structure.
    Also removes script and style tags to keep only structure and text.
    Returns a clean HTML string with only the structural elements and text.
    
    Args:
        html_content (str): The HTML content to clean
        keep_only_body (bool): If True, returns only the body content
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style tags
    for script_or_style in soup.find_all(['script', 'style']):
        script_or_style.decompose()
    
    # Find all tags
    for tag in soup.find_all(True):
        # Remove all attributes from each tag
        tag.attrs = {}
    
    # Extract only body content if requested
    if keep_only_body and soup.body:
        soup = soup.body
    
    # Return the cleaned HTML as a string
    return str(soup)

def analyze_with_groq(content, url):
    """
    Analyze the content using Groq API to determine if it's an article page
    
    Args:
        content (str): The cleaned HTML content
        url (str): The URL of the page
        
    Returns:
        dict: Analysis results including if it's an article page
    """
    # Initialize Groq client
    client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    # Trim content if too long
    max_content_length = 15000  # Limit content length to avoid token limits
    trimmed_content = content[:max_content_length] if len(content) > max_content_length else content
    
    # Create prompt for analysis
    prompt = f"""
    Analyze the following HTML content from the URL: {url}
    
    HTML Content:
    {trimmed_content}
    
    Determine if this is a dedicated article page (not a list of articles, homepage, or other non-article page). 
    An article page typically has:
    - A clear main title/headline
    - A body of text content (paragraphs)
    - Usually a publication date
    - Often has author information
    - Focused on a single topic
    
    Provide your analysis in JSON format with the following fields:
    - is_article_page: true/false
    - confidence: number between 0-1
    - reasoning: brief explanation
    - detected_title: the article title if found
    - detected_publish_date: the publication date if found
    - detected_author: the author if found
    """
    
    # Call Groq API
    try:
        chat_completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": "You are an AI specialized in analyzing web content structure. Respond only with the requested JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_completion_tokens=1000,
            top_p=1,
            stream=False,
            stop=None
        )
        
        # Extract and parse JSON response
        response_text = chat_completion.choices[0].message.content
        try:
            # Try to extract JSON if it's wrapped in backticks or has extra text
            if "```json" in response_text:
                json_content = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_content = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_content = response_text.strip()
                
            analysis = json.loads(json_content)
            return analysis
        except json.JSONDecodeError:
            return {
                "is_article_page": False,
                "confidence": 0,
                "reasoning": "Error parsing Groq API response",
                "error": "Invalid JSON response"
            }
            
    except Exception as e:
        return {
            "is_article_page": False,
            "confidence": 0,
            "reasoning": f"Error calling Groq API: {str(e)}",
            "error": str(e)
        }

def extract_article_content(html_content, analysis):
    """
    Extract the main article content including headline, paragraphs, and other relevant elements
    
    Args:
        html_content (str): The HTML content
        analysis (dict): The analysis result from Groq
        
    Returns:
        dict: Dictionary containing extracted article content
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract title from analysis or try to find it in the HTML
    title = analysis.get('detected_title', '')
    if not title and soup.title:
        title = soup.title.text.strip()
    
    # Try to find the main article content
    article_content = ""
    main_element = None
    
    # Common article container elements
    article_candidates = soup.find_all(['article', 'main', 'div', 'section'])
    
    # Score elements based on content density and structure
    candidate_scores = []
    for element in article_candidates:
        # Skip tiny elements
        if len(element.get_text(strip=True)) < 100:
            continue
            
        # Get all paragraphs within this element
        paragraphs = element.find_all('p')
        paragraph_text_length = sum(len(p.get_text(strip=True)) for p in paragraphs)
        
        # Calculate text density
        total_text = element.get_text(strip=True)
        total_length = len(total_text)
        
        # Skip elements that are too short
        if total_length < 200:
            continue
            
        # Calculate scores based on:
        # 1. Total text length (longer is better for articles)
        # 2. Paragraph density (articles usually have proper paragraphs)
        # 3. Presence of common article elements
        length_score = min(total_length / 1000, 5)  # Cap at 5
        paragraph_density = paragraph_text_length / max(total_length, 1)
        
        # Look for article indicators
        has_headline = bool(element.find(['h1', 'h2', 'h3']))
        has_date = bool(element.find(string=lambda text: 
            text and any(date_word in text.lower() for date_word in ['date', 'published', 'posted'])))
        has_author = bool(element.find(string=lambda text: 
            text and any(author_word in text.lower() for author_word in ['author', 'by', 'written'])))
        
        # Calculate final score
        indicators_score = sum([has_headline * 2, has_date, has_author])
        final_score = length_score + (paragraph_density * 3) + indicators_score
        
        candidate_scores.append((element, final_score))
    
    # Sort candidates by score (highest first)
    candidate_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Extract content from the best candidate if available
    if candidate_scores:
        main_element = candidate_scores[0][0]
        
        # Extract paragraphs from the main element
        paragraphs = main_element.find_all('p')
        article_content = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        # If no paragraphs were found, just use the text content
        if not article_content:
            article_content = main_element.get_text(strip=True)
    
    # If we still don't have content, use the first few paragraphs from the page
    if not article_content:
        paragraphs = soup.find_all('p')
        if paragraphs:
            article_content = "\n\n".join([p.get_text(strip=True) for p in paragraphs[:10] if p.get_text(strip=True)])
    
    # Extract potential publish date
    publish_date = analysis.get('detected_publish_date', '')
    if not publish_date:
        date_elements = soup.find_all(string=lambda text: 
            text and any(date_word in text.lower() for date_word in ['date', 'published', 'posted']))
        if date_elements:
            publish_date = date_elements[0].strip()
    
    # Extract potential author
    author = analysis.get('detected_author', '')
    if not author:
        author_elements = soup.find_all(string=lambda text: 
            text and any(author_word in text.lower() for author_word in ['author', 'by', 'written']))
        if author_elements:
            author = author_elements[0].strip()
    
    return {
        "title": title,
        "content": article_content,
        "publish_date": publish_date,
        "author": author
    }

def extract_and_analyze_articles(url, html_content, soup, metadata):
    """Extract and analyze content to identify article pages"""
    clean_content = clean_html(html_content, keep_only_body=True)
    
    # Analyze with Groq
    analysis = analyze_with_groq(clean_content, url)
    
    # Extract article content if it looks like an article
    is_article = analysis.get("is_article_page", False)
    article_content = {}
    
    if is_article:
        article_content = extract_article_content(clean_content, analysis)
    
    # Return combined results
    return {
        "url": url,
        "analysis": analysis,
        "is_article_page": is_article,
        "title": article_content.get("title", analysis.get("detected_title", soup.title.text if soup.title else "No title")),
        "publish_date": article_content.get("publish_date", analysis.get("detected_publish_date")),
        "author": article_content.get("author", analysis.get("detected_author")),
        "article_content": article_content.get("content", "") if is_article else ""
    }

# Step 1: Set up and run crawler
# Uncomment below to run crawler
# crawler = WebCrawler(
#     start_url="https://newshub.ge",
#     max_depth=2,
#     max_pages=20,
#     respect_robots_txt=False,
#     save_path="./crawl_data"
# )
# result = crawler.crawl()
# print(f"Crawled {result.get('pages_crawled', 0)} pages to ./crawl_data")

# Step 2: Process the content with custom processor
stats = process_html_content(
    crawl_data_path="./crawl_data",
    output_path="./crawl_data/article_analysis.json",
    processor_func=extract_and_analyze_articles
)

# Step 3: Display results and filter only article pages
if stats and 'total_pages_processed' in stats:
    print(f"Processed {stats['total_pages_processed']} pages")
    
    # Load the processed data
    with open("./crawl_data/article_analysis.json", "r") as f:
        all_results = json.load(f)
    
    # Filter only article pages - handle both dictionary and list formats
    articles = []
    for page in all_results:
        # Check if the page is a dictionary
        if isinstance(page, dict):
            # Get is_article_page from the page itself or from the analysis field
            is_article = page.get("is_article_page", False)
            if not is_article and "analysis" in page and isinstance(page["analysis"], dict):
                is_article = page["analysis"].get("is_article_page", False)
            
            if is_article:
                articles.append(page)
    
    # Save filtered articles
    with open("./crawl_data/filtered_articles.json", "w") as f:
        json.dump(articles, f, indent=2)
    
    # Print statistics about extracted content
    articles_with_content = sum(1 for article in articles if article.get("article_content"))
    avg_content_length = sum(len(article.get("article_content", "")) for article in articles) / max(articles_with_content, 1)
    
    print(f"Found {len(articles)} article pages out of {len(all_results)} total pages")
    print(f"Successfully extracted content from {articles_with_content} articles")
    print(f"Average article content length: {int(avg_content_length)} characters")
    print(f"Article pages saved to: ./crawl_data/filtered_articles.json")
    
    # Create a simplified version with just the important data
    simplified_articles = []
    for article in articles:
        simplified_articles.append({
            "url": article.get("url", ""),
            "title": article.get("title", ""),
            "publish_date": article.get("publish_date", ""),
            "author": article.get("author", ""),
            "content": article.get("article_content", "")
        })
    
    # Save simplified articles
    with open("./crawl_data/articles_content.json", "w") as f:
        json.dump(simplified_articles, f, indent=2)
    
    print(f"Simplified article content saved to: ./crawl_data/articles_content.json")
else:
    print("No pages were processed")
