"""
Parser for detailed GEO Sample (GSM) HTML pages.
"""
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from GEOdb.common.types import GEOSample
from GEOdb.scraper.utils import parse_geo_date, get_table_row_text


def parse_sample_page(html: str, accession: str = None) -> GEOSample:
    """
    Parse a detailed GEO Sample HTML page.
    
    Args:
        html: HTML content of the sample page
        accession: Optional accession number (e.g., GSM5965334)
                  If not provided, will try to extract from HTML
        
    Returns:
        GEOSample object
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract accession if not provided
    if not accession:
        accession_elem = soup.find('strong', class_='acc')
        if accession_elem:
            accession = accession_elem.get_text(strip=True)
            # Remove "Sample " prefix if present
            accession = accession.replace('Sample ', '')
    
    # Extract title
    title = get_table_row_text(soup, 'Title') or ''
    
    # Extract status/date
    status_text = get_table_row_text(soup, 'Status') or ''
    status_date = parse_geo_date(status_text)
    if not status_date:
        logging.warning(f'Could not parse status date for {accession}: {status_text}')
        # Use current date as fallback
        status_date = datetime.now()
    
    # Extract sample type
    sample_type = get_table_row_text(soup, 'Sample type') or ''
    
    # Extract source name
    source_name = get_table_row_text(soup, 'Source name')
    
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
                else:
                    organism = tds[1].get_text(strip=True)
                    break
    
    if not organism:
        organism = get_table_row_text(soup, 'Organism') or ''
    
    # Extract characteristics
    characteristics = get_table_row_text(soup, 'Characteristics')
    
    # Extract extracted molecule
    extracted_molecule = get_table_row_text(soup, 'Extracted molecule')
    
    # Extract extraction protocol
    extraction_protocol = get_table_row_text(soup, 'Extraction protocol')
    
    # Extract library strategy
    library_strategy = get_table_row_text(soup, 'Library strategy')
    
    # Extract library source
    library_source = get_table_row_text(soup, 'Library source')
    
    # Extract library selection
    library_selection = get_table_row_text(soup, 'Library selection')
    
    # Extract instrument model
    instrument_model = get_table_row_text(soup, 'Instrument model')
    
    # Extract data processing
    data_processing = get_table_row_text(soup, 'Data processing')
    
    # Extract platform ID
    platform = None
    rows = soup.find_all('tr', valign='top')
    for row in rows:
        tds = row.find_all('td')
        if len(tds) >= 2:
            first_td_text = tds[0].get_text(strip=True)
            if 'Platform ID' in first_td_text or ('Platform' in first_td_text and 'ID' in first_td_text):
                platform_link = tds[1].find('a')
                if platform_link:
                    platform = platform_link.get_text(strip=True)
                    break
                else:
                    platform = tds[1].get_text(strip=True)
                    break
    
    # Extract series
    series = None
    rows = soup.find_all('tr', valign='top')
    for row in rows:
        tds = row.find_all('td')
        if len(tds) >= 2:
            first_td_text = tds[0].get_text(strip=True)
            if 'Series' in first_td_text:
                series_link = tds[1].find('a')
                if series_link:
                    series = series_link.get_text(strip=True)
                    break
    
    if not series:
        logging.warning(f'Could not find series for sample {accession}')
    
    # Create GEOSample object
    sample = GEOSample(
        title=title,
        id=accession,
        date=status_date,
        status=status_date,
        type=sample_type,
        source_name=source_name,
        organism=organism,
        characteristics=characteristics,
        extracted_molecule=extracted_molecule,
        extraction_protocol=extraction_protocol,
        library_strategy=library_strategy,
        library_source=library_source,
        library_selection=library_selection,
        instrument_model=instrument_model,
        data_processing=data_processing,
        platform=platform or '',
        series=series or '',
    )
    
    return sample
