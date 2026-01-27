import aiohttp
import asyncio
import logging
from datetime import datetime
from tqdm import tqdm
from bs4.element import Tag
from bs4 import BeautifulSoup
from urllib.parse import unquote_plus
from GEOdb.common.types import GEOSeriesInfo, GEOSeriesInfoExtra
from GEOdb.common.web import get_aiohttp_session
from GEOdb.common.configs import NCBI_HOST, SERIES_URL, SERIES_DETAIL_URL
from GEOdb.scraper.series_detail import parse_series_page


def extract_post_data(raw_data: str) -> dict:
    data = {}
    items = raw_data.split('&')
    for item in items:
        key, value = item.split('=')
        data[unquote_plus(key)] = unquote_plus(value)
    return data


async def get_search_page(session: aiohttp.ClientSession, term: str, page_index: int = 1, bar: tqdm = None) -> str:
    # term = quote_plus(term)
    # async with session.get(SERIES_URL + f'?term={term}') as response:
    #     return await response.text()

    # data = {k: quote_plus(v) for k, v in data.items()}
    # don't do that

    data = {
        'term': term,
        # 'EntrezSystem2.PEntrez.Gds.Entrez_PageController.PreviousPageName': 'results',
        'EntrezSystem2.PEntrez.Gds.Gds_Facets.FacetsUrlFrag': 'filters=seriesGds',

        'EntrezSystem2.PEntrez.Gds.Gds_Facets.FacetSubmitted': 'true' if page_index == 1 else 'false',
        # THIS LINE IS CRITICAL for filtering series

        'EntrezSystem2.PEntrez.Gds.Gds_ResultsPanel.Entrez_Pager.cPage': max(1, page_index - 1),
        'EntrezSystem2.PEntrez.Gds.Gds_ResultsPanel.Entrez_Pager.CurrPage': page_index,
    }
    async with session.post(SERIES_URL, data=data) as response:
        # return await response.text()
        html = await response.text()
        if bar:
            bar.update(1)
        return html


async def get_init_page(session: aiohttp.ClientSession, term: str) -> str:
    return await get_search_page(session, term, 1)


def parse_items_count(html: str) -> int:
    if 'No items found.' in html:
        return 0
    soup = BeautifulSoup(html, 'html.parser')
    count = soup.find('h3', class_='result_count')
    text = count.text
    # Example: 'Items: 1 to 20 of 8274'
    items_count = text.split(' ')[-1]
    return int(items_count)


def parse_item(item: Tag) -> GEOSeriesInfo:
    title_text = ''
    link = ''
    organism = ''
    series_type = ''
    platform = ''
    samples = 0
    summary = ''
    accession = ''
    series_id = 0

    try:
        title = item.find('p', class_='title')
        title_text = title.text
        link = NCBI_HOST + title.find('a').get('href')
    except AttributeError:
        pass

    supp = item.find('div', class_='supp')
    for dl in supp.find_all('dl', class_='details'):
        try:
            dt = dl.find('dt')
            dd = dl.find('dd')
            if 'Organism' in dt.text:
                organism = dd.text
            elif 'Type' in dt.text:
                series_type = dd.text
            elif 'Platform' in dt.text:
                platform = dd.text
                # Example: '11 Samples'
                # samples = int(dl.find_all('a')[1].text.split(' ')[0])
                for a in dl.find_all('a'):
                    if 'Samples' in a.text:
                        samples = int(a.text.split(' ')[0])
                        break
            dl.replace_with('')
        except AttributeError:
            pass
    try:
        supp.find('a').replace_with('')
        summary = supp.text
    except AttributeError:
        pass

    aux = item.find('div', class_='aux')
    for dl in aux.find_all('dl', class_='rprtid'):
        dt = dl.find('dt')
        dd = dl.find('dd')
        if 'Accession' in dt.text:
            accession = dd.text
        elif 'ID' in dt.text:
            series_id = int(dd.text)

    if not all([title_text, link, organism, series_type, platform, summary, accession, series_id]):
        logging.warning(f'Incomplete data for {accession}:\t{title_text}')

    # Use current date as fallback for status/date
    current_date = datetime.now()

    item_info = GEOSeriesInfo(
        title=title_text,
        date=current_date,
        status=current_date,
        link=link,
        url=link,
        organism=organism,
        type=series_type,
        summary=summary,
        design='',  # Not available in search results
        contributors=[],  # Not available in search results
        citation=None,
        extra=None,  # Not available in search results
        platform=platform,
        samples=[],  # Empty list - samples not available in search results
        samples_count=samples,
        id=accession,
        accession=accession,
        series_id=series_id,
        ftp=None,
        sra=None,
    )
    return item_info


def parse_items(html: str) -> list[GEOSeriesInfo]:
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('div', class_='rslt')
    series = [parse_item(item) for item in items]
    return series


async def query_series(term: str) -> list[GEOSeriesInfo]:
    series_list = []
    session = get_aiohttp_session()

    init_page = await get_init_page(session, term)
    items_count = parse_items_count(init_page)
    pages_count = items_count // 20 + 1
    logging.info(f'Found {items_count} items')
    logging.info(f'Will parse {pages_count} pages')

    pbar = tqdm(total=pages_count - 1, desc='Parsing pages', unit='page')
    tasks = [get_search_page(session, term, i, pbar) for i in range(2, pages_count + 1)]
    pages = await asyncio.gather(*tasks)
    series_list.extend(parse_items(init_page))
    for page in pages:
        series_list.extend(parse_items(page))

    await session.close()
    return series_list


async def get_series_detail_page(session: aiohttp.ClientSession, accession: str) -> str:
    """
    Fetch the detailed HTML page for a series.
    
    Args:
        session: aiohttp ClientSession
        accession: Series accession (e.g., 'GSE5370')
        
    Returns:
        HTML content of the detailed series page
    """
    url = f'{SERIES_DETAIL_URL}{accession}'
    async with session.get(url) as response:
        return await response.text()


async def get_series_detail(accession: str, get_sample_details: bool = False) -> GEOSeriesInfo:
    """
    Fetch and parse a detailed series page.
    
    Args:
        accession: Series accession (e.g., 'GSE5370')
        get_sample_details: If True, fetch full sample details. If False, create minimal
                           sample objects with only id (accession) and title.
        
    Returns:
        GEOSeriesInfo object with full details
    """
    session = get_aiohttp_session()
    try:
        html = await get_series_detail_page(session, accession)
        return parse_series_page(html, accession, get_sample_details=get_sample_details)
    finally:
        await session.close()


async def get_series_details(accessions: list[str], get_sample_details: bool = False) -> list[GEOSeriesInfo]:
    """
    Fetch and parse multiple detailed series pages concurrently.
    
    Args:
        accessions: List of series accessions (e.g., ['GSE5370', 'GSE199152'])
        get_sample_details: If True, fetch full sample details. If False, create minimal
                           sample objects with only id (accession) and title.
        
    Returns:
        List of GEOSeriesInfo objects with full details
    """
    session = get_aiohttp_session()
    try:
        tasks = [get_series_detail_page(session, acc) for acc in accessions]
        html_pages = await asyncio.gather(*tasks)
        return [parse_series_page(html, acc, get_sample_details=get_sample_details) for html, acc in zip(html_pages, accessions)]
    finally:
        await session.close()
