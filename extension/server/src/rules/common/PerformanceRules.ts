import { DiagnosticSeverity } from 'vscode-languageserver/node';
import { Rule, RuleContext } from '../RuleEngine';
import Parser from 'web-tree-sitter';

export const PerformanceLoopRule: Rule = {
  id: 'common-performance-loop',
  name: 'Inefficient Loop Detection',
  severity: DiagnosticSeverity.Information,
  languages: ['python'],
  analyze: (context: RuleContext) => {
    const { document, tree, report } = context;

    function traverse(node: Parser.SyntaxNode) {
      if (node.type === 'for_statement' || node.type === 'while_statement') {
         // check if there's a function definition inside
         let hasFuncDef = false;
         for (let i = 0; i < node.childCount; i++) {
             const child = node.child(i);
             // A simplistic check, real traversal would be deeper
             if (child && child.type === 'block') {
                 for (let j = 0; j < child.childCount; j++) {
                     if (child.child(j)?.type === 'function_definition') {
                         hasFuncDef = true;
                         break;
                     }
                 }
             }
         }
         
         if (hasFuncDef) {
            report({
              severity: DiagnosticSeverity.Information,
              range: {
                start: { line: node.startPosition.row, character: node.startPosition.column },
                end: { line: node.endPosition.row, character: node.endPosition.column }
              },
              message: `Performance warning: Defining a function inside a loop can be inefficient.`,
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
