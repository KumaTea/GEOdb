"""
Utility functions for parsing GEO HTML pages.
"""
import re
import logging
from datetime import datetime
from typing import Optional, Tuple
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString


def parse_geo_date(date_str: str) -> Optional[datetime]:
    """
    Parse a GEO date string to datetime object.
    
    Handles formats like:
    - "Public on Jul 21, 2006"
    - "Jul 21, 2006"
    - "Mar 22, 2022"
    
    Args:
        date_str: Date string from GEO HTML
        
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None
    
    # Remove "Public on " prefix if present
    date_str = re.sub(r'^Public on\s+', '', date_str.strip())
    
    # Try various date formats
    formats = [
        '%b %d, %Y',  # Jul 21, 2006
        '%B %d, %Y',  # July 21, 2006
        '%d %b %Y',   # 21 Jul 2006
        '%d %B %Y',   # 21 July 2006
        '%Y-%m-%d',   # 2006-07-21
        '%Y/%m/%d',   # 2006/07/21
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logging.warning(f'Could not parse date: {date_str}')
    return None


def get_table_row_text(soup: BeautifulSoup, field_name: str) -> Optional[str]:
    """
    Extract text from a table row by field name.
    
    Looks for a <tr> where the first <td> contains the field name,
    and returns the text from the second <td>.
    
    Args:
        soup: BeautifulSoup object
        field_name: Name of the field to extract
        
    Returns:
        Text content or None if not found
    """
    rows = soup.find_all('tr', valign='top')
    for row in rows:
        tds = row.find_all('td')
        if len(tds) >= 2:
            first_td_text = tds[0].get_text(strip=True)
            # Check if field name matches (allowing partial matches)
            if field_name.lower() in first_td_text.lower():
                # Get text from second td, handling links
                second_td = tds[1]
                # Extract text, handling <br> tags as newlines
                text_parts = []
                for element in second_td.contents:
                    if isinstance(element, NavigableString):
                        text_parts.append(str(element).strip())
                    elif element.name == 'br':
                        text_parts.append('\n')
                    elif element.name == 'a':
                        text_parts.append(element.get_text(strip=True))
                    elif hasattr(element, 'get_text'):
                        text_parts.append(element.get_text(separator=' ', strip=True))
                
                result = ' '.join(text_parts).strip()
                # Clean up multiple spaces and newlines
                result = re.sub(r'\s+', ' ', result)
                return result if result else None
    
    return None


def get_table_row_text_bgcolor(soup: BeautifulSoup, field_name: str) -> Optional[str]:
    """
    Extract text from a table row with bgcolor="#eeeeee" by field name.
    
    This is used for fields like Submission date, Contact name, etc.
    
    Args:
        soup: BeautifulSoup object
        field_name: Name of the field to extract
        
    Returns:
        Text content or None if not found
    """
    rows = soup.find_all('tr', bgcolor='#eeeeee')
    for row in rows:
        tds = row.find_all('td')
        if len(tds) >= 2:
            first_td_text = tds[0].get_text(strip=True)
            if field_name.lower() in first_td_text.lower():
                second_td = tds[1]
                text = second_td.get_text(separator=' ', strip=True)
                # Handle email links
                email_link = second_td.find('a', href=lambda x: x and x.startswith('mailto:'))
                if email_link:
                    text = email_link.get_text(strip=True)
                return text if text else None
    
    return None


def extract_links_from_row(soup: BeautifulSoup, field_name: str) -> list[str]:
    """
    Extract all links from a table row by field name.
    
    Args:
        soup: BeautifulSoup object
        field_name: Name of the field to extract
        
    Returns:
        List of link texts
    """
    rows = soup.find_all('tr', valign='top')
    for row in rows:
        tds = row.find_all('td')
        if len(tds) >= 2:
            first_td_text = tds[0].get_text(strip=True)
            if field_name.lower() in first_td_text.lower():
                second_td = tds[1]
                links = []
                for link in second_td.find_all('a'):
                    links.append(link.get_text(strip=True))
                return links
    
    return []


def get_text_from_tag(tag: Tag) -> str:
    """
    Extract text from a tag, handling <br> as newlines.
    
    Args:
        tag: BeautifulSoup Tag object
        
    Returns:
        Text content with <br> converted to newlines
    """
    if not tag:
        return ''
    
    text_parts = []
    for element in tag.contents:
        if isinstance(element, NavigableString):
            text_parts.append(str(element).strip())
        elif element.name == 'br':
            text_parts.append('\n')
        elif hasattr(element, 'get_text'):
            text_parts.append(element.get_text(separator=' ', strip=True))
    
    result = ' '.join(text_parts).strip()
    result = re.sub(r'\s+', ' ', result)
    return result
