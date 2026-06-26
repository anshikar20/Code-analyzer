import { Diagnostic, DiagnosticSeverity } from 'vscode-languageserver/node';
import { TextDocument } from 'vscode-languageserver-textdocument';
import Parser from 'web-tree-sitter';

export interface RuleContext {
  document: TextDocument;
  tree: Parser.Tree;
  report: (diagnostic: Diagnostic) => void;
}

export interface Rule {
  id: string;
  name: string;
  severity: DiagnosticSeverity;
  languages: string[]; // 'all' or ['python', 'java', 'cpp']
  analyze: (context: RuleContext) => void;
}

export interface CustomRule {
  id: string;
  name: string;
  severity: string;
  languages: string[];
  enabled: boolean;
  regex: string;
  description: string;
}

export class RuleEngine {
  private rules: Rule[] = [];
  private customRules: CustomRule[] = [];

  public registerRule(rule: Rule) {
    this.rules.push(rule);
  }

  public setCustomRules(rules: CustomRule[]) {
    this.customRules = rules;
  }

  public run(document: TextDocument, tree: Parser.Tree): Diagnostic[] {
    const diagnostics: Diagnostic[] = [];
    const report = (d: Diagnostic) => diagnostics.push(d);

    const context: RuleContext = { document, tree, report };

    // Run Built-in Rules
    for (const rule of this.rules) {
      if (rule.languages.includes(document.languageId) || rule.languages.includes('all')) {
        try {
          rule.analyze(context);
        } catch (e) {
          console.error(`Error running rule ${rule.name}:`, e);
        }
      }
    }

    // Run Custom Regex Rules
    const text = document.getText();
    for (const rule of this.customRules) {
      if (!rule.enabled || !rule.regex) continue;
      if (rule.languages.includes(document.languageId) || rule.languages.includes('all')) {
        try {
          const re = new RegExp(rule.regex, 'g');
          let match;
          while ((match = re.exec(text)) !== null) {
            const startPos = document.positionAt(match.index);
            const endPos = document.positionAt(match.index + match[0].length);

            report({
              severity: this.mapSeverity(rule.severity),
              range: { start: startPos, end: endPos },
              message: rule.description || rule.name,
              source: 'OmniAnalyzerCustom'
            });

            // Prevent infinite loop if regex doesn't advance
            if (re.lastIndex === match.index) {
              re.lastIndex++;
            }
          }
        } catch (e) {
          console.error(`Error running custom rule ${rule.name}:`, e);
        }
      }
    }

    return diagnostics;
  }

  private mapSeverity(severity: string): DiagnosticSeverity {
    switch (severity?.toLowerCase()) {
      case 'critical':
      case 'error':
        return DiagnosticSeverity.Error;
      case 'warning':
        return DiagnosticSeverity.Warning;
      case 'info':
      default:
        return DiagnosticSeverity.Information;
    }
  }
}

// Built-in Syntax Error Rule
export const SyntaxErrorRule: Rule = {
  id: 'core-syntax-error',
  name: 'Syntax Error Detection',
  severity: DiagnosticSeverity.Error,
  languages: ['all'],
  analyze: (context: RuleContext) => {
    const { document, tree, report } = context;

    function traverse(node: Parser.SyntaxNode) {
      if (node.isMissing()) {
        report({
          severity: DiagnosticSeverity.Error,
          range: {
            start: { line: node.startPosition.row, character: node.startPosition.column },
            end: { line: node.endPosition.row, character: node.endPosition.column }
          },
          message: `Syntax error: missing ${node.type}`,
          source: 'OmniAnalyzer'
        });
      } else if (node.type === 'ERROR') {
        report({
          severity: DiagnosticSeverity.Error,
          range: {
            start: { line: node.startPosition.row, character: node.startPosition.column },
            end: { line: node.endPosition.row, character: node.endPosition.column }
          },
          message: `Syntax error`,
          source: 'OmniAnalyzer'
        });
      }
      for (let i = 0; i < node.childCount; i++) {
        traverse(node.child(i)!);
      }
    }

    traverse(tree.rootNode);
  }
};
