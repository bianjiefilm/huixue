import { ref, computed } from 'vue';

/**
 * 目录节点接口
 */
export interface TOCNode {
  id: string;
  level: number;
  title: string;
  children: TOCNode[];
  anchorId: string;
}

/**
 * Handbook解析器
 * 用于解析Markdown内容，生成多级目录树
 */
export function useHandbookParser() {
  /**
   * 解析Markdown内容，提取目录结构
   * @param markdownContent Markdown原始内容
   * @returns 多级目录树数组
   */
  const parseMarkdownTOC = (markdownContent: string): TOCNode[] => {
    if (!markdownContent) return [];

    const lines = markdownContent.split('\n');
    const toc: TOCNode[] = [];
    const stack: TOCNode[] = [];
    let counter = 0;

    lines.forEach((line) => {
      // 匹配Markdown标题 (# ## ### 等)
      const match = line.match(/^(#{1,6})\s+(.+)/);

      if (match) {
        const level = match[1].length;
        const title = match[2].trim();
        counter++;

        // 生成唯一的锚点ID
        const anchorId = `section-${counter}`;

        const node: TOCNode = {
          id: String(counter),
          level,
          title,
          children: [],
          anchorId
        };

        // 构建层级关系
        // 弹出所有level大于等于当前level的节点
        while (stack.length && stack[stack.length - 1].level >= level) {
          stack.pop();
        }

        // 如果栈中还有节点，说明当前节点是栈顶节点的子节点
        if (stack.length > 0) {
          stack[stack.length - 1].children.push(node);
        } else {
          // 否则是顶级节点
          toc.push(node);
        }

        // 将当前节点入栈
        stack.push(node);
      }
    });

    return toc;
  };

  /**
   * 为Markdown内容添加锚点ID
   * @param markdownContent Markdown原始内容
   * @returns 添加了锚点的Markdown内容
   */
  const addAnchorsToMarkdown = (markdownContent: string): string => {
    if (!markdownContent) return '';

    let counter = 0;
    const lines = markdownContent.split('\n');

    const processedLines = lines.map((line) => {
      const match = line.match(/^(#{1,6})\s+(.+)/);

      if (match) {
        counter++;
        const hashes = match[1];
        const title = match[2].trim();
        const anchorId = `section-${counter}`;

        // 添加锚点div
        return `<div id="${anchorId}"></div>\n\n${hashes} ${title}`;
      }

      return line;
    });

    return processedLines.join('\n');
  };

  /**
   * 扁平化目录树（用于某些场景）
   * @param nodes 目录树节点数组
   * @returns 扁平化的节点数组
   */
  const flattenTOC = (nodes: TOCNode[]): TOCNode[] => {
    const result: TOCNode[] = [];

    const traverse = (nodes: TOCNode[]) => {
      nodes.forEach((node) => {
        result.push(node);
        if (node.children.length > 0) {
          traverse(node.children);
        }
      });
    };

    traverse(nodes);
    return result;
  };

  /**
   * 根据锚点ID查找节点
   * @param nodes 目录树节点数组
   * @param anchorId 锚点ID
   * @returns 匹配的节点或null
   */
  const findNodeByAnchor = (nodes: TOCNode[], anchorId: string): TOCNode | null => {
    for (const node of nodes) {
      if (node.anchorId === anchorId) {
        return node;
      }
      if (node.children.length > 0) {
        const found = findNodeByAnchor(node.children, anchorId);
        if (found) return found;
      }
    }
    return null;
  };

  return {
    parseMarkdownTOC,
    addAnchorsToMarkdown,
    flattenTOC,
    findNodeByAnchor
  };
}
