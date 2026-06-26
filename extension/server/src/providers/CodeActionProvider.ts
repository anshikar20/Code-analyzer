import { CodeActionParams, CodeAction, Command, CodeActionKind, TextEdit } from 'vscode-languageserver/node';
import { aiService } from '../ai/AIService';
import { TextDocuments } from 'vscode-languageserver/node';
import { TextDocument } from 'vscode-languageserver-textdocument';

export async function handleCodeAction(params: CodeActionParams, documents: TextDocuments<TextDocument>): Promise<CodeAction[]> {
    const document = documents.get(params.textDocument.uri);
    if (!document) return [];

    const actions: CodeAction[] = [];

    // Add Generate Docstring Action
    const docstringAction: CodeAction = {
        title: '✨ Generate AI Docstring',
        kind: CodeActionKind.RefactorRewrite,
        command: Command.create('✨ Generate AI Docstring', 'omni.generateDocstring', params.textDocument.uri, params.range)
    };
    actions.push(docstringAction);

    // If there are diagnostics in the range, offer a refactor suggestion
    if (params.context.diagnostics.length > 0) {
        const diagnostic = params.context.diagnostics[0];
        const fixAction: CodeAction = {
            title: `✨ AI Fix: ${diagnostic.message}`,
            kind: CodeActionKind.QuickFix,
            command: Command.create(`✨ AI Fix`, 'omni.aiFix', params.textDocument.uri, params.range, diagnostic.message)
        };
        actions.push(fixAction);
    }

    return actions;
}
