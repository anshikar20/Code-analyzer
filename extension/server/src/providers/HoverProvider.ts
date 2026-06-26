import { HoverParams, Hover, MarkupKind } from 'vscode-languageserver/node';
import { aiService } from '../ai/AIService';
import { TextDocuments } from 'vscode-languageserver/node';
import { TextDocument } from 'vscode-languageserver-textdocument';

const hoverCache = new Map<string, string>();
let hoverTimer: NodeJS.Timeout | null = null;

export async function handleHover(params: HoverParams, documents: TextDocuments<TextDocument>): Promise<Hover | null> {
    const document = documents.get(params.textDocument.uri);
    if (!document) return null;

    const text = document.getText();
    const lines = text.split('\n');
    const line = lines[params.position.line];

    if (!line || line.trim().length === 0) return null;
    const cacheKey = line.trim();

    if (hoverCache.has(cacheKey)) {
        return {
            contents: {
                kind: MarkupKind.Markdown,
                value: `**AI Explanation:**\n\n${hoverCache.get(cacheKey)}`
            }
        };
    }

    return new Promise((resolve) => {
        if (hoverTimer) clearTimeout(hoverTimer);
        
        hoverTimer = setTimeout(async () => {
            const explanation = await aiService.explainCode(line);
            if (explanation) {
                hoverCache.set(cacheKey, explanation);
                resolve({
                    contents: {
                        kind: MarkupKind.Markdown,
                        value: `**AI Explanation:**\n\n${explanation}`
                    }
                });
            } else {
                resolve(null);
            }
        }, 1000); // 1s debounce
    });
}
