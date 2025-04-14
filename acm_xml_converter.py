import xml.etree.ElementTree as ET
import traceback
import re
from datetime import datetime
import collections


class XML:
    def __init__(self):
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

        # LaTeX special characters that need escaping
        self.latex_special_chars = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
            '\\': r'\textbackslash{}',
            '<': r'\textless{}',
            '>': r'\textgreater{}'
        }

        # BibTeX to BibLaTeX field name mapping
        self.biblatex_field_map = {
            'journal': 'journaltitle',
            'address': 'location',
            'school': 'institution',
            'articleno': 'number',  # Map articleno to number in BibLaTeX
        }

        # Track journals and publishers for string definitions
        self.journals = {}  # Format: {journal_key: {full_name: "", abbreviated: "", category: ""}}
        self.publishers = {}  # Format: {publisher_key: {name: "", category: ""}}

        # Keep track of journal names to keys for duplicate detection
        self.journal_name_to_key = {}  # {name: key} mapping to avoid duplicates

        # Enhanced categories for grouping with more comprehensive lists
        self.journal_categories = {
            'ACM': ['ACM', 'Association for Computing Machinery', 'CACM', 'Communications of the ACM', 'Commun. ACM',
                    'Trans. ACM', 'Transactions on', 'SIGPLAN', 'SIGCHI', 'SIGGRAPH', 'SIGSOFT', 'SIGIR', 'SIGKDD', 'SIGMOD'],
            'IEEE': ['IEEE', 'Institute of Electrical and Electronics Engineers', 'Transactions on', 'Journal of',
                     'Proceedings of the IEEE', 'Computer Society'],
            'SIAM': ['SIAM', 'Society for Industrial and Applied Mathematics', 'Journal on', 'Review'],
            'AMS': ['AMS', 'American Mathematical Society', 'Mathematical'],
            'Springer': ['Springer', 'Lecture Notes in Computer Science', 'LNCS', 'Lecture Notes in'],
            'Elsevier': ['Elsevier', 'Science Direct', 'Information Sciences', 'Computer Science'],
            'Conference': ['Proceedings of', 'Conference on', 'Symposium on', 'Workshop on']
        }

        # Publisher categories for grouping
        self.publisher_categories = {
            'Academic': ['Academic', 'Academic Press', 'University'],
            'ACM': ['ACM', 'Association for Computing Machinery'],
            'IEEE': ['IEEE', 'Institute of Electrical and Electronics Engineers'],
            'Commercial': ['Wiley', 'Springer', 'Elsevier', 'McGraw', 'Addison', 'Wesley']
        }

        # Pattern matchers for intelligent categorization
        self.journal_patterns = {
            'Conference': [r'proc\.?\s+of', r'proceedings', r'conference', r'symposium', r'workshop'],
            'Journal': [r'journal', r'transactions', r'quarterly', r'review', r'letters'],
            'Magazine': [r'magazine', r'bulletin', r'forum', r'digest'],
        }

    def escape_latex(self, text):
        """Escape LaTeX special characters in text."""
        if not self.escape_latex_chars or not text:
            return text

        for char, replacement in self.latex_special_chars.items():
            text = text.replace(char, replacement)
        return text

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

        # Generate output with string definitions if applicable
        if self.use_string_definitions:
            string_definitions = self._generate_string_definitions()
            if string_definitions:
                print(
                    f"Generated {string_definitions.count('@String')} string definitions")
                return string_definitions + '\n\n' + '\n\n'.join(bibtex_entries)

        # Default return if no string definitions
        return '\n\n'.join(bibtex_entries)

    def _extract_fields_from_xml(self, record):
        """Extract fields from the XML record with better error handling."""
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

            # Extract years
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

            # Add additional fields as needed for a complete BibTeX entry
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
            result += ", ".join([self._describe_xml_structure(child,
                                                              depth+1, max_depth) for child in children[:5]])
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

        # Standard required fields that should always be included
        all_std_fields = ["author", "title", "journal", "booktitle", "year",
                          "volume", "number", "pages", "publisher", "address",
                          "editor", "doi", "url", "month", "note"]

        # Process required fields first
        for field in required_fields:
            field_value = fields.get(field)
            if field_value is not None:
                formatted_fields += f"\n  {field} = {{{field_value}}},"
            else:
                # Empty string for missing required field
                formatted_fields += f'\n  {field} = "",'
                missing_fields.append(field)

        # Process other standard fields - include them all with empty strings if missing
        for field in all_std_fields:
            if field not in required_fields:  # Skip if already processed as required
                if field in fields:
                    formatted_fields += f"\n  {field} = {{{fields[field]}}},"
                else:
                    formatted_fields += f'\n  {field} = "",'

        # Process any remaining fields that are non-standard
        for field, value in fields.items():
            if field not in required_fields and field not in all_std_fields:
                formatted_fields += f"\n  {field} = {{{value}}},"

        # Log warning for missing required fields
        if missing_fields and not self.suppress_warnings:
            title = fields.get('title', '')
            print(
                f"Warning: Missing required field(s) for BibTeX entry '{title}': {missing_fields}")

        return formatted_fields

    def _format_fields_acm_style(self, fields, required_fields, entry_type):
        """Format fields in ACM style using string definitions where appropriate."""
        formatted_fields = ""
        missing_fields = []

        # Standard fields in ACM order
        acm_field_order = ['author', 'title', 'journal', 'booktitle', 'publisher',
                           'volume', 'number', 'series', 'edition', 'year', 'month',
                           'pages', 'articleno', 'numpages', 'doi', 'url', 'address',
                           'editor', 'organization', 'note']

        # Process fields in specific order
        for field in acm_field_order:
            # Field exists in entry
            if field in fields:
                # Special handling for journal with string definitions
                if field == 'journal' and self.use_string_definitions:
                    journal_name = fields['journal']
                    journal_key = None

                    # Try to find this journal in our collection
                    for j_key, j_info in self.journals.items():
                        if j_info['full_name'] == journal_name:
                            journal_key = j_key
                            break

                    # Use string reference if found, otherwise use full name
                    if journal_key:
                        formatted_fields += f"\n  journal = {journal_key},"
                    else:
                        formatted_fields += f"\n  journal = {{{journal_name}}},"

                # Special handling for publisher with string definitions
                elif field == 'publisher' and self.use_string_definitions:
                    publisher_name = fields['publisher']
                    publisher_key = None

                    # Try to find this publisher in our collection
                    for p_key, p_info in self.publishers.items():
                        if p_info['name'] == publisher_name:
                            publisher_key = p_key
                            break

                    # Use string reference if found, otherwise use full name
                    if publisher_key:
                        formatted_fields += f"\n  publisher = {publisher_key},"
                    else:
                        formatted_fields += f"\n  publisher = {{{publisher_name}}},"

                # Special handling for booktitle with string definitions
                elif field == 'booktitle' and self.use_string_definitions:
                    booktitle_text = fields['booktitle']
                    booktitle_key = None

                    # Try to find this booktitle in our collection
                    for j_key, j_info in self.journals.items():
                        if j_info['full_name'] == booktitle_text:
                            booktitle_key = j_key
                            break

                    # Use string reference if found, otherwise use full name
                    if booktitle_key:
                        formatted_fields += f"\n  booktitle = {booktitle_key},"
                    else:
                        formatted_fields += f"\n  booktitle = {{{booktitle_text}}},"

                # Handle other fields normally
                else:
                    formatted_fields += f"\n  {field} = {{{fields[field]}}},"

            # Field doesn't exist but is required
            elif field in required_fields:
                # Empty string for missing field
                formatted_fields += f'\n  {field} = "",'
                missing_fields.append(field)

            # Field doesn't exist and isn't required, but should be included as empty
            else:
                # Include all standard fields
                formatted_fields += f'\n  {field} = "",'

        # Add any extra fields not in our standard order
        for field, value in fields.items():
            if field not in acm_field_order:
                formatted_fields += f"\n  {field} = {{{value}}},"

        return formatted_fields

    def _collect_journal_info(self, record):
        """Collect journal information for generating BibTeX string definitions."""
        # Get journal information from secondary title (most common location)
        secondary_title = record.find('.//titles/secondary-title')
        if secondary_title is not None:
            journal_text = self._extract_text_from_styled_element(
                secondary_title)
            if journal_text and journal_text.strip():
                journal_name = journal_text.strip()
                # Generate an appropriate key for this journal, removing special characters
                journal_key = self._generate_acm_journal_key(journal_name)

                # Store full name and categorize journal
                if journal_key not in self.journals and len(journal_name) > 3:
                    category = self._determine_journal_category(journal_name)
                    self.journals[journal_key] = {
                        'full_name': journal_name,
                        'abbreviated': '',
                        'category': category
                    }
                    self.journal_name_to_key[journal_name] = journal_key

                    # Add debug output to see what's being collected
                    if self.debug_mode:
                        print(
                            f"Added journal: {journal_key} = '{journal_name}' (Category: {category})")

        # Also check for conference proceedings in the booktitle field
        booktitle_elem = record.find('.//titles/tertiary-title')
        if booktitle_elem is not None:
            booktitle_text = self._extract_text_from_styled_element(
                booktitle_elem)
            if booktitle_text and booktitle_text.strip():
                booktitle = booktitle_text.strip()
                # For conference proceedings, use a different key prefix
                booktitle_key = "Proc" + \
                    self._generate_acm_journal_key(booktitle)

                if booktitle_key not in self.journals and len(booktitle) > 3:
                    # Conference proceedings are usually categorized as Conference
                    self.journals[booktitle_key] = {
                        'full_name': booktitle,
                        'abbreviated': '',
                        'category': 'Conference'
                    }
                    self.journal_name_to_key[booktitle] = booktitle_key

                    if self.debug_mode:
                        print(
                            f"Added booktitle: {booktitle_key} = '{booktitle}' (Category: Conference)")

    def _collect_publisher_info(self, record):
        """Collect publisher information for generating BibTeX string definitions."""
        publisher_elem = record.find('.//publisher')
        if publisher_elem is not None:
            publisher_text = self._extract_text_from_styled_element(
                publisher_elem)
            if publisher_text and publisher_text.strip():
                publisher_name = publisher_text.strip()

                # Only process publishers with substantial names
                if len(publisher_name) > 3:
                    # Generate a key for this publisher
                    publisher_key = self._generate_acm_publisher_key(
                        publisher_name)

                    # Store publisher info if not already stored
                    if publisher_key not in self.publishers:
                        category = self._determine_publisher_category(
                            publisher_name)
                        self.publishers[publisher_key] = {
                            'name': publisher_name,
                            'category': category
                        }

                        if self.debug_mode:
                            print(
                                f"Added publisher: {publisher_key} = '{publisher_name}' (Category: {category})")

    def _determine_publisher_category(self, publisher_name=None, journal_name=None, isbn=None):
        """
        Determine the category of the publisher based on available information.
        """
        if publisher_name is None:
            return "unknown"

        publisher_lower = publisher_name.lower()

        # Check against common academic publishers
        academic_publishers = ["springer", "elsevier", "ieee", "acm", "wiley", "oxford",
                               "cambridge", "taylor & francis", "sage", "nature"]

        # Check publisher categories from our dictionary
        for category, keywords in self.publisher_categories.items():
            for keyword in keywords:
                if keyword.lower() in publisher_lower:
                    return category

        # Check for academic publishers
        for publisher in academic_publishers:
            if publisher in publisher_lower:
                return "Academic"

        # Check for universities/academic institutions
        if "university" in publisher_lower or "institute" in publisher_lower:
            return "Academic"

        # Check for society publishers
        if "society" in publisher_lower or "association" in publisher_lower:
            return "Society"

        # Default to commercial for unknown publishers
        return "Commercial"

    def _generate_string_definitions(self):
        """Generate BibTeX string definitions in ACM style with more complete coverage."""
        if not self.journals and not self.publishers:
            return ""

        output = ""

        # Add journals section if we have journals
        if self.journals:
            output += "% Journals\n\n"
            output += "% First the Full Name is given, then the abbreviation used in the AMS Math\n"
            output += "% Reviews, with an indication if it could not be found there.\n"
            output += "% Note the 2nd overwrites the 1st, so swap them if you want the full name.\n\n"

            # Group journals by category
            journal_categories = {}
            for j_key, j_info in self.journals.items():
                category = j_info.get('category', 'Other')
                if category not in journal_categories:
                    journal_categories[category] = []
                journal_categories[category].append((j_key, j_info))

            # Define category display order
            category_order = ['ACM', 'IEEE', 'Springer', 'Elsevier',
                              'Conference', 'Journal', 'Magazine', 'Other']

            # First display categories in our priority order
            for category in category_order:
                if category in journal_categories and journal_categories[category]:
                    output += f" %{{{category}}}\n"

                    # Sort journals by key within category
                    for j_key, j_info in sorted(journal_categories[category], key=lambda x: x[0]):
                        if j_info.get('full_name'):
                            output += f" @String{{{j_key} = \"{j_info['full_name']}\" }}\n"
                        # Add abbreviated version if available and different
                        if j_info.get('abbreviated') and j_info.get('abbreviated') != j_info.get('full_name'):
                            output += f" @String{{{j_key} = \"{j_info['abbreviated']}\" }}\n"

                    output += "\n"  # Add spacing between categories

            # Then add any remaining categories not in our priority list
            remaining_categories = set(
                journal_categories.keys()) - set(category_order)
            for category in sorted(remaining_categories):
                if journal_categories[category]:
                    output += f" %{{{category}}}\n"
                    for j_key, j_info in sorted(journal_categories[category], key=lambda x: x[0]):
                        if j_info.get('full_name'):
                            output += f" @String{{{j_key} = \"{j_info['full_name']}\" }}\n"
                        if j_info.get('abbreviated') and j_info.get('abbreviated') != j_info.get('full_name'):
                            output += f" @String{{{j_key} = \"{j_info['abbreviated']}\" }}\n"
                    output += "\n"

        # Add publishers section if we have publishers
        if self.publishers:
            output += "% Publishers % ================================================= |\n\n"

            # Group publishers by category
            publisher_categories = {}
            for p_key, p_info in self.publishers.items():
                category = p_info.get('category', 'Other')
                if category not in publisher_categories:
                    publisher_categories[category] = []
                publisher_categories[category].append((p_key, p_info))

            # Define publisher category display order
            pub_category_order = ['Academic', 'Society',
                                  'ACM', 'IEEE', 'Commercial', 'Other']

            # Display publishers by category
            for category in pub_category_order:
                if category in publisher_categories and publisher_categories[category]:
                    output += f" %{{{category}}}\n"
                    for p_key, p_info in sorted(publisher_categories[category], key=lambda x: x[0]):
                        output += f" @String{{{p_key} = \"{p_info['name']}\" }}\n"
                    output += "\n"

            # Add any remaining categories
            remaining_pub_cats = set(
                publisher_categories.keys()) - set(pub_category_order)
            for category in sorted(remaining_pub_cats):
                if publisher_categories[category]:
                    output += f" %{{{category}}}\n"
                    for p_key, p_info in sorted(publisher_categories[category], key=lambda x: x[0]):
                        output += f" @String{{{p_key} = \"{p_info['name']}\" }}\n"
                    output += "\n"

        return output
