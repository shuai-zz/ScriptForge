## ADDED Requirements

### Requirement: Script schema definition
The system SHALL define a YAML Schema (v1.0) for complete screenplay representation.

#### Scenario: Script metadata
- **WHEN** a script YAML is generated
- **THEN** it SHALL include a `metadata` section with: title, optional subtitle, source novel name, source author, schema version, timestamps, total scene count, and estimated runtime

#### Scenario: Character roster in script
- **WHEN** a script YAML is generated
- **THEN** it SHALL include a `characters` list where each character has: unique ID, name, aliases, role type, age, gender, archetype, traits list, arc summary, and relationships

#### Scenario: Scene content structure
- **WHEN** a script YAML is generated
- **THEN** each scene SHALL contain: unique ID, scene number, slug (location type + name + time), summary, characters present list, props list, content blocks (alternating action/dialogue), and annotations

#### Scenario: Scene index
- **WHEN** a script YAML is generated
- **THEN** it SHALL include a `scene_index` section providing a flat list of all scenes with scene ID, number, slug, summary, characters, and page estimate for quick navigation

### Requirement: Character schema definition
The system SHALL define a YAML Schema (v1.0) for individual character profiles, separable from scripts.

#### Scenario: Character basic info
- **WHEN** a character profile YAML is generated
- **THEN** it SHALL include: character ID, basic info (name, aliases, age, gender, occupation, appearance), story role (type, archetype, motivation, goals, flaw), and character arc (starting state, midpoint shift, ending state)

#### Scenario: Character voice profiling
- **WHEN** a character profile YAML is generated
- **THEN** it SHALL include voice characteristics: speech patterns, catchphrases, vocabulary level — to enable AI to generate distinctive dialogue per character

#### Scenario: Cross-project character reuse
- **WHEN** a character profile is stored as an independent YAML file
- **THEN** it SHALL be referenceable from multiple script projects via its character ID

### Requirement: Story Bible schema definition
The system SHALL define a YAML Schema (v1.0) for the Story Bible — the AI's global analysis output.

#### Scenario: Chapter synopses
- **WHEN** a Story Bible YAML is generated
- **THEN** it SHALL include overall synopsis and per-chapter summaries with: key events (≤5 per chapter), new characters introduced, new locations introduced, foreshadowing setups, and foreshadowing payoffs

#### Scenario: Character network
- **WHEN** a Story Bible YAML is generated
- **THEN** it SHALL include a character network with nodes (character references) and edges (relationships with chapter activity ranges and key moments)

#### Scenario: Timeline, themes, foreshadowing, locations
- **WHEN** a Story Bible YAML is generated
- **THEN** it SHALL include: a chronological event timeline with flashback markers, theme identification with visual motif suggestions, comprehensive foreshadowing tracking, and location index with key props

### Requirement: Project config schema definition
The system SHALL define a YAML Schema (v1.0) for project-level configuration.

#### Scenario: LLM provider configuration
- **WHEN** a project config YAML is saved
- **THEN** it SHALL include an `llm_providers` list where each provider specifies: label, provider type (anthropic/openai_compatible), model name, optional base URL, encrypted API key, assigned pipeline stages, and model parameters (temperature, max_tokens, thinking settings)

#### Scenario: Conversion parameters
- **WHEN** a project config YAML is saved
- **THEN** it SHALL include conversion parameters: target format, language, scene title style, dialogue name style, annotation detail level, auto-split setting, and dialogue preservation preference

### Requirement: Annotation schema definition
The system SHALL define a YAML Schema (v1.0) for AI adaptation annotations.

#### Scenario: Annotation structure
- **WHEN** an annotation YAML is generated
- **THEN** it SHALL include: unique ID, severity level, category (from controlled vocabulary), target reference (type + scene + element), title, detailed description, source quote, alternatives list with pros/cons, confidence score, and auto-applied flag

#### Scenario: Annotation category taxonomy
- **WHEN** an annotation is categorized
- **THEN** the category field SHALL use one of these controlled values: `adaptation_decision`, `inner_to_visual`, `pacing_suggestion`, `character_consistency`, `dialogue_enhancement`, `scene_split_merge`, `foreshadowing`, `format_mismatch`

### Requirement: Schema documentation
The system SHALL include a Schema documentation file explaining the design rationale for each field and design decision.

#### Scenario: Schema doc covers design rationale
- **WHEN** a developer or user reads the Schema documentation
- **THEN** it SHALL explain for each major design decision: what the field/decision is, why it was made, what alternatives were considered, and what trade-offs exist

#### Scenario: Schema versioning policy
- **WHEN** schemas need to evolve
- **THEN** they SHALL follow semantic versioning (vMAJOR.MINOR) with backward compatibility documented
