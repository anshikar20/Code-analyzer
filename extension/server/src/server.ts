import {
  createConnection,
  TextDocuments,
  ProposedFeatures,
  InitializeParams,
  TextDocumentSyncKind,
  InitializeResult,
  DidChangeConfigurationNotification
} from 'vscode-languageserver/node';

import { TextDocument } from 'vscode-languageserver-textdocument';
import { ParserManager } from './parser/ParserManager';
import { DocumentManager } from './document/DocumentManager';
import { RuleEngine, SyntaxErrorRule } from './rules/RuleEngine';
import { PythonUnusedVariableRule, PythonMutableDefaultArgumentRule, PythonUnreachableCodeRule } from './rules/python/SemanticRules';
import { HardcodedSecretRule } from './rules/common/SecurityRules';
import { PerformanceLoopRule } from './rules/common/PerformanceRules';
import { DependencyVulnerabilityRule } from './rules/common/DependencyRules';
import { CppUnsafeFunctionsRule } from './rules/common/CAndCppRules';

const connection = createConnection(ProposedFeatures.all);
const documents: TextDocuments<TextDocument> = new TextDocuments(TextDocument);

const documentManager = new DocumentManager();
const ruleEngine = new RuleEngine();

// Register Built-in Rules
ruleEngine.registerRule(SyntaxErrorRule);
ruleEngine.registerRule(PythonUnusedVariableRule);
ruleEngine.registerRule(PythonMutableDefaultArgumentRule);
ruleEngine.registerRule(PythonUnreachableCodeRule);
ruleEngine.registerRule(HardcodedSecretRule);
ruleEngine.registerRule(PerformanceLoopRule);
ruleEngine.registerRule(DependencyVulnerabilityRule);
ruleEngine.registerRule(CppUnsafeFunctionsRule);

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

let workspaceRoot: string | null = null;

function loadCustomRules() {
  if (workspaceRoot) {
    const analyzerJsonPath = path.join(workspaceRoot, '.analyzer.json');
    if (fs.existsSync(analyzerJsonPath)) {
      try {
        const content = fs.readFileSync(analyzerJsonPath, 'utf8');
        const rules = JSON.parse(content);
        if (Array.isArray(rules)) {
          ruleEngine.setCustomRules(rules);
          return;
        }
      } catch (e) {
        connection.console.error(`Failed to parse .analyzer.json: ${e}`);
      }
    }
  }

  // Fallback to dashboard's rules.json
  const dashboardRulesPath = path.resolve(__dirname, '..', '..', 'dashboard', 'api', 'rules.json');
  if (fs.existsSync(dashboardRulesPath)) {
    try {
      const content = fs.readFileSync(dashboardRulesPath, 'utf8');
      const rules = JSON.parse(content);
      if (Array.isArray(rules)) {
        ruleEngine.setCustomRules(rules);
        return;
      }
    } catch (e) {
      // ignore
    }
  }

  ruleEngine.setCustomRules([]);
}

let hasConfigurationCapability = false;
let backendDebounceTimers: Map<string, NodeJS.Timeout> = new Map();

import { handleHover } from './providers/HoverProvider';
import { handleCodeAction } from './providers/CodeActionProvider';
import { aiService } from './ai/AIService';

connection.onInitialize(async (params: InitializeParams) => {
  const capabilities = params.capabilities;

  hasConfigurationCapability = !!(
    capabilities.workspace && !!capabilities.workspace.configuration
  );

  workspaceRoot = params.rootUri ? fileURLToPath(params.rootUri) : null;

  await ParserManager.initialize();

  loadCustomRules();

  const result: InitializeResult = {
    capabilities: {
      textDocumentSync: TextDocumentSyncKind.Incremental,
      hoverProvider: true,
      codeActionProvider: true,
      executeCommandProvider: {
        commands: ['omni.generateDocstring', 'omni.aiFix']
      }
    }
  };
  return result;
});

connection.onInitialized(() => {
  if (hasConfigurationCapability) {
    connection.client.register(DidChangeConfigurationNotification.type, undefined);
  }
});

connection.onDidChangeWatchedFiles(_change => {
  loadCustomRules();
  documents.all().forEach(validateTextDocument);
});

connection.onHover((params) => handleHover(params, documents));
connection.onCodeAction((params) => handleCodeAction(params, documents));

connection.onExecuteCommand(async (params) => {
    if (params.command === 'omni.generateDocstring' && params.arguments) {
        const uri = params.arguments[0];
        const range = params.arguments[1];
        const document = documents.get(uri);
        if (document) {
            const text = document.getText(range);
            const docstring = await aiService.generateDocstring(text);
            if (docstring) {
                connection.workspace.applyEdit({
                    documentChanges: [{
                        textDocument: { uri: document.uri, version: null },
                        edits: [{ range: { start: range.start, end: range.start }, newText: docstring + '\n' }]
                    }]
                });
            }
        }
    } else if (params.command === 'omni.aiFix' && params.arguments) {
        const uri = params.arguments[0];
        const range = params.arguments[1];
        const issue = params.arguments[2];
        const document = documents.get(uri);
        if (document) {
            const text = document.getText(range);
            const fixed = await aiService.refactorSuggestion(text, issue);
            if (fixed) {
                connection.workspace.applyEdit({
                    documentChanges: [{
                        textDocument: { uri: document.uri, version: null },
                        edits: [{ range, newText: fixed }]
                    }]
                });
            }
        }
    }
});



interface OmniAnalyzerSettings {
  enableCloudAI: boolean;
  geminiApiKey: string;
  model: string;
}

const defaultSettings: OmniAnalyzerSettings = { enableCloudAI: false, geminiApiKey: '', model: 'gemini-2.5-flash' };
let globalSettings: OmniAnalyzerSettings = defaultSettings;
const documentSettings: Map<string, Thenable<OmniAnalyzerSettings>> = new Map();

connection.onDidChangeConfiguration(change => {
  if (hasConfigurationCapability) {
    documentSettings.clear();
  } else {
    globalSettings = <OmniAnalyzerSettings>((change.settings.omniAnalyzer || defaultSettings));
  }
  documents.all().forEach(validateTextDocument);
});

async function getDocumentSettings(resource: string): Promise<OmniAnalyzerSettings> {
  if (!hasConfigurationCapability) {
    return Promise.resolve(globalSettings);
  }
  let result = documentSettings.get(resource);
  if (!result) {
    result = connection.workspace.getConfiguration({
      scopeUri: resource,
      section: 'omniAnalyzer'
    });
    documentSettings.set(resource, result);
  }
  return await result;
}

documents.onDidClose(e => {
  documentSettings.delete(e.document.uri);
  documentManager.remove(e.document.uri);
});

documents.onDidChangeContent(change => {
  validateTextDocument(change.document);
});

async function validateTextDocument(textDocument: TextDocument): Promise<void> {
  const settings = await getDocumentSettings(textDocument.uri);
  aiService.updateConfiguration(settings.enableCloudAI, settings.geminiApiKey, settings.model);

  // 1. Parse Document & Run Fast Local Rules
  const tree = await documentManager.parse(textDocument);
  let localDiagnostics: any[] = [];
  if (tree) {
    localDiagnostics = ruleEngine.run(textDocument, tree);
  }
  
  // Clear any pending backend analysis for this document
  if (backendDebounceTimers.has(textDocument.uri)) {
    clearTimeout(backendDebounceTimers.get(textDocument.uri)!);
  }

  // Send local diagnostics immediately for fast feedback
  connection.sendDiagnostics({ uri: textDocument.uri, diagnostics: localDiagnostics });

  // 2. Schedule Deep Backend Analysis
  const timer = setTimeout(async () => {
    try {
      const code = textDocument.getText();
      const languageId = textDocument.languageId;
      
      const response = await fetch('http://127.0.0.1:8000/analyze/full', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language: languageId, enable_custom_rules: true })
      });
      
      if (response.ok) {
        const data: any = await response.json();
        const backendDiagnostics = data.findings.map((f: any) => {
          let severity = 2; // Warning
          if (f.severity === 'critical' || f.severity === 'error') severity = 1; // Error
          if (f.severity === 'info') severity = 3; // Information
          
          return {
            severity,
            range: {
              start: { line: Math.max(0, f.line - 1), character: 0 },
              end: { line: Math.max(0, f.line - 1), character: 100 }
            },
            message: `[${f.source}] ${f.message}`,
            source: 'OmniAnalyzer',
            code: f.rule_id
          };
        });
        
        // Merge and update
        connection.sendDiagnostics({ 
          uri: textDocument.uri, 
          diagnostics: [...localDiagnostics, ...backendDiagnostics] 
        });
      }
    } catch (e) {
      connection.console.warn(`Backend analysis failed: ${e}`);
    }
  }, 2000);
  
  backendDebounceTimers.set(textDocument.uri, timer);
}

documents.listen(connection);
connection.listen();
