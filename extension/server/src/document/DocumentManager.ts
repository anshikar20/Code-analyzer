import { TextDocument } from 'vscode-languageserver-textdocument';
import { ParserManager } from '../parser/ParserManager';
import Parser from 'web-tree-sitter';

export class DocumentManager {
  private trees: Map<string, Parser.Tree> = new Map();

  public async parse(document: TextDocument): Promise<Parser.Tree | null> {
    const parser = await ParserManager.getParser(document.languageId);
    if (!parser) return null;

    const text = document.getText();
    const newTree = parser.parse(text);
    
    this.trees.set(document.uri, newTree);
    return newTree;
  }

  public getTree(uri: string): Parser.Tree | undefined {
    return this.trees.get(uri);
  }

  public remove(uri: string) {
    this.trees.delete(uri);
  }
}
