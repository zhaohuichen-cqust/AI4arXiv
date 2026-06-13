#!/usr/bin/env python3
"""
Fetch latest papers from arXiv related to machine learning for traffic flow prediction
and send via email.
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_arxiv_papers(search_query, max_results=50):
    """
    Fetch papers from arXiv API
    
    Args:
        search_query: Search query string
        max_results: Maximum number of results
    
    Returns:
        List of paper dictionaries
    """
    base_url = 'http://export.arxiv.org/api/query?'
    
    # Construct search query
    search_terms = {
        'search_query': search_query,
        'start': 0,
        'max_results': max_results,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    
    url = base_url + urllib.parse.urlencode(search_terms)
    
    logger.info(f"Fetching papers from arXiv with URL: {url}")
    
    try:
        with urllib.request.urlopen(url) as response:
            xml_data = response.read().decode('utf-8')
        
        # Parse XML response
        root = ET.fromstring(xml_data)
        
        # Define namespace
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        papers = []
        for entry in root.findall('atom:entry', ns):
            paper = {}
            
            # Extract information
            paper['title'] = entry.find('atom:title', ns).text.strip()
            paper['authors'] = [author.find('atom:name', ns).text 
                              for author in entry.findall('atom:author', ns)]
            paper['summary'] = entry.find('atom:summary', ns).text.strip()
            paper['published'] = entry.find('atom:published', ns).text
            paper['arxiv_id'] = entry.find('atom:id', ns).text.split('/abs/')[-1]
            paper['pdf_url'] = f"https://arxiv.org/pdf/{paper['arxiv_id']}.pdf"
            paper['abs_url'] = f"https://arxiv.org/abs/{paper['arxiv_id']}"
            
            papers.append(paper)
        
        logger.info(f"Successfully fetched {len(papers)} papers")
        return papers
    
    except Exception as e:
        logger.error(f"Error fetching papers from arXiv: {e}")
        return []

def send_email(papers, recipient_email):
    """
    Send email with paper information
    
    Args:
        papers: List of paper dictionaries
        recipient_email: Recipient email address
    """
    sender_email = os.environ.get('EMAIL_SENDER')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    
    if not sender_email or not sender_password:
        logger.warning("Email credentials not provided. Skipping email sending.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Weekly arXiv Papers: Machine Learning for Traffic Flow Prediction"
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # Create email body
        plain_text = create_plain_text_body(papers)
        html_text = create_html_body(papers)
        
        msg.attach(MIMEText(plain_text, 'plain'))
        msg.attach(MIMEText(html_text, 'html'))
        
        # Send email
        logger.info(f"Connecting to SMTP server: {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {recipient_email}")
        return True
    
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

def create_plain_text_body(papers):
    """Create plain text email body"""
    body = "Weekly arXiv Papers: Machine Learning for Traffic Flow Prediction\n"
    body += "=" * 70 + "\n\n"
    body += f"Found {len(papers)} papers published in the last 7 days\n"
    body += f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    body += "=" * 70 + "\n\n"
    
    for i, paper in enumerate(papers, 1):
        body += f"[{i}] {paper['title']}\n"
        body += f"Authors: {', '.join(paper['authors'][:3])}"
        if len(paper['authors']) > 3:
            body += f" and {len(paper['authors']) - 3} more"
        body += "\n"
        body += f"Published: {paper['published'][:10]}\n"
        body += f"Abstract: {paper['summary'][:300]}...\n"
        body += f"Link: {paper['abs_url']}\n"
        body += f"PDF: {paper['pdf_url']}\n"
        body += "-" * 70 + "\n\n"
    
    return body

def create_html_body(papers):
    """Create HTML email body"""
    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
            .paper { margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; background-color: #ecf0f1; }
            .title { font-weight: bold; font-size: 16px; margin: 10px 0; }
            .authors { color: #555; margin: 5px 0; }
            .abstract { margin: 10px 0; line-height: 1.6; }
            .links { margin: 10px 0; }
            .links a { display: inline-block; margin-right: 15px; color: #3498db; text-decoration: none; }
            .links a:hover { text-decoration: underline; }
            .meta { color: #777; font-size: 12px; margin: 5px 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Weekly arXiv Papers</h1>
            <p>Machine Learning for Traffic Flow Prediction</p>
            <p>Updated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC') + """</p>
        </div>
    """
    
    for i, paper in enumerate(papers, 1):
        html += f"""
        <div class="paper">
            <div class="title">[{i}] {paper['title']}</div>
            <div class="authors">
                <strong>Authors:</strong> {', '.join(paper['authors'][:3])}
        """
        if len(paper['authors']) > 3:
            html += f" and {len(paper['authors']) - 3} more"
        
        html += f"""
            </div>
            <div class="meta">Published: {paper['published'][:10]}</div>
            <div class="abstract">
                <strong>Abstract:</strong><br>
                {paper['summary'][:500]}...
            </div>
            <div class="links">
                <a href="{paper['abs_url']}">View on arXiv</a>
                <a href="{paper['pdf_url']}">Download PDF</a>
            </div>
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    return html

def main():
    """Main function"""
    # arXiv search query for machine learning in traffic flow prediction
    # Using 'all' field to search across title, abstract, authors
    search_query = '(cat:cs.AI OR cat:cs.LG OR cat:stat.ML) AND (traffic OR "traffic flow" OR "traffic prediction")'
    
    # Fetch papers
    papers = fetch_arxiv_papers(search_query, max_results=50)
    
    if papers:
        logger.info(f"Found {len(papers)} papers")
        
        # Send email
        recipient_email = os.environ.get('RECIPIENT_EMAIL', 'chen-zhh@qq.com')
        send_email(papers, recipient_email)
    else:
        logger.warning("No papers found")

if __name__ == '__main__':
    main()
