from datetime import datetime
from dataclasses import dataclass


@dataclass
class GEOSample:
    title: str

    date: datetime
    status: datetime  # alias for date
    type: str  # sample type: SRA, etc.

    platform: str
    series: str

    source_name: str = None
    organism: str = None
    characteristics: str = None
    treatment_protocol: str = None
    extracted_molecule: str = None
    extraction_protocol: str = None
    label: str = None
    label_protocol: str = None
    hybridization_protocol: str = None
    scan_protocol: str = None
    library_strategy: str = None
    library_source: str = None
    library_selection: str = None
    instrument_model: str = None
    description: str = None
    data_processing: str = None


@dataclass
class GEOSeriesInfoExtra:
    submission: datetime = None
    last_update: datetime = None
    contact: str = None
    department: str = None
    email: str = None
    phone: str = None
    organization: str = None
    street: str = None
    city: str = None
    state: str = None
    zip_code: str = None
    country: str = None


@dataclass
class GEOSeriesInfo:
    title: str
    link: str
    url: str  # alias
    organism: str
    type: str  # experiment type: array, high throughput sequencing, etc.
    summary: str
    platform: str
    samples_count: int
    id: str
    accession: str  # alias
    series_id: int

    date: datetime = None
    status: datetime = None  # alias for date
    design: str = None
    contributors: list[str] = None
    samples: list[GEOSample] = None
    citation: str = None
    extra: GEOSeriesInfoExtra = None
    ftp: str = None
    sra: str = None
