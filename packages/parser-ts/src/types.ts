export interface Position {
  line: number;
  column: number;
  offset: number;
}

export interface Range {
  start: Position;
  end: Position;
}

export type NodeType =
  | 'root'
  | 'paragraph'
  | 'heading'
  | 'text'
  | 'emphasis'
  | 'strong'
  | 'inlineCode'
  | 'code'
  | 'list'
  | 'listItem'
  | 'thematicBreak'
  | 'blockquote'
  | 'directive'
  | 'role';

export interface BaseNode {
  type: NodeType;
  position?: Range;
}

export interface RootNode extends BaseNode {
  type: 'root';
  children: BlockNode[];
  frontmatter?: Record<string, unknown>;
}

export interface ParagraphNode extends BaseNode {
  type: 'paragraph';
  children: InlineNode[];
}

export interface HeadingNode extends BaseNode {
  type: 'heading';
  depth: 1 | 2 | 3 | 4 | 5 | 6;
  children: InlineNode[];
  id?: string;
}

export interface TextNode extends BaseNode {
  type: 'text';
  value: string;
}

export interface EmphasisNode extends BaseNode {
  type: 'emphasis';
  children: InlineNode[];
}

export interface StrongNode extends BaseNode {
  type: 'strong';
  children: InlineNode[];
}

export interface InlineCodeNode extends BaseNode {
  type: 'inlineCode';
  value: string;
}

export interface CodeNode extends BaseNode {
  type: 'code';
  lang?: string;
  value: string;
}

export interface ListNode extends BaseNode {
  type: 'list';
  ordered: boolean;
  children: ListItemNode[];
}

export interface ListItemNode extends BaseNode {
  type: 'listItem';
  children: BlockNode[];
}

export interface ThematicBreakNode extends BaseNode {
  type: 'thematicBreak';
}

export interface BlockquoteNode extends BaseNode {
  type: 'blockquote';
  children: BlockNode[];
}

/** Stitchwork block directive: `:::{name} args` … `:::` */
export interface DirectiveNode extends BaseNode {
  type: 'directive';
  name: string;
  args?: string;
  options: Record<string, unknown>;
  /** Children only when the directive accepts a body. Empty array for option-only directives. */
  children: BlockNode[];
}

/** Stitchwork inline role: `{name}\`opts\`[text]` or `{name}\`opts\`` */
export interface RoleNode extends BaseNode {
  type: 'role';
  name: string;
  options: Record<string, unknown>;
  /** The bracketed display text, if present. */
  text?: string;
}

export type InlineNode =
  | TextNode
  | EmphasisNode
  | StrongNode
  | InlineCodeNode
  | RoleNode;

export type BlockNode =
  | ParagraphNode
  | HeadingNode
  | CodeNode
  | ListNode
  | ThematicBreakNode
  | BlockquoteNode
  | DirectiveNode;

export type AnyNode = RootNode | BlockNode | InlineNode | ListItemNode;
