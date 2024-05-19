import aiohttp
from GEOdb.common.configs import USER_AGENT


def get_aiohttp_session():
    return aiohttp.ClientSession(headers={'User-Agent': USER_AGENT})
