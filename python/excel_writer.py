#!/usr/bin/env python3
"""
Append a row to an Excel file, creating it if it doesn't exist.
Makes job_link a clickable hyperlink.
Usage: python excel_writer.py <excel_file> <base64_json_row>
"""

import sys
import os
import json
import base64
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

# Column order for the Excel file
COLUMNS = [
    'status', 'needs_review', 'review_flags', 'title', 'company', 'location',
    'job_link', 'posted_date', 'score', 'seniority', 'industry', 'company_size',
    'role_summary', 'match_reasons', 'concerns', 'rejection_reason',
    'cover_letter', 'processed_at'
]

# Status colors
STATUS_COLORS = {
    'MATCH': '90EE90',      # Light green
    'REVIEW': 'FFD700',     # Gold/yellow
    'REJECTED': 'FFB6C1',   # Light pink
}

def main():
    if len(sys.argv) < 3:
        print("Usage: python excel_writer.py <excel_file> <base64_json_row>")
        sys.exit(1)

    excel_file = sys.argv[1]
    base64_data = sys.argv[2]

    # Decode the base64 JSON row
    try:
        json_str = base64.b64decode(base64_data).decode('utf-8')
        row_data = json.loads(json_str)
    except Exception as e:
        print(f"Error decoding data: {e}")
        sys.exit(1)

    # Check if file exists
    if os.path.exists(excel_file):
        wb = load_workbook(excel_file)
        ws = wb.active
    else:
        # Create new workbook with headers
        wb = Workbook()
        ws = wb.active
        ws.title = "Jobs"

        # Write header row with bold and background
        header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF')

        for col_idx, col_name in enumerate(COLUMNS, 1):
            cell = ws.cell(row=1, column=col_idx, value=col_name.upper().replace('_', ' '))
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')

        # Freeze header row
        ws.freeze_panes = 'A2'

    # Find next empty row
    next_row = ws.max_row + 1

    # Get status for coloring
    status = row_data.get('status', '')
    status_color = STATUS_COLORS.get(status, 'FFFFFF')
    status_fill = PatternFill(start_color=status_color, end_color=status_color, fill_type='solid')

    # Write the data row
    for col_idx, col_name in enumerate(COLUMNS, 1):
        value = row_data.get(col_name, '')
        cell = ws.cell(row=next_row, column=col_idx)

        # Make job_link a clickable hyperlink
        if col_name == 'job_link' and value:
            cell.value = 'Open Job'
            cell.hyperlink = value
            cell.font = Font(color='0563C1', underline='single')
        else:
            # Truncate very long values (like cover letters) for Excel
            if isinstance(value, str) and len(value) > 32000:
                value = value[:32000] + "... [truncated]"
            cell.value = value

        # Color the status column
        if col_name == 'status':
            cell.fill = status_fill
            cell.font = Font(bold=True)

        # Highlight needs_review
        if col_name == 'needs_review' and value == 'YES':
            cell.fill = PatternFill(start_color='FFD700', end_color='FFD700', fill_type='solid')
            cell.font = Font(bold=True)

    # Auto-adjust column widths (approximate)
    column_widths = {
        'status': 10,
        'needs_review': 12,
        'review_flags': 25,
        'title': 35,
        'company': 25,
        'location': 20,
        'job_link': 12,
        'posted_date': 12,
        'score': 8,
        'seniority': 15,
        'industry': 20,
        'company_size': 15,
        'role_summary': 50,
        'match_reasons': 40,
        'concerns': 30,
        'rejection_reason': 40,
        'cover_letter': 50,
        'processed_at': 20
    }

    for col_idx, col_name in enumerate(COLUMNS, 1):
        col_letter = chr(64 + col_idx) if col_idx <= 26 else f"A{chr(64 + col_idx - 26)}"
        ws.column_dimensions[col_letter].width = column_widths.get(col_name, 15)

    # Save
    wb.save(excel_file)
    print(f"Saved row to {excel_file}")

if __name__ == "__main__":
    main()
