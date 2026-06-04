## ADDED Requirements

### Requirement: Multi-format export
The system SHALL export scripts in YAML, PDF, Fountain, and Final Draft XML (FDX) formats.

#### Scenario: YAML export
- **WHEN** user exports as YAML
- **THEN** system downloads the complete script as a `.yaml` file following the ScriptForge Script Schema v1.0

#### Scenario: PDF export with standard screenplay formatting
- **WHEN** user exports as PDF
- **THEN** system generates a PDF with standard screenplay formatting: 12pt Courier Prime, 1.5" left margin, 1" right/top/bottom margins, proper slug line and dialogue positioning
- **AND** includes a title page with script title, author, and generation date

#### Scenario: Fountain export
- **WHEN** user exports as Fountain
- **THEN** system converts the script to Fountain syntax (standard plain-text screenplay markup) and downloads as `.fountain`

#### Scenario: FDX export
- **WHEN** user exports as Final Draft XML
- **THEN** system generates a valid `.fdx` file compatible with Final Draft software, with proper XML structure for scenes, characters, and dialogue elements

### Requirement: Export format selection
The system SHALL allow users to select export format and configure format-specific options.

#### Scenario: Export dialog
- **WHEN** user clicks "导出" on the editor toolbar
- **THEN** system displays a dialog with format options (YAML/PDF/Fountain/FDX), a preview area, and format-specific configuration

#### Scenario: Multi-format batch export
- **WHEN** user selects multiple formats and confirms export
- **THEN** system generates all selected formats and packages them as a zip download

### Requirement: Print-ready PDF
The system SHALL produce print-ready PDFs following industry screenplay standards.

#### Scenario: Page numbering
- **WHEN** PDF is generated
- **THEN** page numbers SHALL appear in the top-right corner of every page after the title page
- **AND** scene numbers SHALL appear in the left and right margins

#### Scenario: Page break handling
- **WHEN** a scene spans a page break
- **THEN** the PDF SHALL include (CONTINUED) markers at page bottoms and CONTINUED: headers at page tops per industry convention
