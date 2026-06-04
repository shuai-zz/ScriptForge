## ADDED Requirements

### Requirement: Stage 0 — Global Story Bible generation
The system SHALL analyze all uploaded chapters to produce a structured Story Bible containing characters, relationships, timeline, themes, foreshadowing, and locations.

#### Scenario: Character extraction
- **WHEN** Stage 0 executes
- **THEN** system identifies all named characters across all chapters
- **AND** for each character, extracts: name, aliases, role type (protagonist/antagonist/supporting/minor), age, gender, traits, arc summary, speech patterns, and relationships with other characters

#### Scenario: Relationship network construction
- **WHEN** Stage 0 extracts characters
- **THEN** system identifies character relationships including: type (lover/family/friend/rival/etc.), intensity (1-5), history, current status, and predicted evolution across chapters

#### Scenario: Timeline construction
- **WHEN** Stage 0 analyzes chapters
- **THEN** system constructs an event timeline including: time label (now/flashback/flashforward), event description, duration, time of day, and trigger events for flashbacks

#### Scenario: Theme and motif extraction
- **WHEN** Stage 0 analyzes chapters
- **THEN** system identifies 1-3 core themes with supporting textual instances and suggests visual motifs for screen adaptation

#### Scenario: Foreshadowing tracking
- **WHEN** Stage 0 identifies a plot setup
- **THEN** system records it as a foreshadowing item with: setup chapter, description, status (unresolved/resolved), and payoff chapter if resolved

### Requirement: Stage 1 — Per-chapter conversion
The system SHALL convert each chapter into structured script scenes, using the Story Bible as shared context.

#### Scenario: Scene boundary detection
- **WHEN** Stage 1 processes a chapter
- **THEN** system identifies scene boundaries based on location changes, time jumps, and narrative breaks
- **AND** generates a standard slug line (INT./EXT. Location - Time) for each scene

#### Scenario: Narrative-to-action conversion
- **WHEN** Stage 1 encounters descriptive narration
- **THEN** system converts it into visual action blocks while preserving essential atmosphere and detail
- **AND** each action block includes a source reference to the original chapter and paragraph

#### Scenario: Inner monologue externalization
- **WHEN** Stage 1 encounters internal thoughts or emotional descriptions
- **THEN** system externalizes them through character actions, expressions, subtext in dialogue, or visual metaphors
- **AND** generates an annotation explaining the adaptation decision with confidence score

#### Scenario: Dialogue extraction and formatting
- **WHEN** Stage 1 encounters character speech (direct or described)
- **THEN** system extracts or reconstructs dialogue in standard screenplay format (character name + line + optional parenthetical)
- **AND** for described speech (not direct quote), marks the annotation with lower confidence

#### Scenario: Parallel chapter processing
- **WHEN** multiple chapters need conversion in Stage 1
- **THEN** system processes them in parallel within the LangGraph map node
- **AND** each chapter receives the Story Bible and the preceding chapter's script as context

### Requirement: Stage 2 — Global assembly and validation
The system SHALL assemble all chapter scripts into a complete screenplay and perform cross-chapter consistency checks.

#### Scenario: Sequential scene assembly
- **WHEN** Stage 2 executes
- **THEN** system concatenates all chapter scenes in order, assigns sequential scene numbers, and generates the scene index table

#### Scenario: Character consistency validation
- **WHEN** Stage 2 assembles the script
- **THEN** system checks that character names are consistent across all scenes
- **AND** flags any character who appears in early chapters but disappears without resolution

#### Scenario: Timeline consistency validation
- **WHEN** Stage 2 validates the script
- **THEN** system checks that time-of-day transitions between consecutive scenes are logically coherent
- **AND** flags any implausible time jumps for user review

#### Scenario: Global annotation generation
- **WHEN** Stage 2 completes assembly
- **THEN** system generates global annotations covering: pacing issues, character balance, structural suggestions, and missing elements

### Requirement: Conversion run management
The system SHALL track each conversion run with status, timing, and error information.

#### Scenario: Conversion run lifecycle
- **WHEN** a conversion starts
- **THEN** system creates a ConversionRun record with status "running" and start timestamp
- **AND** upon completion or failure, updates status and records duration and any error messages

#### Scenario: Resume after failure
- **WHEN** a conversion fails at a specific stage
- **THEN** user can retry from the failed stage using the persisted checkpoint state
