## ADDED Requirements

### Requirement: Annotation generation during conversion
The system SHALL generate annotations for each adaptation decision made by the AI during conversion.

#### Scenario: Annotation for inner-to-visual adaptation
- **WHEN** AI converts internal monologue to visual action
- **THEN** system generates an annotation with: severity "suggestion", category "inner_to_visual", a description of what was changed and why, the original text quote, 1-2 alternative approaches, and a confidence score

#### Scenario: Confidence scoring
- **WHEN** AI makes an adaptation decision
- **THEN** system assigns a confidence score (0.0–1.0)
- **AND** annotations with confidence below 0.6 are automatically marked with a "low confidence" visual indicator

### Requirement: Annotation display in editor
The system SHALL display annotations in a filterable sidebar panel linked to the corresponding script blocks.

#### Scenario: Annotation sidebar
- **WHEN** user opens a script in the editor
- **THEN** the right sidebar displays all annotations for the currently selected scene, grouped by severity

#### Scenario: Annotation-to-block highlighting
- **WHEN** user hovers over an annotation in the sidebar
- **THEN** the corresponding script block (action or dialogue) SHALL pulse with a highlight animation

#### Scenario: Click annotation to navigate
- **WHEN** user clicks an annotation in the sidebar
- **THEN** the editor scrolls to the corresponding block and expands its annotation details inline

### Requirement: Annotation filtering
The system SHALL allow users to filter annotations by severity, category, and confidence level.

#### Scenario: Filter by confidence
- **WHEN** user selects "low confidence only" filter
- **THEN** the sidebar displays only annotations with confidence < 0.6, enabling focused review of uncertain AI decisions

#### Scenario: Filter by category
- **WHEN** user selects a category filter (e.g., "inner_to_visual")
- **THEN** sidebar displays only annotations of that category

### Requirement: Annotation actions
The system SHALL allow users to accept, ignore, or request modification of AI annotations.

#### Scenario: Accept an annotation
- **WHEN** user clicks "Accept" on an annotation
- **THEN** the annotation turns green and is removed from the active review list
- **AND** the associated script content remains unchanged

#### Scenario: Ignore an annotation
- **WHEN** user clicks "Ignore" on an annotation
- **THEN** the annotation turns gray with reduced opacity and is hidden from default view

#### Scenario: Apply an alternative suggestion
- **WHEN** an annotation includes alternative approaches
- **AND** user selects one of the alternatives
- **THEN** system replaces the associated script block content with the selected alternative
- **AND** marks the annotation as resolved

### Requirement: Global annotations
The system SHALL generate project-level annotations for cross-scene concerns.

#### Scenario: Global pacing suggestion
- **WHEN** Stage 2 detects consecutive slow-paced scenes exceeding a threshold
- **THEN** system generates a global annotation suggesting pacing adjustments with specific scene references

#### Scenario: Character balance warning
- **WHEN** Stage 2 detects a character appearing in fewer than 5% of scenes despite being listed as a main character
- **THEN** system generates a global warning annotation about character underutilization
