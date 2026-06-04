## ADDED Requirements

### Requirement: Multi-provider LLM configuration
The system SHALL support multiple LLM providers configurable by the user with their own API keys.

#### Scenario: Add an Anthropic provider
- **WHEN** user adds a new provider with type "Anthropic", model "claude-sonnet-4-6", and their API key
- **THEN** system encrypts the API key with AES-256-GCM and stores the provider configuration persistently

#### Scenario: Add an OpenAI-compatible provider
- **WHEN** user adds a new provider with type "OpenAI Compatible", custom base URL, model name, and API key
- **THEN** system treats it as an OpenAI-compatible endpoint and uses the standard Chat Completion API

#### Scenario: Masked API key in UI
- **WHEN** system returns provider configuration to the frontend
- **THEN** the API key SHALL be masked, showing only the first 6 and last 4 characters (e.g., `sk-ant-***...***aBcD`)

#### Scenario: Update or delete a provider
- **WHEN** user edits or removes a provider
- **THEN** system updates the provider configuration and all subsequent conversion runs use the updated settings

### Requirement: Stage-based model assignment
The system SHALL allow users to assign different LLM providers to different pipeline stages.

#### Scenario: Assign models to stages
- **WHEN** user configures providers, they may designate which stage(s) each provider serves (Stage 0: Bible Analysis, Stage 1: Chapter Conversion, Stage 2: Assembly)
- **THEN** the pipeline uses the assigned provider for each stage

#### Scenario: Default model fallback
- **WHEN** a stage has no explicitly assigned provider
- **THEN** system uses the project default provider

### Requirement: API key security
The system SHALL encrypt all stored API keys and never expose them in plaintext.

#### Scenario: Encryption at rest
- **WHEN** an API key is stored in the database
- **THEN** it SHALL be encrypted using AES-256-GCM with a key derived from the `SCRIPTFORGE_ENCRYPTION_KEY` environment variable

#### Scenario: Key excluded from logs and responses
- **WHEN** the system logs or returns API responses
- **THEN** the full API key SHALL never appear in logs, error messages, or API response payloads

### Requirement: LangGraph pipeline orchestration
The system SHALL use a LangGraph StateGraph to orchestrate the multi-stage conversion pipeline with streaming progress.

#### Scenario: Pipeline execution with streaming
- **WHEN** user starts a conversion
- **THEN** the LangGraph StateGraph executes stages in sequence, with Stage 1 chapters processed in parallel
- **AND** progress events are streamed to the frontend via SSE for each node execution

#### Scenario: Quality gate rejection
- **WHEN** a quality gate node detects insufficient output (e.g., fewer than 1 key character identified)
- **THEN** the graph branches to a retry path that re-invokes the previous stage with adjusted parameters
- **AND** after 3 retries, the graph branches to a human intervention node that prompts the user

#### Scenario: Pipeline state persistence
- **WHEN** a conversion is interrupted (server restart, network failure)
- **THEN** the pipeline state SHALL be recoverable from the last checkpoint
- **AND** user can resume from the last completed stage

### Requirement: SSE progress streaming
The system SHALL stream AI conversion progress to the frontend using Server-Sent Events.

#### Scenario: Stage progress events
- **WHEN** a pipeline stage starts, progresses, or completes
- **THEN** the backend emits an SSE event with `{ stage, status, message, progress_percent }`
- **AND** the frontend updates the progress UI in real-time

#### Scenario: Live script preview during generation
- **WHEN** Stage 1 is converting a chapter
- **THEN** the generated script content SHALL be streamed to the frontend as it is produced
- **AND** the user can see their novel being transformed into script in real-time
