# GEOdb
An asynchronous Python library for the Gene Expression Omnibus (GEO) database

## Usage

### parser

`from GEOdb.parser.series import parse_file, parse_item`

Either parse a file:

`parse_file('/path/to/GEO/downloaded.txt')`

Or parse a text:

```python
t = """1. Transcriptional profiling of human KIR+ CD8 T cells
(Submitter supplied) This SuperSeries is composed of the SubSeries listed below.
Organism:	Homo sapiens
Type:		Expression profiling by high throughput sequencing; Other
Platforms: GPL20301 GPL18573 4548 Samples
FTP download: GEO (TXT) ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE193nnn/GSE193442/
Series		Accession: GSE193442	ID: 200193442"""

parse_item(t)
```

```
GEOSeriesInfo(title='Transcriptional profiling of human KIR+ CD8 T cells',
              link='https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE193442',
              url='https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE193442',
              summary='(Submitter supplied) This SuperSeries is composed of '
                      'the SubSeries listed below.',
              organism='Homo sapiens',
              type='Expression profiling by high throughput sequencing; Other',
              platform='GPL20301',
              samples=4548,
              id='GSE193442',
              accession='GSE193442',
              series_id=200193442,
              ftp='ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE193nnn/GSE193442/',
              sra=None)
```
