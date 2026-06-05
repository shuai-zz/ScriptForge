import { useCallback } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { Scene, ScriptBlock, ScriptCharacter } from "@/types/script";
import ActionBlock from "./ActionBlock";
import DialogueBlock from "./DialogueBlock";
import { cn } from "@/lib/utils";
import { GripVertical, Plus, Trash2 } from "lucide-react";

interface SceneContainerProps {
  scene: Scene;
  characters: ScriptCharacter[];
  selectedBlockId: string | null;
  highlightedBlockId: string | null;
  readOnly?: boolean;
  onUpdateBlock: (blockId: string, updates: Partial<ScriptBlock>) => void;
  onAddBlock: (afterBlockId?: string, type?: ScriptBlock["type"]) => void;
  onDeleteBlock: (blockId: string) => void;
  onReorderBlocks: (blockIds: string[]) => void;
  onSelectBlock: (blockId: string) => void;
  onToggleBlockType: (blockId: string) => void;
}

function SortableBlockItem({
  block,
  characters,
  isSelected,
  isHighlighted,
  readOnly,
  onUpdate,
  onSelect,
  onEnter,
  onToggleType,
  onDelete,
}: {
  block: ScriptBlock;
  characters: ScriptCharacter[];
  isSelected: boolean;
  isHighlighted: boolean;
  readOnly?: boolean;
  onUpdate: (updates: Partial<ScriptBlock>) => void;
  onSelect: () => void;
  onEnter: () => void;
  onToggleType: () => void;
  onDelete: () => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: block.block_id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} className="relative">
      {!readOnly && (
        <button
          className="absolute -left-6 top-1/2 -translate-y-1/2 text-muted opacity-0 transition-opacity hover:text-foreground group-hover:opacity-100"
          {...attributes}
          {...listeners}
        >
          <GripVertical size={14} />
        </button>
      )}
      <div className={cn("group transition-all", isHighlighted && "animate-pulse-highlight")}>
        {block.type === "action" ? (
          <ActionBlock
            block={block}
            characters={characters}
            isSelected={isSelected}
            readOnly={readOnly}
            onUpdate={onUpdate}
            onSelect={onSelect}
            onEnter={onEnter}
            onToggleType={onToggleType}
          />
        ) : (
          <DialogueBlock
            block={block}
            characters={characters}
            isSelected={isSelected}
            readOnly={readOnly}
            onUpdate={onUpdate}
            onSelect={onSelect}
            onEnter={onEnter}
            onToggleType={onToggleType}
          />
        )}
        {isSelected && !readOnly && (
          <div className="mt-1 flex gap-2 opacity-0 transition-opacity group-hover:opacity-100">
            <button
              className="flex items-center gap-1 rounded bg-accent px-2 py-0.5 text-xs text-muted hover:text-foreground"
              onClick={(e) => {
                e.stopPropagation();
                onEnter();
              }}
            >
              <Plus size={12} /> 添加块
            </button>
            <button
              className="flex items-center gap-1 rounded bg-accent px-2 py-0.5 text-xs text-rose-400 hover:text-rose-300"
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
            >
              <Trash2 size={12} /> 删除
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SceneContainer({
  scene,
  characters,
  selectedBlockId,
  highlightedBlockId,
  readOnly,
  onUpdateBlock,
  onAddBlock,
  onDeleteBlock,
  onReorderBlocks,
  onSelectBlock,
  onToggleBlockType,
}: SceneContainerProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (over && active.id !== over.id) {
        const oldIndex = scene.blocks.findIndex((b) => b.block_id === active.id);
        const newIndex = scene.blocks.findIndex((b) => b.block_id === over.id);
        const newBlocks = arrayMove(scene.blocks, oldIndex, newIndex).map(
          (b, i) => ({ ...b, order: i })
        );
        onReorderBlocks(newBlocks.map((b) => b.block_id));
      }
    },
    [scene.blocks, onReorderBlocks]
  );

  const slugLine = `${scene.slug.location_type} ${scene.slug.location_name} - ${scene.slug.time}`;

  return (
    <div className="mb-8">
      {/* Slug line */}
      <div className="mb-4 border-b border-border pb-2">
        <h3 className="font-mono text-sm font-bold uppercase tracking-wide text-amber-gold">
          {slugLine}
        </h3>
        {scene.summary && (
          <p className="mt-1 text-xs text-muted">{scene.summary}</p>
        )}
      </div>

      {/* Blocks */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={scene.blocks.map((b) => b.block_id)}
          strategy={verticalListSortingStrategy}
        >
          <div className="space-y-3 pl-6">
            {scene.blocks.map((block) => (
              <SortableBlockItem
                key={block.block_id}
                block={block}
                characters={characters}
                isSelected={selectedBlockId === block.block_id}
                isHighlighted={highlightedBlockId === block.block_id}
                readOnly={readOnly}
                onUpdate={(updates) => onUpdateBlock(block.block_id, updates)}
                onSelect={() => onSelectBlock(block.block_id)}
                onEnter={() => onAddBlock(block.block_id, block.type)}
                onToggleType={() => onToggleBlockType(block.block_id)}
                onDelete={() => onDeleteBlock(block.block_id)}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      {/* Add block at end */}
      {!readOnly && (
        <button
          className="mt-3 flex w-full items-center justify-center gap-1 rounded-md border border-dashed border-border py-2 text-xs text-muted hover:border-amber-gold hover:text-amber-gold"
          onClick={() => onAddBlock()}
        >
          <Plus size={14} /> 添加块
        </button>
      )}
    </div>
  );
}
