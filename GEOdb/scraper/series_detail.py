"""
Parser for detailed GEO Series (GSE) HTML pages.
"""
import re
import logging
from typing import Optional
from datetime import datetime
from bs4 import BeautifulSoup
from GEOdb.common.configs import NCBI_HOST
from GEOdb.scraper.sample_detail import parse_sample_page
from GEOdb.common.types import GEOSeriesInfo, GEOSeriesInfoExtra, GEOSample
from GEOdb.scraper.utils import parse_geo_date, get_table_row_text, get_table_row_text_bgcolor


def extract_contributors(soup: BeautifulSoup) -> list[str]:
    """
    Extract contributor names from the HTML.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        List of contributor names
    """
    contributors = []
    rows = soup.find_all('tr', valign='top')
    for row in rows:
        tds = row.find_all('td')
        if len(tds) >= 2:
            first_td_text = tds[0].get_text(strip=True)
            if 'Contributor' in first_td_text:
                second_td = tds[1]
                # Find all author links
                for link in second_td.find_all('a'):
                    author_name = link.get_text(strip=True)
                    if author_name:
                        contributors.append(author_name)
                # If no links, try getting text directly
                if not contributors:
                    text = second_td.get_text(strip=True)
                    if text and text not in ['Citation missing', '']:
                        contributors.append(text)
                break
    
    return contributors


def extract_citation(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract citation information.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Citation string or None
    """
    rows = soup.find_all('tr', valign='top')
    for row in rows:
        tds = row.find_all('td')
        if len(tds) >= 2:
            first_td_text = tds[0].get_text(strip=True)
            if 'Citation' in first_td_text:
                second_td = tds[1]
                text = second_td.get_text(strip=True)
                # Skip placeholder messages
                if text and 'Has this study been published' not in text:
                    return text
    return None


def extract_platforms(soup: BeautifulSoup) -> str:
    """
    Extract platform information.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Platform string (comma-separated if multiple)
    """
    platforms = []
    rows = soup.find_all('tr', valign='top')
    for row in rows:
        tds = row.find_all('td')
        if len(tds) >= 2:
            first_td_text = tds[0].get_text(strip=True)
            if 'Platform' in first_td_text:
                second_td = tds[1]
                # Find all platform links
                for link in second_td.find_all('a'):
                    platform = link.get_text(strip=True)
                    if platform:
                        platforms.append(platform)
                break
    
    return ', '.join(platforms) if platforms else ''


def extract_sample_accessions(soup: BeautifulSoup) -> list[str]:
    """
    Extract sample accession numbers from the HTML.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        List of sample accession numbers (e.g., ['GSM74359', 'GSM74360', ...])
    """
    sample_accessions = []
    rows = soup.find_all('tr', valign='top')
    
    for row in rows:
        tds = row.find_all('td')
        if len(tds) >= 2:
            first_td_text = tds[0].get_text(strip=True)
            if 'Samples' in first_td_text or 'Sample' in first_td_text:
                # Find all sample links in the row
                second_td = tds[1]
                # Look in nested tables too
                all_tables = [second_td] + second_td.find_all('table')
                for table in all_tables:
                    for link in table.find_all('a', href=re.compile(r'acc=GSM\d+')):
                        href = link.get('href', '')
                        # Extract GSM number from href
                        match = re.search(r'acc=(GSM\d+)', href)
                        if match:
                            sample_accessions.append(match.group(1))
                        else:
                            # Fallback: use link text if it looks like a GSM number
                            link_text = link.get_text(strip=True)
                            if re.match(r'^GSM\d+$', link_text):
                                sample_accessions.append(link_text)
                break
    
    return sample_accessions


def extract_sample_accessions_and_titles(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """
    Extract sample accession numbers and their titles from the HTML.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        List of tuples (accession, title) (e.g., [('GSM74359', 'FSH-NHM-3UA-s2'), ...])
    """
    sample_data = []
    rows = soup.find_all('tr', valign='top')
    
    for row in rows:
        tds = row.find_all('td')
        if len(tds) >= 2:
            first_td_text = tds[0].get_text(strip=True)
            if 'Samples' in first_td_text or 'Sample' in first_td_text:
                # Find all sample links in the row
                second_td = tds[1]
                # Look in nested tables too (including hidden divs)
                all_tables = [second_td] + second_td.find_all('table')
                # Also check for hidden divs with samples
                hidden_divs = second_td.find_all('div', id=re.compile(r'L\d+div'))
                for div in hidden_divs:
                    all_tables.extend(div.find_all('table'))
                
                for table in all_tables:
                    # Find all rows in the table
                    for tr in table.find_all('tr'):
                        tds_in_row = tr.find_all('td')
                        if len(tds_in_row) >= 2:
                            # First td contains the accession link
                            link = tds_in_row[0].find('a', href=re.compile(r'acc=GSM\d+'))
                            if link:
                                href = link.get('href', '')
                                # Extract GSM number from href
                                match = re.search(r'acc=(GSM\d+)', href)
                                if match:
                                    accession = match.group(1)
                                else:
                                    # Fallback: use link text
                                    accession = link.get_text(strip=True)
                                
                                # Second td contains the title
                                title = tds_in_row[1].get_text(strip=True)
                                sample_data.append((accession, title))
                break
    
    return sample_data


def extract_ftp_link(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract FTP download link.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        FTP URL or None
    """
    # Look for FTP links in the download section
    ftp_links = soup.find_all('a', href=re.compile(r'^ftp://'))
    if ftp_links:
        return ftp_links[0].get('href')
    
    # Also check in the supplementary files table
    rows = soup.find_all('tr')
    for row in rows:
        for link in row.find_all('a', href=re.compile(r'^ftp://')):
            return link.get('href')
    
    return None


def extract_sra_link(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract SRA link from Relations section.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        SRA URL or None
    """
    rows = soup.find_all('tr', valign='top')
    for row in rows:
        tds = row.find_all('td')
        if len(tds) >= 2:
            first_td_text = tds[0].get_text(strip=True)
            if 'SRA' in first_td_text:
                link = tds[1].find('a')
                if link:
                    return link.get('href')
    return None


def parse_series_page(html: str, accession: str = None, get_sample_details: bool = False) -> GEOSeriesInfo:
    """
    Parse a detailed GEO Series HTML page.
    
    Args:
        html: HTML content of the series page
        accession: Optional accession number (e.g., GSE5370)
                  If not provided, will try to extract from HTML
        
    Returns:
        GEOSeriesInfo object
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract accession if not provided
    if not accession:
        accession_elem = soup.find('strong', class_='acc')
        if accession_elem:
            accession = accession_elem.get_text(strip=True)
            # Remove "Series " prefix if present
            accession = accession.replace('Series ', '')
    
    # Extract series_id from the accession page if available
    series_id = 0
    # Try to extract from link or other metadata
    
    # Extract title
    title = get_table_row_text(soup, 'Title') or ''
    series_title = title
    
    # Extract link
    link = f'{NCBI_HOST}/geo/query/acc.cgi?acc={accession}'
    
    # Extract status/date
    status_text = get_table_row_text(soup, 'Status') or ''
    status_date = parse_geo_date(status_text)
    if not status_date:
        logging.warning(f'Could not parse status date for {accession}: {status_text}')
        # Use current date as fallback
        status_date = datetime.now()
    
    # Extract organism
    organism = None
    rows = soup.find_all('tr', valign='top')
    for row in rows:
        tds = row.find_all('td')
        if len(tds) >= 2:
            first_td_text = tds[0].get_text(strip=True)
            if 'Organism' in first_td_text:
                organism_link = tds[1].find('a')
                if organism_link:
                    organism = organism_link.get_text(strip=True)
                    break
    
    if not organism:
        organism = get_table_row_text(soup, 'Organism') or ''
    
    # Extract experiment type
    experiment_type = get_table_row_text(soup, 'Experiment type')
    if not experiment_type:
        experiment_type = get_table_row_text(soup, 'Type')
    
    # Extract summary
    summary = get_table_row_text(soup, 'Summary') or ''
    
    # Extract overall design
    design = get_table_row_text(soup, 'Overall design') or ''
    
    # Extract contributors
    contributors = extract_contributors(soup)
    
    # Extract citation
    citation = extract_citation(soup)
    
    # Extract platform
    platform = extract_platforms(soup)
    
    # Extract sample count and accessions
    sample_count_text = None
    rows = soup.find_all('tr', valign='top')
    for row in rows:
        tds = row.find_all('td')
        if len(tds) >= 2:
            first_td_text = tds[0].get_text(strip=True)
            if 'Samples' in first_td_text:
                # Extract count from text like "Samples (9)"
                match = re.search(r'\((\d+)\)', first_td_text)
                if match:
                    sample_count_text = int(match.group(1))
                    break
    
    # Extract sample data (accessions and titles)
    if get_sample_details:
        sample_accessions = extract_sample_accessions(soup)
        # placeholder
        get_sample_html = lambda x: ''
        samples_html = {acc: get_sample_html(acc) for acc in sample_accessions}
        samples_list = [parse_sample_page(k, v) for k, v in samples_html.items()]
        samples_dict = {sample.id: sample for sample in samples_list}
    else:
        # Extract sample accessions and titles for minimal objects
        sample_data = extract_sample_accessions_and_titles(soup)
        sample_accessions = [acc for acc, _ in sample_data]
        # Create minimal GEOSample objects with only id (accession) and title
        samples_list = []
        for sample_acc, sample_title in sample_data:
            # Store title with accession for identification: "GSM74359: FSH-NHM-3UA-s2"
            if sample_title:
                title = sample_title
            else:
                title = sample_acc
            sample = GEOSample(
                title=title,
                id=sample_acc,
                date=status_date,
                status=status_date,
                type='',  # Not available in summary
                platform=platform or '',
                series=accession,
            )
            samples_list.append(sample)
        samples_dict = {sample.id: sample for sample in samples_list}
    
    samples_count = sample_count_text or len(sample_accessions)
    
    # Extract extra information (contact details)
    extra = GEOSeriesInfoExtra(
        submission=parse_geo_date(get_table_row_text_bgcolor(soup, 'Submission date')),
        last_update=parse_geo_date(get_table_row_text_bgcolor(soup, 'Last update date')),
        contact=get_table_row_text_bgcolor(soup, 'Contact name'),
        department=get_table_row_text_bgcolor(soup, 'Department'),
        email=get_table_row_text_bgcolor(soup, 'E-mail'),
        phone=get_table_row_text_bgcolor(soup, 'Phone'),
        organization=get_table_row_text_bgcolor(soup, 'Organization name'),
        street=get_table_row_text_bgcolor(soup, 'Street address'),
        city=get_table_row_text_bgcolor(soup, 'City'),
        state=get_table_row_text_bgcolor(soup, 'State') or get_table_row_text_bgcolor(soup, 'province'),
        zip_code=get_table_row_text_bgcolor(soup, 'ZIP') or get_table_row_text_bgcolor(soup, 'Postal code'),
        country=get_table_row_text_bgcolor(soup, 'Country'),
    )
    
    # Extract FTP link
    ftp = extract_ftp_link(soup)
    
    # Extract SRA link
    sra = extract_sra_link(soup)
    
    # Create GEOSeriesInfo object
    series_info = GEOSeriesInfo(
        title=series_title,
        date=status_date,
        status=status_date,
        link=link,
        url=link,
        organism=organism,
        type=experiment_type or '',
        summary=summary,
        design=design,
        contributors=contributors,
        citation=citation,
        extra=extra,
        platform=platform,
        samples=samples_dict,
        samples_count=samples_count,
        id=accession,
        accession=accession,
        series_id=series_id,
        ftp=ftp,
        sra=sra,
    )
    
    return series_info
