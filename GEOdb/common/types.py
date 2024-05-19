from dataclasses import dataclass


@dataclass
class GEOSeriesInfo:
    title: str

    link: str
    url: str  # alias

    summary: str
    organism: str
    type: str
    platform: str
    samples: int

    id: str
    accession: str  # alias
    series_id: int

    ftp: str = None
    sra: str = None
