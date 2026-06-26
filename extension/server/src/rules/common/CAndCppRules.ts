import { DiagnosticSeverity } from 'vscode-languageserver/node';
import { Rule, RuleContext } from '../RuleEngine';
import Parser from 'web-tree-sitter';

const UNSAFE_FUNCTIONS: Record<string, string> = {
  strcpy: 'strcpy does not check buffer bounds. Use strncpy instead to prevent buffer overflow.',
  strcat: 'strcat does not check buffer bounds. Use strncat instead to prevent buffer overflow.',
  sprintf: 'sprintf does not check buffer bounds. Use snprintf instead.',
  gets: 'gets is extremely unsafe and has been removed from the C standard library. Use fgets instead.'
};

export const CppUnsafeFunctionsRule: Rule = {
  id: 'cpp-unsafe-functions',
  name: 'Unsafe C/C++ Functions',
  severity: DiagnosticSeverity.Warning,
  languages: ['cpp', 'c'],
  analyze: (context: RuleContext) => {
    const { tree, report } = context;

    function traverse(node: Parser.SyntaxNode) {
      if (node.type === 'call_expression') {
        const functionNode = node.childForFieldName('function');
        if (functionNode && functionNode.type === 'identifier') {
          const funcName = functionNode.text;
          if (UNSAFE_FUNCTIONS[funcName]) {
            report({
              severity: DiagnosticSeverity.Warning,
              range: {
                start: { line: functionNode.startPosition.row, character: functionNode.startPosition.column },
                end: { line: functionNode.endPosition.row, character: functionNode.endPosition.column }
              },
              message: UNSAFE_FUNCTIONS[funcName],
              source: 'OmniAnalyzer'
            });
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
