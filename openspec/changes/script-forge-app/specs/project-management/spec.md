## ADDED Requirements

### Requirement: Project CRUD
The system SHALL allow users to create, read, update, and delete script adaptation projects.

#### Scenario: Create a new project
- **WHEN** user navigates to dashboard and clicks "新建项目"
- **THEN** system presents a creation form with project name, optional description, and target format (movie/tv_series/stage_play)
- **AND** upon submission, system creates the project with a unique UUID and redirects to the project workspace

#### Scenario: List all projects
- **WHEN** user navigates to the dashboard
- **THEN** system displays all projects as cards showing project name, scene count, character count, last modified time, and a progress indicator

#### Scenario: Delete a project
- **WHEN** user confirms project deletion
- **THEN** system removes the project, its chapters, scripts, and associated Git repository
- **AND** system displays a confirmation message

### Requirement: Chapter upload and management
The system SHALL accept novel chapters as text input and manage them for a project.

#### Scenario: Upload chapters via text paste
- **WHEN** user pastes chapter text into the upload area
- **THEN** system accepts the text, auto-detects word count, and stores it as a chapter with auto-incremented chapter number

#### Scenario: Upload chapters via file
- **WHEN** user uploads a .txt or .md file
- **THEN** system reads the file content, stores it as a chapter, and displays the chapter title (from filename or first line)

#### Scenario: Minimum chapter requirement for conversion
- **WHEN** user attempts to start AI conversion with fewer than 3 chapters uploaded
- **THEN** system SHALL display a message indicating at least 3 chapters are required and prevent conversion from starting

#### Scenario: Reorder chapters
- **WHEN** user drags a chapter to a new position in the chapter list
- **THEN** system updates the chapter numbering and persists the new order

### Requirement: Project configuration
The system SHALL allow users to configure conversion parameters for a project.

#### Scenario: Configure target format
- **WHEN** user selects a target format (movie, tv_series, stage_play)
- **THEN** system adjusts conversion prompts and output schema accordingly

#### Scenario: Configure conversion parameters
- **WHEN** user adjusts parameters such as scene title style (international/chinese), dialogue name style, annotation detail level, and dialogue preservation preference
- **THEN** system persists these preferences and applies them during the next conversion run
