## ADDED Requirements

### Requirement: Block-based script rendering
The system SHALL render script content as a sequence of editable blocks, alternating between action and dialogue types.

#### Scenario: Action block display
- **WHEN** the editor renders an action block
- **THEN** it SHALL display the action text in a content-editable area with a "🎬 动作" label
- **AND** show the source text reference ("💡 原文: 第X章第Y段") as a collapsible footer

#### Scenario: Dialogue block display
- **WHEN** the editor renders a dialogue block
- **THEN** it SHALL display the character name in a header, the dialogue line in a content-editable area, and the parenthetical (if any) as an editable sub-field
- **AND** show the source text reference and any linked annotations as badges

#### Scenario: Block-type visual distinction
- **WHEN** the editor displays mixed action and dialogue blocks
- **THEN** action blocks SHALL have a distinct left border color (amber gold) from dialogue blocks (sage green) for rapid visual scanning

### Requirement: Drag-and-drop block reordering
The system SHALL allow users to reorder blocks within and between scenes via drag-and-drop.

#### Scenario: Reorder blocks within a scene
- **WHEN** user drags a block to a new position within the same scene
- **THEN** system updates the block's order field and re-renders the block sequence

#### Scenario: Move block to another scene
- **WHEN** user drags a block from one scene to another
- **THEN** system removes the block from the source scene and inserts it at the drop position in the target scene

#### Scenario: Copy block with modifier key
- **WHEN** user holds Alt/Option while dragging a block
- **THEN** system creates a copy of the block at the drop position instead of moving it

### Requirement: Scene timeline navigation
The system SHALL provide a horizontal scene timeline for rapid navigation between scenes.

#### Scenario: Timeline display
- **WHEN** the editor loads a script
- **THEN** system renders a horizontal scrollable timeline showing each scene as a filmstrip card with: scene number, location emoji, character color dots, and estimated page count

#### Scenario: Scene selection via timeline
- **WHEN** user clicks a scene card in the timeline
- **THEN** the main editor scrolls to that scene and highlights it
- **AND** the side navigation also highlights the selected scene

#### Scenario: Insert scene via timeline
- **WHEN** user clicks the "+" button between two scene cards in the timeline
- **THEN** system creates a new empty scene inserted at that position

### Requirement: Keyboard shortcuts
The system SHALL support keyboard shortcuts for common editing operations.

#### Scenario: Block creation shortcuts
- **WHEN** user presses Enter at the end of a block
- **THEN** system creates a new block of the same type after the current block

#### Scenario: Block type toggling
- **WHEN** user presses Tab on a block
- **THEN** system toggles the block type between action and dialogue

#### Scenario: Global command palette
- **WHEN** user presses Cmd/Ctrl+K
- **THEN** system opens a command palette with searchable actions (navigate to scene, create checkpoint, export, find character, etc.)

### Requirement: Source text traceability
The system SHALL link each script block to its originating novel text.

#### Scenario: View source context
- **WHEN** user clicks the source reference on a block
- **THEN** system displays a popover with the original chapter text surrounding the source paragraph
- **AND** highlights the specific sentences that generated the block

### Requirement: Focus mode
The system SHALL provide a distraction-free full-screen editing mode.

#### Scenario: Enter focus mode
- **WHEN** user presses Shift+F or clicks the focus mode button
- **THEN** system hides the side navigation, annotation panel, and timeline
- **AND** centers the current scene on a dark background with Courier Prime font at increased size

#### Scenario: Exit focus mode
- **WHEN** user presses Escape in focus mode
- **THEN** system restores the full three-panel layout
