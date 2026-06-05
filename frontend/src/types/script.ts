/** Block-based script data model (Phase 7.1) */

export type BlockType = "action" | "dialogue";

export type LocationType = "INT." | "EXT." | "INT./EXT.";

export type TimeOfDay =
  | "DAY"
  | "NIGHT"
  | "DAWN"
  | "DUSK"
  | "MORNING"
  | "AFTERNOON"
  | "EVENING"
  | "LATER"
  | "CONTINUOUS"
  | "SAME TIME";

export type RoleType = "protagonist" | "antagonist" | "supporting" | "minor";

export interface SourceRef {
  chapter: number;
  paragraph: number;
  quote: string;
}

export interface ScriptBlock {
  block_id: string;
  order: number;
  type: BlockType;
  text?: string; // action
  char_id?: string; // dialogue
  char_name?: string; // dialogue
  line?: string; // dialogue
  parenthetical?: string; // dialogue
  annotation_refs: string[];
  source_ref?: SourceRef;
}

export interface Slug {
  location_type: LocationType;
  location_name: string;
  time: TimeOfDay;
}

export interface SceneAnnotationRef {
  annotation_id: string;
}

export interface Scene {
  scene_id: string;
  scene_number: number;
  slug: Slug;
  summary?: string;
  characters_present: string[];
  props: string[];
  blocks: ScriptBlock[];
  annotations: SceneAnnotationRef[];
}

export interface ScriptCharacter {
  character_id: string;
  name: string;
  aliases: string[];
  role_type: RoleType;
  age?: number;
  gender?: string;
  archetype?: string;
  traits: string[];
  arc_summary?: string;
}

export interface ScriptMetadata {
  title: string;
  subtitle?: string;
  source_novel?: string;
  source_author?: string;
  schema_version: string;
  created_at?: string;
  updated_at?: string;
  total_scenes: number;
  estimated_runtime: number;
}

export interface SceneIndexEntry {
  scene_id: string;
  scene_number: number;
  slug_line: string;
  summary?: string;
  characters: string[];
  page_estimate?: number;
}

export interface GlobalAnnotationRef {
  annotation_id: string;
}

export interface ScriptV1 {
  schema_version: "1.0";
  schema_name: "scriptforge-script";
  metadata: ScriptMetadata;
  characters: ScriptCharacter[];
  scenes: Scene[];
  scene_index: SceneIndexEntry[];
  global_annotations: GlobalAnnotationRef[];
}

/** Editor-specific helpers */

export interface EditorState {
  script: ScriptV1;
  activeSceneId: string | null;
  selectedBlockId: string | null;
  focusMode: boolean;
  commandPaletteOpen: boolean;
}

export type EditorAction =
  | { type: "SET_SCRIPT"; script: ScriptV1 }
  | { type: "UPDATE_BLOCK"; sceneId: string; blockId: string; updates: Partial<ScriptBlock> }
  | { type: "ADD_BLOCK"; sceneId: string; block: ScriptBlock; afterBlockId?: string }
  | { type: "DELETE_BLOCK"; sceneId: string; blockId: string }
  | { type: "REORDER_BLOCKS"; sceneId: string; blockIds: string[] }
  | { type: "MOVE_BLOCK"; fromSceneId: string; toSceneId: string; blockId: string; targetIndex: number }
  | { type: "SET_ACTIVE_SCENE"; sceneId: string }
  | { type: "SET_SELECTED_BLOCK"; blockId: string | null }
  | { type: "TOGGLE_FOCUS_MODE" }
  | { type: "OPEN_COMMAND_PALETTE" }
  | { type: "CLOSE_COMMAND_PALETTE" };
