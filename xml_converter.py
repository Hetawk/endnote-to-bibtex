import xml.etree.ElementTree as ET
import traceback
import re
from datetime import datetime
import collections

# Import the external API manager for robust reference completion
try:
    from external_api_manager import ExternalAPIManager
    API_AVAILABLE = True
except ImportError:
    print("Warning: External API manager not available. Install requirements: pip install requests fuzzywuzzy python-Levenshtein")
    API_AVAILABLE = False


class XML:
    def __init__(self):
        # Initialize external API manager for robust reference completion
        self.api_manager = ExternalAPIManager() if API_AVAILABLE else None
        self.enable_api_enhancement = API_AVAILABLE  # Can be toggled via UI

        # Progress callback for GUI updates
        self.progress_callback = None

        self.entry_type_map = {
            'Journal Article': 'article',
            'Book': 'book',
            'Book Section': 'incollection',
            'Conference Paper': 'inproceedings',
            'Conference Proceedings': 'proceedings',
            'Conference Proceeding': 'proceedings',
            'Thesis': 'phdthesis',
            'Report': 'techreport',
            'Web Page': 'online',
            'Patent': 'patent',
            'Unpublished Work': 'unpublished',
            'Manuscript': 'unpublished',
            'Magazine Article': 'article',
            'Newspaper Article': 'article',
            'Electronic Article': 'article',
            'Generic': 'misc'
        }
        self.suppress_warnings = True  # Default to suppress warnings
        self.extract_styled_text = True  # Extract text from styled elements
        self.conversion_errors = []  # Track errors during conversion
        self.use_acm_style = False  # Default to standard BibTeX format
        self.use_string_definitions = True  # Option to enable/disable string definitions
        self.use_biblatex_fields = False  # Option to use BibLaTeX field names
        self.escape_latex_chars = True  # Escape LaTeX special characters
        self.debug_mode = True  # Enable debug mode by default to help diagnose issues

    def convert_to_bibtex(self, xml_data):
        # Reset collections and errors list
        self.conversion_errors = []
        self.journals = {}
        self.publishers = {}
        self.journal_name_to_key = {}

        # For debugging the conversion process
        print("Starting conversion process...")
        print(f"String definitions enabled: {self.use_string_definitions}")
        print(f"BibLaTeX fields enabled: {self.use_biblatex_fields}")
        print(f"ACM style enabled: {self.use_acm_style}")

        if isinstance(xml_data, str):
            try:
                # Check if XML data is empty or too short
                if len(xml_data.strip()) < 50:
                    error_msg = f"XML data appears to be too short or empty: '{xml_data[:50]}'"
                    print(error_msg)
                    self.conversion_errors.append(error_msg)
                    return ""
                xml_root = ET.fromstring(xml_data)
                print(f"XML root tag: {xml_root.tag}")
            except ET.ParseError as e:
                error_msg = f"Error parsing XML: {e}"
                print(error_msg)
                self.conversion_errors.append(error_msg)
                return ""
        elif isinstance(xml_data, ET.Element):
            xml_root = xml_data
        else:
            error_msg = "Invalid XML data type"
            print(error_msg)
            self.conversion_errors.append(error_msg)
            return ""

        # Find records with flexible path handling
        records = []
        # Try different common paths for records
        possible_paths = [
            './/record',
            './/records/record',
            './/xml/records/record',
            './/EndNote/records/record',
            './/xml/database/record'
        ]
        for path in possible_paths:
            found_records = xml_root.findall(path)
            if found_records:
                records = found_records
                print(f"Found {len(records)} records using path: {path}")
                break
        if not records:
            # Try to get more information about the XML structure
            xml_structure = self._describe_xml_structure(xml_root)
            error_msg = f"No records found in XML data. XML structure: {xml_structure}"
            print(error_msg)
            self.conversion_errors.append(error_msg)
            return ""

        # Only collect journal and publisher info if string definitions are enabled
        if self.use_string_definitions:
            try:
                # Report that we're collecting string definitions
                self._call_progress_callback(
                    0, len(records),
                    "Collecting journal and publisher information for string definitions..."
                )
                # Process journal and publisher information
                print(
                    "Collecting journal and publisher information for string definitions...")
                for record in records:
                    try:
                        self._collect_journal_info(record)
                    except Exception as e:
                        self.conversion_errors.append(
                            f"Error collecting journal info: {str(e)}")

                    try:
                        self._collect_publisher_info(record)
                    except Exception as e:
                        self.conversion_errors.append(
                            f"Error collecting publisher info: {str(e)}")
            except Exception as e:
                print(
                    f"Warning: Error in string definition collection: {str(e)}")
                self.use_string_definitions = False

        # Create a separate list for successful entries
        bibtex_entries = []
        processed_count = 0
        failures_count = 0

        # Second pass: convert entries to BibTeX
        for index, record in enumerate(records):
            try:
                processed_count += 1

                # Call progress callback and check for cancellation
                should_continue = self._call_progress_callback(
                    index + 1, len(records),
                    f"Processing record {index + 1}/{len(records)}"
                )
                if not should_continue:
                    print("Conversion cancelled by user")
                    break

                # Print details for first few records and every 20th
                if index < 3 or (index % 20 == 0):
                    print(f"Processing record {index + 1}/{len(records)}...")

                # Extract basic record information for error reporting
                title_info = "[No title]"
                try:
                    title_elem = record.find('.//titles/title')
                    if title_elem is not None:
                        title_text = self._extract_text_from_styled_element(
                            title_elem)
                        if title_text:
                            title_info = title_text[:50] + \
                                "..." if len(title_text) > 50 else title_text
                except Exception:
                    pass

                # Get entry type from ref-type
                ref_type_elem = record.find('.//ref-type')
                if ref_type_elem is not None and 'name' in ref_type_elem.attrib:
                    entry_type_name = ref_type_elem.attrib['name']
                    if index < 3:
                        print(f"Record type: {entry_type_name}")
                else:
                    entry_type_name = record.attrib.get('ref-type', 'Generic')
                # Map the entry type name to a BibTeX entry type
                if entry_type_name == 'Conference Paper':
                    entry_type = 'inproceedings'
                else:
                    entry_type = self.entry_type_map.get(
                        entry_type_name, 'misc')

                # Generate entry key based on author and year in ACM format style
                author_elem = record.find('.//contributors/authors/author')
                year_elem = record.find('.//dates/year')

                if author_elem is not None and year_elem is not None:
                    author_text = self._extract_text_from_styled_element(
                        author_elem)
                    year_text = self._extract_text_from_styled_element(
                        year_elem)

                    if author_text and year_text:
                        # Extract last name of first author
                        if ',' in author_text:
                            last_name = author_text.split(',')[0].strip()
                        else:
                            name_parts = author_text.split()
                            last_name = name_parts[-1].strip()

                        # Clean the last name (remove special characters)
                        last_name = ''.join(
                            c for c in last_name if c.isalnum())

                        # Format key like "Mamo24" instead of "ref1167"
                        entry_key = f"{last_name}{year_text[-2:]}"
                    else:
                        # Fall back to a more unique identifier
                        key_elem = record.find('.//rec-number')
                        entry_key = f"{last_name or 'Entry'}{key_elem.text if key_elem is not None and key_elem.text else index + 1}"
                else:
                    # If no author or year, create a sensible fallback
                    title_elem = record.find('.//titles/title')
                    if title_elem is not None:
                        title_text = self._extract_text_from_styled_element(
                            title_elem)
                        if title_text:
                            # Create key from first letters of significant title words
                            words = [w for w in re.findall(r'\b[A-Za-z]+\b', title_text)
                                     if len(w) > 3 and w.lower() not in {'with', 'from', 'this', 'that', 'and', 'for'}]
                            if words:
                                entry_key = ''.join(
                                    word[0].upper() for word in words[:3])
                                if year_elem is not None and self._extract_text_from_styled_element(year_elem):
                                    year_text = self._extract_text_from_styled_element(
                                        year_elem)
                                    entry_key += year_text[-2:]
                                else:
                                    entry_key += str(index + 1)
                            else:
                                entry_key = f"Entry{index + 1}"
                        else:
                            entry_key = f"Entry{index + 1}"
                    else:
                        entry_key = f"Entry{index + 1}"

                # Extract fields from XML record
                fields = self._extract_fields_from_xml(record)
                if not fields:
                    # Skip if no fields were extracted
                    self.conversion_errors.append(
                        f"No fields extracted for record {index + 1}")
                    failures_count += 1
                    continue

                # Get required fields list for validation
                required_fields = self._get_required_fields(entry_type)
                self._collect_publisher_info(record)
                # Format the fields for BibTeX
                if self.use_acm_style:
                    formatted_fields = self._format_fields_acm_style(
                        fields, required_fields, entry_type)
                else:
                    formatted_fields = self._format_fields(
                        fields, required_fields)

                # Create the full BibTeX entry with content
                bibtex_entry = f"@{entry_type}{{{entry_key},{formatted_fields}\n}}"
                bibtex_entries.append(bibtex_entry)
            except Exception as e:
                failures_count += 1
                error_msg = f"Error processing record {index + 1}: {str(e)}"
                print(error_msg)
                print(traceback.format_exc())
                self.conversion_errors.append(error_msg)
                continue

        # Provide detailed conversion statistics
        print(
            f"Processed {processed_count} records: {len(bibtex_entries)} successes, {failures_count} failures")

        if not bibtex_entries:
            error_msg = "Conversion failed: No BibTeX entries generated"
            print(error_msg)

            # If we have errors, print them
            if self.conversion_errors:
                print(f"Encountered {len(self.conversion_errors)} errors")
                for err in self.conversion_errors[:5]:
                    print(f"- {err}")
            return ""

        # Remove duplicates and ensure unique keys
        self._call_progress_callback(
            len(records), len(records),
            "Removing duplicates and ensuring unique keys..."
        )
        deduplicated_entries = self._remove_duplicates_and_fix_keys(
            bibtex_entries)
        print(
            f"Deduplicated from {len(bibtex_entries)} to {len(deduplicated_entries)} unique entries")

        # Generate output with string definitions if applicable
        if self.use_string_definitions:
            # Report that we're generating string definitions
            self._call_progress_callback(
                len(records), len(records),
                "Generating BibTeX string definitions..."
            )
            string_definitions = self._generate_string_definitions()
            if string_definitions:
                print(
                    f"Generated {string_definitions.count('@String')} string definitions")
                return string_definitions + '\n\n' + '\n\n'.join(deduplicated_entries)

        # Default return if no string definitions
        return '\n\n'.join(deduplicated_entries)

    def _extract_fields_from_xml(self, record):
        """Extract fields from the XML record with better error handling and API enhancement."""
        try:
            fields = {}

            # Extract title
            title_elem = record.find('.//titles/title')
            if title_elem is not None:
                title_text = self._extract_text_from_styled_element(title_elem)
                if title_text:
                    fields['title'] = title_text.strip()

            # Extract authors
            authors_elem = record.find('.//contributors/authors')
            if authors_elem is not None:
                author_names = []
                for author in authors_elem.findall('.//author'):
                    author_text = self._extract_text_from_styled_element(
                        author)
                    if author_text:
                        author_names.append(author_text.strip())
                if author_names:
                    fields['author'] = ' and '.join(author_names)

            # Extract year
            year_elem = record.find('.//dates/year')
            if year_elem is not None:
                year_text = self._extract_text_from_styled_element(year_elem)
                if year_text:
                    fields['year'] = year_text.strip()

            # Extract journal/book title
            secondary_title = record.find('.//titles/secondary-title')
            if secondary_title is not None:
                secondary_text = self._extract_text_from_styled_element(
                    secondary_title)
                if secondary_text:
                    ref_type_elem = record.find('.//ref-type')
                    if ref_type_elem is not None and 'name' in ref_type_elem.attrib:
                        if ref_type_elem.attrib['name'] == 'Journal Article':
                            fields['journal'] = secondary_text.strip()
                        else:
                            fields['booktitle'] = secondary_text.strip()
                    else:
                        fields['journal'] = secondary_text.strip()

            # Extract additional fields we might need
            volume_elem = record.find('.//volume')
            if volume_elem is not None:
                volume_text = self._extract_text_from_styled_element(
                    volume_elem)
                if volume_text:
                    fields['volume'] = volume_text.strip()

            number_elem = record.find('.//number')
            if number_elem is not None:
                number_text = self._extract_text_from_styled_element(
                    number_elem)
                if number_text:
                    fields['number'] = number_text.strip()

            pages_elem = record.find('.//pages')
            if pages_elem is not None:
                pages_text = self._extract_text_from_styled_element(pages_elem)
                if pages_text:
                    fields['pages'] = pages_text.strip()

            doi_elem = record.find('.//electronic-resource-num')
            if doi_elem is not None:
                doi_text = self._extract_text_from_styled_element(doi_elem)
                if doi_text:
                    fields['doi'] = doi_text.strip()

            # Extract URL if available
            url_elem = record.find('.//urls/related-urls/url')
            if url_elem is not None:
                url_text = self._extract_text_from_styled_element(url_elem)
                if url_text:
                    fields['url'] = url_text.strip()

            # Extract abstract if available
            abstract_elem = record.find('.//abstract')
            if abstract_elem is not None:
                abstract_text = self._extract_text_from_styled_element(
                    abstract_elem)
                if abstract_text:
                    fields['abstract'] = abstract_text.strip()

            # Extract publisher if available
            publisher_elem = record.find('.//publisher')
            if publisher_elem is not None:
                publisher_text = self._extract_text_from_styled_element(
                    publisher_elem)
                if publisher_text:
                    fields['publisher'] = publisher_text.strip()

            # Extract keywords if available
            keywords_elem = record.find('.//keywords')
            if keywords_elem is not None:
                keywords = []
                for keyword in keywords_elem.findall('.//keyword'):
                    keyword_text = self._extract_text_from_styled_element(
                        keyword)
                    if keyword_text:
                        keywords.append(keyword_text.strip())
                if keywords:
                    fields['keywords'] = ', '.join(keywords)

            # Enhanced reference completion using external APIs if enabled
            if self.debug_mode:
                print(
                    f"Attempting to enhance reference: {fields.get('title', '')[:50]}...")
            if (self.enable_api_enhancement and self.api_manager and
                    len(fields.get('title', '')) > 10):
                # Check if we're missing critical fields
                missing_critical_fields = not all([
                    fields.get('doi'),
                    fields.get('journal') or fields.get('booktitle'),
                    fields.get('year'),
                    fields.get('pages') or fields.get(
                        'volume') or fields.get('number')
                ])

                if missing_critical_fields:
                    try:
                        enhanced_fields = self.api_manager.enhance_reference(
                            fields)

                        # Count how many new fields were added
                        added_fields = []
                        for key, value in enhanced_fields.items():
                            if key not in fields or not fields.get(key):
                                added_fields.append(key)

                        if added_fields:
                            print(
                                f"Enhanced with fields: {', '.join(added_fields)}")
                            fields.update(enhanced_fields)
                        else:
                            print(f"No additional fields found via API")
                    except Exception as e:
                        print(f"API enhancement failed: {e}")
                        # Continue with existing fields if API fails
                else:
                    print(f"Reference appears complete, skipping API enhancement")

            return fields
        except Exception as e:
            print(f"Error extracting fields: {e}")
            print(traceback.format_exc())
            return {}

    def _describe_xml_structure(self, element, depth=0, max_depth=3):
        """Return a string describing the structure of the XML element."""
        if depth > max_depth:
            return "..."
        result = f"{element.tag}"
        if element.attrib:
            attribs = ", ".join(
                [f"{k}='{v}'" for k, v in element.attrib.items()])
            result += f"[{attribs}]"
        children = list(element)
        if children:
            result += " { "
            result += ", ".join([self._describe_xml_structure(child, depth+1, max_depth)
                                 for child in children[:5]])
            if len(children) > 5:
                result += f", ... ({len(children)-5} more)"
            result += " }"
        elif element.text and element.text.strip():
            text = element.text.strip()
            if len(text) > 30:
                text = text[:27] + "..."
            result += f": '{text}'"
        return result

    def _get_required_fields(self, entry_type):
        """Get required fields for a specific entry type"""
        # Handle unknown entry types gracefully
        required_fields = {
            "article": ["author", "title", "journal", "year"],
            # Allow books without explicit author
            "book": ["title", "publisher", "year"],
            "inbook": ["title", "publisher", "year"],
            "incollection": ["author", "title", "booktitle", "year"],
            "inproceedings": ["author", "title", "booktitle", "year"],
            "proceedings": ["title", "year"],
            "phdthesis": ["author", "title", "school", "year"],
            "mastersthesis": ["author", "title", "school", "year"],
            "techreport": ["author", "title", "institution", "year"],
            # URL is recommended but not strictly required
            "online": ["title"],
            "misc": [],  # No required fields
            "patent": ["author", "title", "number", "year"],
            "unpublished": ["author", "title", "note"]
        }

        # Return empty list if entry type is not recognized - don't enforce requirements on unknown types
        return required_fields.get(entry_type, [])

    def _extract_text_from_styled_element(self, element):
        """Extract text from styled elements with improved error handling."""
        if element is None:
            return ""

        # Get direct text if available
        text = element.text or ""

        # Try to extract from style elements if present
        if self.extract_styled_text:
            style_elements = element.findall('.//style')
            if style_elements:
                styled_text = "".join([(style.text or "")
                                      for style in style_elements])
                if styled_text.strip():
                    text = styled_text

        return text

    def _format_fields(self, fields, required_fields=[]):
        """Format fields into BibTeX format with empty strings for missing fields."""
        formatted_fields = ""
        missing_fields = []

        # Process required fields first
        for field in required_fields:
            field_value = fields.get(field)
            if field_value is not None:
                formatted_fields += f"\n  {field} = {{{field_value}}},"
            else:
                # Empty string for missing required field
                formatted_fields += f'\n  {field} = "",'
                missing_fields.append(field)

        # Process all other fields
        optional_fields = ["address", "editor", "volume", "number", "series",
                           "month", "note", "publisher", "edition", "isbn", "doi", "url"]

        # Add existing fields that weren't required
        for field, field_value in fields.items():
            if field not in required_fields:
                formatted_fields += f"\n  {field} = {{{field_value}}},"
                # Remove from optional fields list since we've added it
                if field in optional_fields:
                    optional_fields.remove(field)

        # Add empty strings for missing optional fields
        for field in optional_fields:
            formatted_fields += f'\n  {field} = "",'

        if missing_fields and not self.suppress_warnings:
            title = fields.get('title', '')
            print(
                f"Warning: Missing required field(s) for BibTeX entry '{title}': {missing_fields}")

        return formatted_fields

    def _format_fields_acm_style(self, fields, required_fields, entry_type):
        """Format fields in ACM style using string definitions where appropriate."""
        formatted_fields = ""
        missing_fields = []

        # Process fields in a specific order for consistency
        field_order = ['author', 'title', 'journal', 'booktitle', 'publisher',
                       'volume', 'number', 'series', 'edition', 'year', 'month',
                       'pages', 'articleno', 'numpages', 'doi', 'url', 'address']

        # Add required fields first
        for field in field_order:
            if field in fields:
                # Special handling for journal names that should use string definitions
                if field == 'journal' and self.use_string_definitions:
                    journal_name = fields['journal']
                    journal_key = self._find_journal_key(journal_name)

                    # Use string reference if found, otherwise use the full text
                    if journal_key:
                        formatted_fields += f"\n  journal = {journal_key},"
                    else:
                        formatted_fields += f"\n  journal = {{{journal_name}}},"

                # Special handling for publishers that should use string definitions
                elif field == 'publisher' and self.use_string_definitions:
                    publisher_name = fields['publisher']
                    publisher_key = self._find_publisher_key(publisher_name)

                    # Use string reference if found, otherwise use the full text
                    if publisher_key:
                        formatted_fields += f"\n  publisher = {publisher_key},"
                    else:
                        formatted_fields += f"\n  publisher = {{{publisher_name}}},"

                # Special handling for month field
                elif field == 'month':
                    month_text = fields['month'].lower()
                    month_abbrev = {
                        'january': 'jan', 'february': 'feb', 'march': 'mar',
                        'april': 'apr', 'may': 'may', 'june': 'jun',
                        'july': 'jul', 'august': 'aug', 'september': 'sep',
                        'october': 'oct', 'november': 'nov', 'december': 'dec'
                    }

                    # Find the month abbreviation if possible
                    for full_month, abbrev in month_abbrev.items():
                        if full_month in month_text:
                            formatted_fields += f"\n  month = {abbrev},"
                            break
                    else:
                        formatted_fields += f"\n  month = {{{month_text}}},"

                # Special handling for pages - calculate numpages if needed
                elif field == 'pages':
                    pages_text = fields['pages']
                    formatted_fields += f"\n  pages = {{{pages_text}}},"

                    if '--' in pages_text or '-' in pages_text:
                        # Try to calculate numpages for page ranges
                        try:
                            separator = '--' if '--' in pages_text else '-'
                            start, end = pages_text.split(separator)
                            start = int(start.strip())
                            end = int(end.strip())
                            numpages = end - start + 1
                            formatted_fields += f"\n  numpages = {{{numpages}}},"
                        except ValueError:
                            # If we can't parse as integers, just continue
                            pass
                    else:
                        # Handle single page as article number
                        formatted_fields += f"\n  articleno = {{{pages_text}}},"
                        formatted_fields += f"\n  numpages = {{1}},"

                # Standard handling for other fields
                else:
                    formatted_fields += f"\n  {field} = {{{fields[field]}}},"

            # Check if a required field is missing
            elif field in required_fields:
                missing_fields.append(field)

        # Add any remaining fields not in our ordered list
        for field, value in fields.items():
            if field not in field_order:
                formatted_fields += f"\n  {field} = {{{value}}},"

        # Log missing required fields if warnings are enabled
        if missing_fields and not self.suppress_warnings:
            title = fields.get('title', '')
            print(
                f"Warning: Missing required field(s) for BibTeX entry '{title}': {missing_fields}")

        return formatted_fields

    def _collect_journal_info(self, record):
        """Collect journal information for generating BibTeX string definitions."""
        secondary_title = record.find('.//titles/secondary-title')
        if secondary_title is not None:
            journal_text = self._extract_text_from_styled_element(
                secondary_title)
            if journal_text and journal_text.strip():
                journal_name = journal_text.strip()

                # Generate an appropriate key for this journal
                journal_key = self._generate_acm_journal_key(journal_name)

                # Store full name and categorize journal
                if journal_key not in self.journals:
                    category = self._determine_journal_category(journal_name)
                    self.journals[journal_key] = {
                        'full_name': journal_name,
                        'abbreviated': '',
                        'category': category
                    }
                    self.journal_name_to_key[journal_name] = journal_key

                # If the journal name looks like an abbreviation, store it as such
                if "." in journal_name or all(len(word) <= 4 for word in journal_name.split()):
                    existing_key = self.journal_name_to_key.get(
                        journal_name, journal_key)
                    if existing_key in self.journals and not self.journals[existing_key]['abbreviated']:
                        self.journals[existing_key]['abbreviated'] = journal_name

    def _collect_publisher_info(self, record):
        """Collect publisher information for generating BibTeX string definitions."""
        publisher_elem = record.find('.//publisher')
        if publisher_elem is not None:
            publisher_text = self._extract_text_from_styled_element(
                publisher_elem)
            if publisher_text and publisher_text.strip():
                publisher_name = publisher_text.strip()

                # Generate a key for this publisher
                publisher_key = self._generate_acm_publisher_key(
                    publisher_name)

                # Store the publisher info
                if publisher_key not in self.publishers:
                    self.publishers[publisher_key] = {
                        'name': publisher_name,
                        'category': self._determine_publisher_category(publisher_name)
                    }

    def _find_journal_key(self, journal_name):
        """Find the key for a journal name in our collected journals."""
        for key, info in self.journals.items():
            if (info.get('full_name') == journal_name or
                    info.get('abbreviated') == journal_name):
                return key
        return None

    def _find_publisher_key(self, publisher_name):
        """Find the key for a publisher name in our collected publishers."""
        for key, info in self.publishers.items():
            if info.get('name') == publisher_name:
                return key
        return None

    def _generate_acm_journal_key(self, journal_name):
        """Generate an ACM-style journal key."""
        # Remove common words and create acronym
        words = journal_name.replace('&', 'and').split()
        key_words = []

        for word in words:
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word and clean_word.lower() not in {'of', 'on', 'in', 'for', 'and', 'the', 'a', 'an'}:
                key_words.append(clean_word)

        if key_words:
            return 'J' + ''.join(word[:3].upper() for word in key_words[:3])
        else:
            return 'JGEN'

    def _generate_acm_publisher_key(self, publisher_name):
        """Generate an ACM-style publisher key."""
        # Remove common words and create acronym
        words = publisher_name.replace('&', 'and').split()
        key_words = []

        for word in words:
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word and clean_word.lower() not in {'of', 'on', 'in', 'for', 'and', 'the', 'a', 'an', 'inc', 'llc', 'ltd'}:
                key_words.append(clean_word)

        if key_words:
            return 'P' + ''.join(word[:3].upper() for word in key_words[:2])
        else:
            return 'PGEN'

    def _determine_journal_category(self, journal_name):
        """Determine the category of a journal based on its name."""
        name_lower = journal_name.lower()

        if any(word in name_lower for word in ['computer', 'computing', 'software', 'programming']):
            return 'Computer Science'
        elif any(word in name_lower for word in ['engineering', 'technical', 'ieee']):
            return 'Engineering'
        elif any(word in name_lower for word in ['science', 'research', 'nature']):
            return 'Science'
        else:
            return 'General'

    def _determine_publisher_category(self, publisher_name):
        """Determine the category of a publisher based on its name."""
        name_lower = publisher_name.lower()

        if any(word in name_lower for word in ['ieee', 'acm', 'springer', 'elsevier']):
            return 'Academic'
        elif any(word in name_lower for word in ['press', 'university']):
            return 'University Press'
        else:
            return 'Commercial'

    def _generate_string_definitions(self):
        """Generate BibTeX string definitions for journals and publishers."""
        definitions = []

        # Generate journal string definitions
        for key, info in self.journals.items():
            if info['full_name']:
                definitions.append(f'@String{{{key} = "{info["full_name"]}}}')

        # Generate publisher string definitions
        for key, info in self.publishers.items():
            if info['name']:
                definitions.append(f'@String{{{key} = "{info["name"]}}}')

        return '\n'.join(definitions)

    def _remove_duplicates_and_fix_keys(self, bibtex_entries):
        """Remove duplicate entries and ensure unique BibTeX keys."""
        unique_entries = {
        }  # Dictionary to store unique entries: key -> (entry_text, fingerprint, score)
        key_counts = {}  # Track how many times each base key has been used

        for entry in bibtex_entries:
            # Extract the current key and content
            key, content = self._parse_bibtex_entry(entry)
            if not key or not content:
                continue

            # Generate a content fingerprint for duplicate detection
            fingerprint = self._generate_content_fingerprint(content)

            # Check if this is a duplicate based on content similarity
            duplicate_key = None
            for existing_key, (existing_entry, existing_fingerprint, existing_score) in unique_entries.items():
                if self._are_entries_similar(fingerprint, existing_fingerprint):
                    duplicate_key = existing_key
                    break

            # Score this entry (higher score = better quality)
            entry_score = self._score_entry_quality(content)

            if duplicate_key:
                # This is a duplicate - keep the better one
                existing_score = unique_entries[duplicate_key][2]
                if entry_score > existing_score:
                    unique_entries[duplicate_key] = (
                        entry, fingerprint, entry_score)
                    print(
                        f"Replacing duplicate entry {duplicate_key} with better version")
                else:
                    print(f"Skipping duplicate entry for {key}")
                continue

            # Ensure unique key
            base_key = self._extract_base_key(key)
            unique_key = self._generate_unique_key(base_key, key_counts)
            key_counts[base_key] = key_counts.get(base_key, 0) + 1

            # Replace the key in the entry if needed
            if unique_key != key:
                entry = entry.replace(
                    f"@{self._extract_entry_type(entry)}{{{key},",
                    f"@{self._extract_entry_type(entry)}{{{unique_key},", 1)
                print(f"Renamed key from {key} to {unique_key}")

            unique_entries[unique_key] = (entry, fingerprint, entry_score)

        # Return the deduplicated entries
        return [entry_data[0] for entry_data in unique_entries.values()]

    def _parse_bibtex_entry(self, entry):
        """Parse a BibTeX entry to extract key and content."""
        import re
        match = re.match(r'@(\w+)\{([^,]+),\s*\n(.*)\n\}', entry, re.DOTALL)
        if match:
            entry_type, key, content = match.groups()
            return key.strip(), content.strip()
        else:
            return None, None

    def _extract_entry_type(self, entry):
        """Extract the entry type from a BibTeX entry."""
        import re
        match = re.match(r'@(\w+)\{', entry)
        return match.group(1) if match else "misc"

    def _extract_base_key(self, key):
        """Extract base key without numeric suffixes."""
        import re
        base_match = re.match(r'([a-zA-Z]+)(\d*)', key)
        return base_match.group(1) if base_match else key

    def _generate_unique_key(self, base_key, key_counts):
        """Generate a unique key by adding numeric suffix if needed."""
        count = key_counts.get(base_key, 0)
        if count == 0:
            return base_key
        else:
            return f"{base_key}{count + 1}"

    def _generate_content_fingerprint(self, content):
        """Generate a fingerprint for entry content to detect duplicates."""
        import re
        # Extract key fields for comparison
        title_match = re.search(
            r'title\s*=\s*[{"]([^"}]+)["}]', content, re.IGNORECASE)
        author_match = re.search(
            r'author\s*=\s*[{"]([^"}]+)["}]', content, re.IGNORECASE)
        year_match = re.search(
            r'year\s*=\s*[{"]?(\d{4})["}]?', content, re.IGNORECASE)

        title = title_match.group(1).lower().strip() if title_match else ""
        author = author_match.group(1).lower().strip() if author_match else ""
        year = year_match.group(1) if year_match else ""

        # Normalize title and author for comparison
        title = re.sub(r'[^\w\s]', '', title)  # Remove punctuation
        title = re.sub(r'\s+', ' ', title)     # Normalize whitespace
        author = re.sub(r'[^\w\s]', '', author)  # Remove punctuation
        author = re.sub(r'\s+', ' ', author)     # Normalize whitespace

        return {
            'title': title,
            'author': author,
            'year': year
        }

    def _are_entries_similar(self, fingerprint1, fingerprint2):
        """Check if two entries are similar enough to be considered duplicates."""
        title1, title2 = fingerprint1['title'], fingerprint2['title']
        author1, author2 = fingerprint1['author'], fingerprint2['author']
        year1, year2 = fingerprint1['year'], fingerprint2['year']

        # If any key field is missing, be more conservative
        if not title1 or not title2:
            return False

        # Calculate title similarity (simple approach)
        title_similarity = self._calculate_text_similarity(title1, title2)

        # Check author similarity (more lenient due to formatting variations)
        author_similarity = self._calculate_text_similarity(
            author1, author2) if author1 and author2 else 1.0

        # Year must match exactly if both present
        year_match = (year1 == year2) if (year1 and year2) else True

        # Consider it a duplicate if title similarity is high and year matches
        return (title_similarity > 0.85 and year_match and
                (not author1 or not author2 or author_similarity > 0.7))

    def _calculate_text_similarity(self, text1, text2):
        """Calculate similarity between two text strings (0-1)."""
        if not text1 or not text2:
            return 0.0

        # Simple similarity based on common words
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        return intersection / union if union > 0 else 0.0

    def _score_entry_quality(self, content):
        """Score the quality of a BibTeX entry (higher = better)."""
        import re
        score = 0

        # Count number of fields present
        field_pattern = r'(\w+)\s*=\s*[{"][^"}]+["}]'
        fields = re.findall(field_pattern, content, re.IGNORECASE)
        score += len(fields) * 2  # More fields = better

        # Bonus for important fields
        important_fields = ['title', 'author', 'year',
                            'journal', 'booktitle', 'doi', 'pages']
        for field in important_fields:
            if re.search(rf'{field}\s*=', content, re.IGNORECASE):
                score += 5

        # Bonus for DOI presence (indicates higher quality metadata)
        if re.search(r'doi\s*=', content, re.IGNORECASE):
            score += 10

        # Bonus for complete page numbers
        if re.search(r'pages\s*=\s*[{"][\d-]+["}]', content, re.IGNORECASE):
            score += 3

        # Penalty for missing critical fields
        if not re.search(r'title\s*=', content, re.IGNORECASE):
            score -= 20
        if not re.search(r'author\s*=', content, re.IGNORECASE):
            score -= 15
        if not re.search(r'year\s*=', content, re.IGNORECASE):
            score -= 10

        return score

    def set_api_enhancement(self, enabled):
        """Enable or disable API enhancement."""
        self.enable_api_enhancement = enabled and API_AVAILABLE

    def get_api_status(self):
        """Get the status of API availability."""
        return {
            'available': API_AVAILABLE,
            'manager_loaded': self.api_manager is not None,
            'enhancement_enabled': self.enable_api_enhancement
        }

    def set_progress_callback(self, callback):
        """Set a callback function for progress updates."""
        self.progress_callback = callback

    def _call_progress_callback(self, current, total, message=""):
        """Call the progress callback if it exists."""
        if self.progress_callback:
            return self.progress_callback(current, total, message)
        return True  # Continue processing if no callback
