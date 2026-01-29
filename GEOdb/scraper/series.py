import aiohttp
import asyncio
from GEOdb.common.types import GEOSeriesInfo
from GEOdb.common.web import get_aiohttp_session
from GEOdb.common.configs import SERIES_DETAIL_URL
from GEOdb.scraper.series_detail import parse_series_page


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
