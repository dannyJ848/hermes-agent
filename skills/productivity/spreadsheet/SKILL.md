---
name: spreadsheet
version: "1.0.0"
description: |
  Native spreadsheet creation and analysis. Create XLSX files with formulas,
  formatting, charts, and multiple sheets. Read existing Excel/CSV files,
  extract data, perform analysis, and generate formatted output. Uses
  openpyxl for native Excel format (not just pandas).
license: MIT
compatibility: Python 3.10+ with openpyxl, pandas
metadata:
  author: hermeshub
  hermes:
    tags: [spreadsheet, excel, xlsx, csv, formulas, charts, data]
    category: documents
    requires_tools: [terminal, execute_code]
    priority: medium
---

# Spreadsheet (XLSX) Skill

Create and analyze Excel spreadsheets natively via openpyxl. Unlike pandas
(which handles dataframes), this produces real .xlsx files with formatting,
formulas, and charts that open in Excel/LibreOffice.

## When to Use
- User wants an Excel/spreadsheet file created
- User has CSV/Excel data to analyze and output formatted
- User needs formulas, charts, or multi-sheet workbooks
- User asks for a budget, tracker, inventory, or data table

## Creating a Spreadsheet

    from openpyxl import Workbook
    from openpyxl.chart import BarChart, Reference
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"

    # Headers with formatting
    headers = ["Item", "Q1", "Q2", "Q3", "Q4", "Total"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="2F5496", fill_type="solid")

    # Data rows with formulas
    ws.cell(row=2, column=1, value="Revenue")
    ws.cell(row=2, column=2, value=15000)
    ws.cell(row=2, column=6, value="=SUM(B2:E2)")

    # Add a chart
    chart = BarChart()
    data = Reference(ws, min_col=2, max_col=5, min_row=1, max_row=2)
    chart.add_data(data, titles_from_data=True)
    ws.add_chart(chart, "H2")

    wb.save("/tmp/report.xlsx")

## Reading a Spreadsheet

    from openpyxl import load_workbook
    wb = load_workbook("data.xlsx", data_only=True)
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            print(row)

## Key Capabilities
- Formulas (SUM, AVERAGE, VLOOKUP, IF, etc.)
- Formatting (fonts, colors, borders, number formats)
- Charts (bar, line, pie, scatter)
- Multi-sheet workbooks
- Conditional formatting
- Data validation (dropdowns, ranges)
- Pivot-ready data layouts

## Qwopus-Specific Notes
- For data analysis use pandas via execute_code, then export to xlsx
- Keep formulas simple (Qwopus writes them reliably when straightforward)
- Format after data is in place (fewer errors than interleaving)
