import Parser from 'web-tree-sitter';
import * as path from 'path';
import * as fs from 'fs';

export class ParserManager {
  private static isInitialized = false;
  private static parsers: Map<string, Parser> = new Map();

  static async initialize() {
    if (this.isInitialized) return;
    await Parser.init({
      locateFile(scriptName: string, prefix: string) {
        if (scriptName === 'tree-sitter.wasm') {
          return path.join(__dirname, '..', '..', 'node_modules', 'web-tree-sitter', 'tree-sitter.wasm');
        }
        return prefix + scriptName;
      }
    });
    this.isInitialized = true;
  }

  static async getParser(languageId: string): Promise<Parser | null> {
    if (!this.isInitialized) {
      await this.initialize();
    }
    
    if (this.parsers.has(languageId)) {
      return this.parsers.get(languageId)!;
    }

    let wasmPath = '';
    const wasmsDir = path.join(__dirname, '..', '..', 'node_modules', 'tree-sitter-wasms', 'out');
    
    switch (languageId) {
      case 'python':
        wasmPath = path.join(wasmsDir, 'tree-sitter-python.wasm');
        break;
      case 'java':
        wasmPath = path.join(wasmsDir, 'tree-sitter-java.wasm');
        break;
      case 'cpp':
      case 'c':
        wasmPath = path.join(wasmsDir, 'tree-sitter-cpp.wasm');
        break;
      default:
        return null;
    }

    if (!fs.existsSync(wasmPath)) {
      console.warn(`WASM file not found for ${languageId} at ${wasmPath}`);
      return null;
    }

    try {
      const language = await Parser.Language.load(wasmPath);
      const parser = new Parser();
      parser.setLanguage(language);
      this.parsers.set(languageId, parser);
      return parser;
    } catch (e) {
      console.error(`Failed to load parser for ${languageId}:`, e);
      return null;
    }
  }
}
