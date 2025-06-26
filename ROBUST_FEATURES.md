# Robust Reference Converter - Enhancement Guide

## Overview

The Reference Converter has been enhanced with robust external API integration to ensure complete and accurate reference conversion, even when source XML files have missing fields.

## Key Features

### 1. External API Integration

**Supported APIs:**

- **Semantic Scholar**: Academic paper database with comprehensive metadata
- **CrossRef**: Academic publishing metadata service

**Automatic Enhancement:**

- Searches for missing DOIs, journal names, publication years, page numbers
- Fetches complete author information
- Retrieves abstracts and additional metadata
- Uses intelligent title and author matching with fuzzy string comparison

### 2. Robust Field Handling

**Smart Field Completion:**

- Attempts to fill missing required fields from external sources
- Preserves existing data while adding missing information
- Handles different reference types appropriately (articles, conference papers, books, etc.)

**Fallback Strategy:**

- Primary: Use existing XML data
- Secondary: Enhance with Semantic Scholar API
- Tertiary: Enhance with CrossRef API
- Final: Export with available fields only

### 3. Intelligent Processing

**Rate Limiting:**

- Respects API rate limits to avoid being blocked
- Implements delays between API calls
- Handles API failures gracefully

**Error Handling:**

- Continues processing even if APIs are unavailable
- Logs enhancement attempts and results
- Never fails conversion due to API issues

## Installation Requirements

### Basic Installation

```bash
pip install PyQt5
```

### Full Installation (with API enhancement)

```bash
pip install PyQt5 requests fuzzywuzzy python-Levenshtein
```

## Usage

### GUI Application

1. Launch the application: `python main.py`
2. Go to the conversion tab
3. Select your EndNote XML file
4. Enable "External API enhancement" if available
5. Click "Convert Now"

### Programmatic Usage

```python
from xml_converter import XML

# Initialize converter
converter = XML()

# Check API availability
api_status = converter.get_api_status()
print(f"API available: {api_status['available']}")

# Enable API enhancement
converter.set_api_enhancement(True)

# Convert XML to BibTeX
with open('references.xml', 'r') as f:
    xml_data = f.read()

bibtex_output = converter.convert_to_bibtex(xml_data)
```

## Configuration Options

### API Enhancement Settings

- **Enable/Disable**: Toggle external API calls
- **Rate Limiting**: Configurable delays between API calls
- **Field Priority**: Existing fields take precedence over API data

### Output Options

- **Suppress Warnings**: Hide missing field warnings
- **String Definitions**: Generate BibTeX string definitions for journals/publishers
- **ACM Style**: Format output in ACM conference style
- **BibLaTeX**: Use BibLaTeX field names instead of BibTeX

## API Enhancement Process

### For Each Reference:

1. **Extract Basic Info**: Title, authors, year from XML
2. **Check Completeness**: Identify missing critical fields
3. **Search Semantic Scholar**: Query with title + first author
4. **Match Results**: Use fuzzy string matching (>70% similarity)
5. **Extract Metadata**: Parse API response for missing fields
6. **Fallback to CrossRef**: If still missing important fields
7. **Merge Data**: Combine XML data with API enhancements
8. **Generate BibTeX**: Format complete reference

### Enhanced Fields:

- **DOI**: Digital Object Identifier
- **Journal/Venue**: Complete publication venue names
- **Publication Year**: Missing years from publication dates
- **Page Numbers**: Volume, issue, and page ranges
- **Authors**: Complete author names and affiliations
- **URLs**: Official paper links
- **Abstracts**: Paper abstracts when available

## Error Handling

### Common Scenarios:

- **API Unavailable**: Continues with existing XML data
- **No Matches Found**: Uses original XML fields
- **Rate Limiting**: Waits and retries with backoff
- **Network Issues**: Logs error and continues processing
- **Invalid Responses**: Validates data before use

### Logging:

- All API calls and responses are logged
- Enhancement success/failure tracked per reference
- Detailed error messages for troubleshooting

## Testing

Run the test script to verify functionality:

```bash
python test_robust_conversion.py
```

This will:

- Test conversion with and without API enhancement
- Show enhancement statistics
- Generate sample output
- Verify all components are working

## Best Practices

### For Complete References:

1. **Enable API Enhancement**: Always enable when available
2. **Clean Input Data**: Ensure XML has at least titles and some author info
3. **Check Output**: Review generated BibTeX for completeness
4. **Batch Processing**: Process large sets in smaller chunks

### For Performance:

1. **Rate Limiting**: Don't disable rate limiting
2. **Network**: Ensure stable internet connection
3. **Caching**: The system automatically avoids duplicate API calls

### For Quality:

1. **Review Output**: Check enhanced fields for accuracy
2. **Manual Verification**: Spot-check important references
3. **Field Priority**: Trust XML data over API when both exist

## Troubleshooting

### API Enhancement Not Working:

1. Check internet connection
2. Verify dependencies: `pip install requests fuzzywuzzy python-Levenshtein`
3. Check API status in application
4. Review logs for specific errors

### Poor Matching Results:

1. Ensure titles are complete and accurate in XML
2. Check author name formatting
3. Verify publication years are correct
4. Consider manual verification for critical references

### Performance Issues:

1. Increase rate limiting delay
2. Process smaller batches
3. Disable API enhancement for quick conversions
4. Check network stability

## Support

For issues or questions:

1. Check the conversion log for detailed error messages
2. Run the test script to verify installation
3. Review this documentation for configuration options
4. Check that all dependencies are installed correctly
