import { RuleEngine, SyntaxErrorRule } from '../RuleEngine';
import { DiagnosticSeverity } from 'vscode-languageserver/node';

describe('RuleEngine', () => {
    let ruleEngine: RuleEngine;
    
    beforeEach(() => {
        ruleEngine = new RuleEngine();
    });

    it('should register and execute rules correctly', () => {
        const mockRule = {
            id: 'mock-rule',
            name: 'Mock',
            severity: DiagnosticSeverity.Warning,
            languages: ['all'],
            analyze: jest.fn()
        };
        ruleEngine.registerRule(mockRule);
        
        const mockDocument: any = { languageId: 'python', uri: 'file://test.py', getText: () => '' };
        const mockTree: any = {};

        ruleEngine.run(mockDocument, mockTree);
        
        expect(mockRule.analyze).toHaveBeenCalled();
    });

    it('should load and execute custom regex rules correctly', () => {
        const customRules = [
            {
                id: 'custom-print',
                name: 'No print statements',
                severity: 'Warning',
                languages: ['python'],
                enabled: true,
                regex: 'print\\s*\\(',
                description: 'Do not use print in production'
            }
        ];
        
        ruleEngine.setCustomRules(customRules);
        
        const mockDocument: any = {
            languageId: 'python',
            uri: 'file://test.py',
            getText: () => 'print("hello")',
            positionAt: (offset: number) => {
                return { line: 0, character: offset };
            }
        };
        const mockTree: any = {};
        
        const diagnostics = ruleEngine.run(mockDocument, mockTree);
        
        expect(diagnostics.length).toBe(1);
        expect(diagnostics[0].message).toBe('Do not use print in production');
        expect(diagnostics[0].severity).toBe(DiagnosticSeverity.Warning);
        expect(diagnostics[0].range.start.character).toBe(0);
        expect(diagnostics[0].range.end.character).toBe(6); // 'print(' is 6 chars
    });
});
