## ADDED Requirements

### Requirement: Automatic version saving
The system SHALL automatically save versions of the project at configurable intervals and on significant events.

#### Scenario: Periodic auto-save
- **WHEN** user has unsaved changes and the auto-save interval elapses (default 2 minutes)
- **THEN** system creates a Git commit with message "自动保存" and updates the version timeline

#### Scenario: Auto-save on AI generation completion
- **WHEN** a conversion pipeline completes successfully
- **THEN** system automatically creates a version tagged `ai-generated` with a descriptive commit message

#### Scenario: No auto-save without changes
- **WHEN** the auto-save interval elapses but no changes exist since the last save
- **THEN** system SHALL NOT create an empty commit

### Requirement: User checkpoints
The system SHALL allow users to manually save named checkpoints.

#### Scenario: Create a checkpoint
- **WHEN** user triggers "保存检查点" (e.g., via Cmd+S or UI button)
- **THEN** system opens a modal for the user to enter a description and optional tags
- **AND** creates a version with the user's description as the commit message

#### Scenario: Checkpoint confirmation
- **WHEN** a checkpoint is created
- **THEN** system displays a brief toast notification confirming the save with the version identifier

### Requirement: Version timeline
The system SHALL display version history as a chronological timeline.

#### Scenario: Timeline display
- **WHEN** user navigates to the version history page
- **THEN** system displays a vertical timeline with each version showing: version ID, timestamp, type (auto-save/checkpoint/AI-generated), user description (if any), and a summary of changes

#### Scenario: Version type visual distinction
- **WHEN** the timeline renders versions
- **THEN** auto-save versions SHALL use a subtle gray icon; user checkpoints SHALL use a marked amber icon; AI-generated versions SHALL use a sage green icon

### Requirement: Version diff
The system SHALL allow users to compare any two versions of their script.

#### Scenario: Side-by-side diff view
- **WHEN** user selects two versions and clicks "对比"
- **THEN** system displays a side-by-side or unified diff of the YAML script content
- **AND** highlights added, removed, and modified lines with color coding

#### Scenario: Change summary statistics
- **WHEN** a diff is computed
- **THEN** system displays summary statistics: number of lines added, removed, and modified; scenes changed; characters added or removed

### Requirement: Version restore
The system SHALL allow users to restore their project to any previous version.

#### Scenario: Restore to previous version
- **WHEN** user selects a version and clicks "恢复到此版本"
- **THEN** system displays a confirmation dialog warning that current unsaved changes will be lost
- **AND** suggests creating a checkpoint before restoring

#### Scenario: Restore execution
- **WHEN** user confirms restoration
- **THEN** system checks out the selected version's files
- **AND** creates a new version entry marking the restore event
- **AND** reloads the editor with the restored content

### Requirement: Zero Git knowledge required
The system SHALL use Git internally but expose no Git concepts to the user.

#### Scenario: User-facing terminology
- **WHEN** the system displays version-related UI
- **THEN** all terminology SHALL use plain language: "保存" (Save), "检查点" (Checkpoint), "版本历史" (Version History), "对比" (Compare), "恢复" (Restore)
- **AND** terms like "commit", "branch", "push", "merge" SHALL never appear in the UI
