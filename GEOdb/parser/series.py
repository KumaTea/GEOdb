import csv
import logging
from typing import Union, TextIO
from GEOdb.common.types import GEOSeriesInfo
from GEOdb.common.configs import SERIES_DETAIL_URL


def parse_item(item: str) -> GEOSeriesInfo:
    organism = ''
    series_type = ''
    platform = ''
    samples = 0
    accession = ''
    series_id = 0
    ftp = None
    sra = None

    item_split = item.split('\n')

    title = item_split[0].split('.')[1].strip()
    summary = item_split[1].strip()

    for line in item_split[2:]:
        if 'Organism' in line:
            organism = line.split(':')[1].replace('\t', '').strip()
        elif 'Type' in line:
            series_type = line.split(':')[1].replace('\t', '').strip()
        elif 'Platform' in line:
            if ':' in line:
                platform = line.split(':')[1].strip().split(' ')[0].replace('\t', '').strip()
            samples = int(line.split(' ')[-2].replace('\t', '').strip())
        elif 'FTP' in line:
            ftp = line.split(' ')[-1].replace('\t', '').strip()
        elif 'SRA' in line:
            sra = line.split(' ')[-1].replace('\t', '').strip()
        elif 'Series' in line:
            accession = line.split(':')[1].split('\t')[0].strip()
            series_id = int(line.split(':')[-1].replace('\t', '').strip())

    link = f'{SERIES_DETAIL_URL}{accession}'

    required_fields = [title, link, organism, series_type, platform, samples, summary, accession, series_id]
    required_field_names = [
        'title', 'link', 'organism', 'series_type', 'platform', 'samples', 'summary', 'accession', 'series_id'
    ]
    indices = [i for i, value in enumerate(required_fields) if not value]
    if indices:
        logging.warning(f'Incomplete data for {accession}:\t' + ', '.join([required_field_names[i] for i in indices]))

    item_info = GEOSeriesInfo(
        title=title,
        link=link, url=link,
        summary=summary,
        organism=organism,
        type=series_type,
        platform=platform,
        samples=samples,
        id=accession, accession=accession,
        series_id=series_id,
        ftp=ftp,
        sra=sra
    )
    return item_info


def parse_items(items: str) -> list[GEOSeriesInfo]:
    items_split = items.split('\n\n')
    items_strip = [item.strip() for item in items_split]
    series = [parse_item(item) for item in items_strip]
    return series


def parse_file(file: Union[str, TextIO]) -> list[GEOSeriesInfo]:
    if isinstance(file, str):
        with open(file, 'r', encoding='utf-8') as f:
            items = f.read()
    else:
        items = file.read()
    series = parse_items(items)
    return series


def csv_writer_core(writer: csv.DictWriter, series: list[GEOSeriesInfo]):
    writer.writeheader()
    for item in series:
        del item.url
        del item.accession
        # item.title = item.title.replace(',', '，').replace('"', "'")
        # item.summary = item.summary.replace(',', '，').replace('"', "'")
        # item_dict = item.__dict__
        # del item_dict['url']
        # del item_dict['accession']
        # for key in item_dict:
        #     if item_dict[key] in ['', None]:
        #         item_dict[key] = 'none'
        writer.writerow(item.__dict__)


def series_list_to_csv(series: list[GEOSeriesInfo], file: Union[str, TextIO]):
    headers = ['title', 'link', 'summary', 'organism', 'type', 'platform', 'samples', 'id', 'series_id', 'ftp', 'sra']
    if isinstance(file, str):
        with open(file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            csv_writer_core(writer, series)
    else:
        writer = csv.DictWriter(file, fieldnames=headers)
        csv_writer_core(writer, series)
