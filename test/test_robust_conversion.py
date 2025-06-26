#!/usr/bin/env python3
"""
Test script for the robust reference converter
Tests the conversion flow with and without external API enhancement
"""

import traceback
from xml_converter import XML
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_conversion():
    """Test the conversion process"""

    print("=" * 60)
    print("ROBUST REFERENCE CONVERTER TEST")
    print("=" * 60)

    # Initialize converter
    converter = XML()

    # Check API status
    api_status = converter.get_api_status()
    print(f"API Status:")
    print(f"  Available: {api_status['available']}")
    print(f"  Enabled: {api_status['enabled']}")
    print(f"  Manager Ready: {api_status['manager_ready']}")
    print()

    # Test with sample XML file
    xml_file = "meddef1.0.xml"
    if not os.path.exists(xml_file):
        print(f"Error: Test file {xml_file} not found!")
        return

    print(f"Testing conversion with {xml_file}")
    print()

    try:
        # Read XML file
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_data = f.read()

        print("Converting without API enhancement...")
        converter.set_api_enhancement(False)
        result_no_api = converter.convert_to_bibtex(xml_data)

        if result_no_api:
            print(
                f"✓ Conversion successful without API (length: {len(result_no_api)} chars)")

            # Count entries
            entry_count = result_no_api.count('@')
            print(f"  Generated {entry_count} BibTeX entries")
        else:
            print("✗ Conversion failed without API")
            return

        print()

        if api_status['available']:
            print("Converting with API enhancement...")
            converter.set_api_enhancement(True)
            result_with_api = converter.convert_to_bibtex(xml_data)

            if result_with_api:
                print(
                    f"✓ Conversion successful with API (length: {len(result_with_api)} chars)")

                # Count entries
                entry_count = result_with_api.count('@')
                print(f"  Generated {entry_count} BibTeX entries")

                # Compare results
                if len(result_with_api) > len(result_no_api):
                    print(
                        f"  API enhancement added {len(result_with_api) - len(result_no_api)} additional characters")
                else:
                    print(
                        "  No significant enhancement from API (data may already be complete)")
            else:
                print("✗ Conversion failed with API")
        else:
            print("Skipping API enhancement test (dependencies not available)")

        # Save sample output
        output_file = "test_output.bib"
        final_result = result_with_api if api_status['available'] else result_no_api

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_result)

        print(f"\nSample output saved to {output_file}")

        # Show first entry as preview
        lines = final_result.split('\n')
        preview_lines = []
        in_entry = False
        brace_count = 0

        for line in lines:
            if line.strip().startswith('@'):
                in_entry = True
                brace_count = 0

            if in_entry:
                preview_lines.append(line)
                brace_count += line.count('{') - line.count('}')

                if brace_count <= 0 and len(preview_lines) > 1:
                    break

        print("\nSample BibTeX entry:")
        print("-" * 40)
        for line in preview_lines[:15]:  # Show first 15 lines
            print(line)
        if len(preview_lines) > 15:
            print("...")
        print("-" * 40)

        print("\n✓ Robust conversion test completed successfully!")

    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        print(traceback.format_exc())


if __name__ == "__main__":
    test_conversion()
