# enginerzin.github.io

## Static publications

The page reads only `assets/publications.json`. There are no scheduled DBLP
requests, automatic commits, or runtime requests to DBLP.

**Current status (2026-10-21): source unavailable.** The canonical PID page and
XML/BibTeX/RIS endpoints on DBLP and its official mirrors returned Anubis HTML
or timed out during retrieval. No complete bibliography was obtained. The JSON
explicitly records this state and the page shows an unavailable message, not a
zero-publication or completeness claim. This migration remains incomplete until
a verified export is imported.

### Manual update

1. Download the full XML bibliography from <https://dblp.org/pid/15/2739> using
   its “export bibliography → XML” link (canonical export:
   <https://dblp.org/pid/15/2739.xml>). An HTML challenge is not an export.
2. Run `python3 scripts/update_publications.py /path/to/export.xml --retrieved-on YYYY-MM-DD`
   using the actual download date. This command performs no network requests.
3. Review `data/dblp-15-2739.xml` and `assets/publications.json` together. The
   importer checks PID, nonempty source count, every record, and unique DBLP
   keys before writing. It preserves inline title text and author ordering.
   The JSON includes the input SHA-256, retrieval date, and source record count.
4. Verify the source count against the canonical bibliography, inspect the
   newest and oldest records, and test search and every type filter on
   `publications.html` using a local HTTP server before committing both files.

A successful import covers all records in that export, not publications outside
DBLP or changes since the download. Never substitute author-name search results
or an incomplete selection for the full PID bibliography.

Run importer checks with `python3 -m unittest discover -s tests` and loader checks
with `node tests/publications-loader.cjs`.
