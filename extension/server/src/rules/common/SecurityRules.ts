import { DiagnosticSeverity } from 'vscode-languageserver/node';
import { Rule, RuleContext } from '../RuleEngine';
import Parser from 'web-tree-sitter';

export const HardcodedSecretRule: Rule = {
  id: 'common-hardcoded-secret',
  name: 'Hardcoded Secret Detection',
  severity: DiagnosticSeverity.Warning,
  languages: ['all'],
  analyze: (context: RuleContext) => {
    const { document, tree, report } = context;

    // simplistic regex for demo purposes
    const secretRegex = /(?:api[_-]?key|password|secret|token)\s*=\s*['"]([a-zA-Z0-9_\-\.]{10,})['"]/i;

    function traverse(node: Parser.SyntaxNode) {
      if (node.type.includes('assignment') || node.type.includes('variable_declaration')) {
         const text = node.text;
         const match = secretRegex.exec(text);
         if (match) {
            report({
              severity: DiagnosticSeverity.Warning,
              range: {
                start: { line: node.startPosition.row, character: node.startPosition.column },
                end: { line: node.endPosition.row, character: node.endPosition.column }
              },
              message: `Possible hardcoded secret detected. Avoid storing secrets in source code.`,
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
