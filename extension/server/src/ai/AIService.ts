export class AIService {
    private apiKey: string | null = null;
    private model: string = "gemini-2.5-flash";
    private isEnabled = false;

    public updateConfiguration(enabled: boolean, apiKey: string, modelName = "gemini-2.5-flash") {
        this.isEnabled = enabled;
        if (enabled && apiKey) {
            this.apiKey = apiKey;
            this.model = modelName;
        } else {
            this.apiKey = null;
        }
    }

    private async _generateWithFallback(prompt: string): Promise<string> {
        if (!this.isEnabled || !this.apiKey) throw new Error("AI disabled");
        
        try {
            const headers: Record<string, string> = {
                "Content-Type": "application/json"
            };
            if (this.apiKey.startsWith("AIza")) {
                headers["x-goog-api-key"] = this.apiKey;
            } else {
                headers["Authorization"] = `Bearer ${this.apiKey}`;
            }

            const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${this.model}:generateContent`, {
                method: "POST",
                headers: headers,
                body: JSON.stringify({
                    contents: [{ parts: [{ text: prompt }] }]
                })
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Gemini API error: ${response.status} ${errorText}`);
            }
            
            const data: any = await response.json();
            
            if (data.candidates && data.candidates.length > 0 && data.candidates[0].content && data.candidates[0].content.parts.length > 0) {
                return data.candidates[0].content.parts[0].text;
            } else {
                throw new Error("Unexpected response format from Gemini API");
            }
        } catch (e: any) {
            throw e;
        }
    }

    public async explainCode(code: string): Promise<string> {
        if (!this.isEnabled || !this.apiKey) return "";
        try {
            const prompt = `Explain the following source code concisely:\n\n${code}`;
            const resultText = await this._generateWithFallback(prompt);
            return resultText;
        } catch(e: any) {
            return `AI Explanation failed: ${e.message}`;
        }
    }

    public async generateDocstring(code: string): Promise<string> {
        if (!this.isEnabled || !this.apiKey) return "";
        try {
            const prompt = `Generate a standard docstring for the following function/class. Return ONLY the docstring, no other text:\n\n${code}`;
            const resultText = await this._generateWithFallback(prompt);
            return resultText.trim();
        } catch(e) {
            return "";
        }
    }

    public async refactorSuggestion(code: string, issue: string): Promise<string> {
        if (!this.isEnabled || !this.apiKey) return "AI disabled.";
        try {
            const prompt = `Refactor the following code to fix this issue: ${issue}\n\n${code}\n\nReturn ONLY the refactored code without markdown formatting.`;
            const resultText = await this._generateWithFallback(prompt);
            return resultText.replace(/```.*\n/g, '').replace(/```/g, '').trim();
        } catch(e) {
            return code;
        }
    }

    public async reviewCode(code: string): Promise<string> {
        if (!this.isEnabled || !this.apiKey) {
            return "### AI Review Unavailable\n\nCloud AI features are disabled or API key is missing. Please check your extension settings and supply a valid Gemini API Key.";
        }
        try {
            const prompt = `Perform a comprehensive code review of the following source code. Identify bugs, performance bottlenecks, security risks, and readability improvements. Provide constructive suggestions and code refactorings where appropriate. Respond in clean, professional markdown formatting:\n\n${code}`;
            const resultText = await this._generateWithFallback(prompt);
            return resultText;
        } catch (e: any) {
            return `### AI Review Failed\n\nError: ${e.message}`;
        }
    }
}

export const aiService = new AIService();
