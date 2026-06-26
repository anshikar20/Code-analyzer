import { DiagnosticSeverity } from 'vscode-languageserver/node';
import { Rule, RuleContext } from '../RuleEngine';

const VULNERABLE_PACKAGES = ['log4j', 'requests']; // simplistic mock

export const DependencyVulnerabilityRule: Rule = {
  id: 'common-dependency-vulnerability',
  name: 'Dependency Vulnerability Detection',
  severity: DiagnosticSeverity.Error,
  languages: ['python', 'java'],
  analyze: (context: RuleContext) => {
    const { tree, report } = context;

    function traverse(node: any) {
       if (node.type === 'import_statement' || node.type === 'import_from_statement' || node.type === 'import_declaration') {
          const text = node.text;
          for (const pkg of VULNERABLE_PACKAGES) {
             // simplified check for demo
             if (text.includes(pkg)) {
                 report({
                    severity: DiagnosticSeverity.Error,
                    range: {
                      start: { line: node.startPosition.row, character: node.startPosition.column },
                      end: { line: node.endPosition.row, character: node.endPosition.column }
                    },
                    message: `Security vulnerability: Package '${pkg}' is known to have vulnerabilities.`,
                    source: 'OmniAnalyzer'
                 });
             }
          }
       }
       for (let i = 0; i < node.childCount; i++) {
          traverse(node.child(i));
       }
    }
    
    traverse(tree.rootNode);
  }
};
