import { DiagnosticSeverity } from 'vscode-languageserver/node';
import { Rule, RuleContext } from '../RuleEngine';
import Parser from 'web-tree-sitter';

export const PythonUnusedVariableRule: Rule = {
  id: 'python-unused-variable',
  name: 'Python Unused Variable Detection',
  severity: DiagnosticSeverity.Warning,
  languages: ['python'],
  analyze: (context: RuleContext) => {
    const { document, tree, report } = context;

    const assignments: Map<string, Parser.SyntaxNode> = new Map();
    const usages: Set<string> = new Set();

    const traverse = (node: Parser.SyntaxNode) => {
      if (node.type === 'assignment') {
        const left = node.childForFieldName('left');
        if (left && left.type === 'identifier') {
          assignments.set(left.text, left);
        }
      } else if (node.type === 'identifier') {
        const parentType = node.parent?.type;
        if (parentType !== 'assignment' || node.parent?.childForFieldName('left')?.id !== node.id) {
          usages.add(node.text);
        }
      }

      for (let i = 0; i < node.childCount; i++) {
        traverse(node.child(i)!);
      }
    };

    traverse(tree.rootNode);

    for (const [name, node] of assignments.entries()) {
      if (!usages.has(name) && !name.startsWith('_')) {
        report({
          severity: DiagnosticSeverity.Warning,
          range: {
            start: { line: node.startPosition.row, character: node.startPosition.column },
            end: { line: node.endPosition.row, character: node.endPosition.column }
          },
          message: `Variable '${name}' is assigned but never used.`,
          source: 'OmniAnalyzer'
        });
      }
    }
  }
};

export const PythonMutableDefaultArgumentRule: Rule = {
  id: 'python-mutable-default-argument',
  name: 'Python Mutable Default Argument',
  severity: DiagnosticSeverity.Warning,
  languages: ['python'],
  analyze: (context: RuleContext) => {
    const { tree, report } = context;

    function traverse(node: Parser.SyntaxNode) {
      if (node.type === 'default_parameter') {
        const valueNode = node.childForFieldName('value');
        if (valueNode && (valueNode.type === 'list' || valueNode.type === 'dictionary' || valueNode.type === 'set')) {
          report({
            severity: DiagnosticSeverity.Warning,
            range: {
              start: { line: valueNode.startPosition.row, character: valueNode.startPosition.column },
              end: { line: valueNode.endPosition.row, character: valueNode.endPosition.column }
            },
            message: `Mutable default argument of type '${valueNode.type}' detected. Use None as default instead.`,
            source: 'OmniAnalyzer'
          });
        }
      }

      for (let i = 0; i < node.childCount; i++) {
        traverse(node.child(i)!);
      }
    }

    traverse(tree.rootNode);
  }
};

export const PythonUnreachableCodeRule: Rule = {
  id: 'python-unreachable-code',
  name: 'Python Unreachable Code Detection',
  severity: DiagnosticSeverity.Warning,
  languages: ['python'],
  analyze: (context: RuleContext) => {
    const { tree, report } = context;

    function traverse(node: Parser.SyntaxNode) {
      if (node.type === 'block') {
        let hasControlTerminator = false;
        let terminatorNode: Parser.SyntaxNode | null = null;
        for (let i = 0; i < node.childCount; i++) {
          const child = node.child(i);
          if (!child) continue;

          if (hasControlTerminator) {
            report({
              severity: DiagnosticSeverity.Warning,
              range: {
                start: { line: child.startPosition.row, character: child.startPosition.column },
                end: { line: child.endPosition.row, character: child.endPosition.column }
              },
              message: `Unreachable code: statement is after a '${terminatorNode?.type.replace('_statement', '')}'.`,
              source: 'OmniAnalyzer'
            });
          }

          if (child.type === 'return_statement' || child.type === 'break_statement' || child.type === 'continue_statement' || child.type === 'raise_statement') {
            hasControlTerminator = true;
            terminatorNode = child;
          }
        }
      }

      for (let i = 0; i < node.childCount; i++) {
        traverse(node.child(i)!);
      }
    }

    traverse(tree.rootNode);
  }
};

