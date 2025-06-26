import requests
import time
import json
from fuzzywuzzy import fuzz
from urllib.parse import quote


class ExternalAPIManager:
    """Manages external API calls for fetching reference metadata"""

    def __init__(self):
        self.semantic_scholar_base = "https://api.semanticscholar.org/graph/v1"
        self.crossref_base = "https://api.crossref.org/works"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Reference-Converter/1.0 (mailto:your-email@example.com)'
        })
        self.rate_limit_delay = 1.0  # seconds between API calls
        self.last_api_call = 0

    def _rate_limit(self):
        """Implement rate limiting for API calls"""
        now = time.time()
        if now - self.last_api_call < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - (now - self.last_api_call))
        self.last_api_call = time.time()

    def search_semantic_scholar(self, title, authors=None, year=None):
        """Search Semantic Scholar for paper metadata"""
        try:
            self._rate_limit()

            # Construct search query
            query = f'"{title}"'
            if authors:
                # Use first author for search
                first_author = authors.split(
                    ' and ')[0] if ' and ' in authors else authors
                query += f' author:"{first_author}"'

            params = {
                'query': query,
                'fields': 'title,authors,year,journal,venue,doi,url,abstract,citationCount,paperId',
                'limit': 5
            }

            response = self.session.get(
                f"{self.semantic_scholar_base}/paper/search", params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                papers = data.get('data', [])

                # Find best match based on title similarity
                best_match = None
                best_score = 0

                for paper in papers:
                    score = fuzz.ratio(
                        title.lower(), paper.get('title', '').lower())
                    if score > best_score and score > 70:  # Minimum threshold
                        best_score = score
                        best_match = paper

                return best_match

        except Exception as e:
            print(f"Semantic Scholar API error: {e}")

        return None

    def search_crossref(self, title, authors=None, year=None):
        """Search CrossRef for paper metadata"""
        try:
            self._rate_limit()

            # Construct search query
            query_parts = [title]
            if authors:
                first_author = authors.split(
                    ' and ')[0] if ' and ' in authors else authors
                query_parts.append(first_author)
            if year:
                query_parts.append(str(year))

            query = ' '.join(query_parts)

            params = {
                'query': query,
                'rows': 5,
                'select': 'title,author,published-print,published-online,container-title,DOI,URL,abstract,volume,issue,page'
            }

            response = self.session.get(
                self.crossref_base, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                items = data.get('message', {}).get('items', [])

                # Find best match based on title similarity
                best_match = None
                best_score = 0

                for item in items:
                    item_title = ' '.join(item.get('title', []))
                    score = fuzz.ratio(title.lower(), item_title.lower())
                    if score > best_score and score > 70:  # Minimum threshold
                        best_score = score
                        best_match = item

                return best_match

        except Exception as e:
            print(f"CrossRef API error: {e}")

        return None

    def enhance_reference(self, fields):
        """Enhance reference fields using external APIs"""
        enhanced_fields = fields.copy()

        title = fields.get('title', '').strip()
        authors = fields.get('author', '').strip()
        year = fields.get('year', '').strip()

        if not title:
            return enhanced_fields

        print(f"Enhancing reference: {title[:50]}...")

        # Try Semantic Scholar first
        semantic_data = self.search_semantic_scholar(title, authors, year)
        if semantic_data:
            enhanced_fields.update(self._parse_semantic_scholar_data(
                semantic_data, enhanced_fields))
            print(f"Enhanced with Semantic Scholar data")

        # Try CrossRef if still missing important fields
        missing_important_fields = not all([
            enhanced_fields.get('doi'),
            enhanced_fields.get('journal') or enhanced_fields.get('booktitle'),
            enhanced_fields.get('year'),
            enhanced_fields.get('pages') or enhanced_fields.get('volume')
        ])

        if missing_important_fields:
            crossref_data = self.search_crossref(title, authors, year)
            if crossref_data:
                enhanced_fields.update(self._parse_crossref_data(
                    crossref_data, enhanced_fields))
                print(f"Enhanced with CrossRef data")

        return enhanced_fields

    def _parse_semantic_scholar_data(self, data, existing_fields):
        """Parse Semantic Scholar API response"""
        enhanced = {}

        # Only add fields that are missing or empty
        if not existing_fields.get('title') and data.get('title'):
            enhanced['title'] = data['title']

        if not existing_fields.get('author') and data.get('authors'):
            authors = []
            for author in data['authors']:
                if author.get('name'):
                    authors.append(author['name'])
            if authors:
                enhanced['author'] = ' and '.join(authors)

        if not existing_fields.get('year') and data.get('year'):
            enhanced['year'] = str(data['year'])

        if not existing_fields.get('journal') and data.get('journal'):
            enhanced['journal'] = data['journal']['name']
        elif not existing_fields.get('journal') and data.get('venue'):
            enhanced['journal'] = data['venue']

        if not existing_fields.get('doi') and data.get('doi'):
            enhanced['doi'] = data['doi']

        if not existing_fields.get('url') and data.get('url'):
            enhanced['url'] = data['url']

        if not existing_fields.get('abstract') and data.get('abstract'):
            enhanced['abstract'] = data['abstract']

        return enhanced

    def _parse_crossref_data(self, data, existing_fields):
        """Parse CrossRef API response"""
        enhanced = {}

        # Only add fields that are missing or empty
        if not existing_fields.get('title') and data.get('title'):
            enhanced['title'] = ' '.join(data['title'])

        if not existing_fields.get('author') and data.get('author'):
            authors = []
            for author in data['author']:
                given = author.get('given', '')
                family = author.get('family', '')
                if family:
                    if given:
                        authors.append(f"{family}, {given}")
                    else:
                        authors.append(family)
            if authors:
                enhanced['author'] = ' and '.join(authors)

        # Handle publication date
        if not existing_fields.get('year'):
            pub_date = data.get(
                'published-print') or data.get('published-online')
            if pub_date and 'date-parts' in pub_date:
                date_parts = pub_date['date-parts'][0]
                if date_parts:
                    enhanced['year'] = str(date_parts[0])

        if not existing_fields.get('journal') and data.get('container-title'):
            enhanced['journal'] = data['container-title'][0]

        if not existing_fields.get('doi') and data.get('DOI'):
            enhanced['doi'] = data['DOI']

        if not existing_fields.get('url') and data.get('URL'):
            enhanced['url'] = data['URL']

        if not existing_fields.get('volume') and data.get('volume'):
            enhanced['volume'] = data['volume']

        if not existing_fields.get('number') and data.get('issue'):
            enhanced['number'] = data['issue']

        if not existing_fields.get('pages') and data.get('page'):
            enhanced['pages'] = data['page']

        return enhanced
