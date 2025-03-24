import xml.etree.ElementTree as ET
import traceback

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
    
    def convert_to_bibtex(self, xml_data):
        # Reset errors list
        self.conversion_errors = []
        
        if isinstance(xml_data, str):
            # Parse the XML data string into an ElementTree element
            try:
                xml_root = ET.fromstring(xml_data)
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

        # Now xml_root is the root element of the XML data
        bibtex_entries = []
        
        # Check for EndNote XML format
        records_path = './/record'
        if xml_root.find('.//records/record') is not None:
            records_path = './/records/record'
        
        records = xml_root.findall(records_path)
        if not records:
            self.conversion_errors.append("No records found in XML data")
            return ""
            
        for index, record in enumerate(records):
            try:
                # Get entry type from ref-type element or attribute
                ref_type_elem = record.find('.//ref-type')
                if ref_type_elem is not None and 'name' in ref_type_elem.attrib:
                    entry_type_name = ref_type_elem.attrib['name']
                else:
                    entry_type_name = record.attrib.get('ref-type', 'Generic')
                
                # Map to standard BibTeX type
                entry_type = self.entry_type_map.get(entry_type_name, 'misc')
                
                # Generate a unique key for the entry
                key_elem = record.find('.//rec-number')
                entry_key = key_elem.text if key_elem is not None and key_elem.text else f"ref{len(bibtex_entries) + 1}"
                
                # Start building the BibTeX entry
                bibtex_entry = f"@{entry_type}{{{entry_key}"
                
                # Extract and organize fields from XML
                fields = self._extract_fields_from_xml(record)
                
                # Get required fields for this entry type
                required_fields = self._get_required_fields(entry_type)
                
                # Format fields according to BibTeX standards
                formatted_fields = self._format_fields(fields, required_fields)
                
                # Complete the BibTeX entry
                bibtex_entry += formatted_fields + "\n}"
                bibtex_entries.append(bibtex_entry)
            except Exception as e:
                error_msg = f"Error processing record {index + 1}: {str(e)}"
                if not self.suppress_warnings:
                    print(error_msg)
                self.conversion_errors.append(error_msg)
                # Continue with next record instead of failing entirely

        if not bibtex_entries and self.conversion_errors:
            print(f"Conversion failed with {len(self.conversion_errors)} errors")
            return ""
            
        return '\n\n'.join(bibtex_entries)
    
    def _extract_text_from_styled_element(self, element):
        """Extract text from a styled element, considering EndNote XML format."""
        if element is None:
            return ""
        
        # Check if this is a styled text element (EndNote specific)
        if self.extract_styled_text and element.find('.//style') is not None:
            # Combine text from all style elements
            return "".join([style.text if style.text else "" for style in element.findall('.//style')])
        
        # Regular text element
        return element.text if element.text else ""
    
    def _extract_fields_from_xml(self, record):
        """Extract fields from XML record with special handling for EndNote format."""
        try:
            fields = {}
            
            # Process title
            title_elem = record.find('.//titles/title')
            if title_elem is not None:
                title_text = self._extract_text_from_styled_element(title_elem)
                if title_text:
                    fields['title'] = title_text.strip()
            
            # Process authors
            authors_elem = record.find('.//contributors/authors')
            if authors_elem is not None:
                author_names = []
                for author in authors_elem.findall('.//author'):
                    author_text = self._extract_text_from_styled_element(author)
                    if author_text:
                        author_names.append(author_text.strip())
                if author_names:
                    fields['author'] = ' and '.join(author_names)
            
            # Process year
            year_elem = record.find('.//dates/year')
            if year_elem is not None:
                year_text = self._extract_text_from_styled_element(year_elem)
                if year_text:
                    fields['year'] = year_text.strip()
            
            # Process journal/booktitle
            secondary_title = record.find('.//titles/secondary-title')
            if secondary_title is not None:
                secondary_text = self._extract_text_from_styled_element(secondary_title)
                if secondary_text:
                    # Determine if this is a journal or book title based on entry type
                    ref_type_elem = record.find('.//ref-type')
                    if ref_type_elem is not None and 'name' in ref_type_elem.attrib:
                        if ref_type_elem.attrib['name'] == 'Journal Article':
                            fields['journal'] = secondary_text.strip()
                        else:
                            fields['booktitle'] = secondary_text.strip()
            
            # Process volume and issue
            volume_elem = record.find('.//volume')
            if volume_elem is not None:
                volume_text = self._extract_text_from_styled_element(volume_elem)
                if volume_text:
                    fields['volume'] = volume_text.strip()
            
            number_elem = record.find('.//number')
            if number_elem is not None:
                number_text = self._extract_text_from_styled_element(number_elem)
                if number_text:
                    fields['number'] = number_text.strip()
            
            # Process pages
            pages_elem = record.find('.//pages')
            if pages_elem is not None:
                pages_text = self._extract_text_from_styled_element(pages_elem)
                if pages_text:
                    fields['pages'] = pages_text.strip()
            
            # Process publisher/institution
            publisher_elem = record.find('.//publisher')
            if publisher_elem is not None:
                publisher_text = self._extract_text_from_styled_element(publisher_elem)
                if publisher_text:
                    fields['publisher'] = publisher_text.strip()
            
            # Process URL
            url_elem = record.find('.//urls/related-urls/url')
            if url_elem is not None:
                url_text = self._extract_text_from_styled_element(url_elem)
                if url_text:
                    fields['url'] = url_text.strip()
            
            # Process DOI
            doi_elem = record.find('.//electronic-resource-num')
            if doi_elem is not None:
                doi_text = self._extract_text_from_styled_element(doi_elem)
                if doi_text:
                    fields['doi'] = doi_text.strip()
            
            # Process abstract
            abstract_elem = record.find('.//abstract')
            if abstract_elem is not None:
                abstract_text = self._extract_text_from_styled_element(abstract_elem)
                if abstract_text:
                    fields['abstract'] = abstract_text.strip()
            
            # Process keywords
            keywords_elem = record.findall('.//keywords/keyword')
            if keywords_elem:
                keywords = []
                for kw in keywords_elem:
                    kw_text = self._extract_text_from_styled_element(kw)
                    if kw_text:
                        keywords.append(kw_text.strip())
                if keywords:
                    fields['keywords'] = ', '.join(keywords)
            
            # Process ISBN
            isbn_elem = record.find('.//isbn')
            if isbn_elem is not None:
                isbn_text = self._extract_text_from_styled_element(isbn_elem)
                if isbn_text:
                    fields['isbn'] = isbn_text.strip()
            
            # Add other basic elements that are direct children and commonly used
            for tag in ['edition', 'address', 'note', 'month', 'series', 'chapter']:
                elem = record.find(f'.//{tag}')
                if elem is not None:
                    elem_text = self._extract_text_from_styled_element(elem)
                    if elem_text:
                        fields[tag] = elem_text.strip()
            
            return fields
        except Exception as e:
            error_msg = f"Error extracting fields: {str(e)}"
            self.conversion_errors.append(error_msg)
            if not self.suppress_warnings:
                print(error_msg)
            return {}  # Return empty dict on error

    def _get_required_fields(self, entry_type):
        required_fields = {
            "article": ["author", "title", "journal", "year"],
            "book": ["author", "title", "publisher", "year"],
            "inbook": ["author", "title", "publisher", "year"],
            "incollection": ["author", "title", "booktitle", "publisher", "year"],
            "inproceedings": ["author", "title", "booktitle", "year"],
            "proceedings": ["title", "year"],
            "phdthesis": ["author", "title", "school", "year"],
            "mastersthesis": ["author", "title", "school", "year"],
            "techreport": ["author", "title", "institution", "year"],
            "online": ["title", "url"],
            "misc": ["title"],
            "patent": ["author", "title", "number", "year"],
            "unpublished": ["author", "title", "note"]
        }

        return required_fields.get(entry_type, [])

    def _format_fields(self, fields, required_fields=[]):
        formatted_fields = ""
        missing_fields = []

        # Add required fields first
        for field in required_fields:
            field_value = fields.get(field)
            if field_value is not None:
                formatted_fields += f"\n\t{field} = {{{field_value}}},"
            else:
                missing_fields.append(field)

        # Add flexible fields (that aren't already added)
        for field, field_value in fields.items():
            if field not in required_fields:
                formatted_fields += f"\n\t{field} = {{{field_value}}},"

        # Report missing required fields if warnings are not suppressed
        if missing_fields and not self.suppress_warnings:
            title = fields.get('title', '')
            print(f"Warning: Missing required field(s) for BibTeX entry '{title}': {missing_fields}")

        return formatted_fields
