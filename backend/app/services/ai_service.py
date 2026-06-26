"""
Gemini AI integration service.

Provides code review, explanation, docstring generation, refactoring suggestions,
and developer Q&A using Gemini API.

Uses the official google-generativeai SDK.
"""

import logging
from ..config import get_settings

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    _gemini_available = True
except ImportError:
    _gemini_available = False
    logger.warning("google-generativeai not installed. AI features will be disabled.")


# ─── Prompt Templates ──────────────────────────────────

PROMPTS = {
    "review": (
        "You are a senior software engineer performing a code review.\n"
        "Analyze the following {language} code and provide:\n"
        "1. **Bug Detection**: Identify any bugs or logical errors\n"
        "2. **Security Issues**: Flag potential security vulnerabilities\n"
        "3. **Performance**: Note any performance concerns\n"
        "4. **Code Quality**: Suggest readability and maintainability improvements\n"
        "5. **Best Practices**: Recommend industry best practices\n\n"
        "Format your response in clean, professional markdown. "
        "Be constructive and provide specific code suggestions.\n\n"
        "```{language}\n{code}\n```"
    ),
    "explain": (
        "Explain the following {language} code clearly and concisely. "
        "Describe what each part does, the overall purpose, and any important "
        "patterns or techniques used.\n\n"
        "```{language}\n{code}\n```"
    ),
    "refactor": (
        "Refactor the following {language} code to improve readability, "
        "performance, and maintainability. Return ONLY the refactored code "
        "with brief comments explaining the changes. "
        "Do not include markdown code fences.\n\n{code}"
    ),
    "docstring": (
        "Generate a comprehensive docstring for the following {language} "
        "function/class. Follow the standard docstring convention for {language}. "
        "Include parameters, return values, and a brief description. "
        "Return ONLY the docstring, nothing else.\n\n{code}"
    ),
    "ask": (
        "Context: The developer is working on the following {language} code:\n\n"
        "```{language}\n{code}\n```\n\n"
        "Question: {question}\n\n"
        "Provide a clear, actionable answer with code examples if appropriate."
    ),
}


class AIService:
    """Service for AI-powered code analysis using Gemini."""

    def __init__(self):
        self._configured = False

    def _ensure_configured(self) -> bool:
        """Initialize Gemini client on first use."""
        if self._configured:
            return True

        if not _gemini_available:
            logger.warning("google-generativeai SDK not available.")
            self._configured = True
            return False

        settings = get_settings()
        if not settings.gemini_api_key:
            logger.info("No Gemini API key configured. AI features disabled.")
            self._configured = True
            return False

        try:
            genai.configure(api_key=settings.gemini_api_key)
            self._configured = True
            logger.info(f"Gemini configured: primary={settings.gemini_primary_model}, "
                        f"fallback={settings.gemini_fallback_model}")
            return True
        except Exception as e:
            logger.error(f"Failed to configure Gemini: {e}")
            self._configured = True
            return False

    async def _generate(self, prompt: str) -> tuple[str, str]:
        """
        Generate content with primary model, falling back to smaller model on error.

        Returns:
            (response_text, model_name_used)
        """
        if not self._ensure_configured() or not _gemini_available:
            return (
                "### AI Features Unavailable\n\n"
                "Gemini API key is not configured. Set the `ANALYZER_GEMINI_API_KEY` "
                "environment variable or add it to your `.env` file.",
                ""
            )

        settings = get_settings()

        # Try primary model
        try:
            model = genai.GenerativeModel(settings.gemini_primary_model)
            response = await model.generate_content_async(prompt)
            return response.text, settings.gemini_primary_model
        except Exception as e:
            logger.warning(f"Primary model failed ({settings.gemini_primary_model}): {e}")

        # Fallback to smaller model
        try:
            model = genai.GenerativeModel(settings.gemini_fallback_model)
            response = await model.generate_content_async(prompt)
            return response.text, settings.gemini_fallback_model
        except Exception as e:
            logger.error(f"Fallback model also failed: {e}")
            return f"### AI Review Failed\n\nError: {str(e)}", ""

    async def review_code(self, code: str, language: str = "python") -> tuple[str, str]:
        """Perform comprehensive AI code review."""
        prompt = PROMPTS["review"].format(language=language, code=code)
        return await self._generate(prompt)

    async def explain_code(self, code: str, language: str = "python") -> tuple[str, str]:
        """Explain what the code does."""
        prompt = PROMPTS["explain"].format(language=language, code=code)
        return await self._generate(prompt)

    async def refactor_code(self, code: str, language: str = "python") -> tuple[str, str]:
        """Suggest refactored version of the code."""
        prompt = PROMPTS["refactor"].format(language=language, code=code)
        return await self._generate(prompt)

    async def generate_docstring(self, code: str, language: str = "python") -> tuple[str, str]:
        """Generate a docstring for the given code."""
        prompt = PROMPTS["docstring"].format(language=language, code=code)
        return await self._generate(prompt)

    async def ask_question(
        self, code: str, question: str, language: str = "python"
    ) -> tuple[str, str]:
        """Answer a developer question about the code."""
        prompt = PROMPTS["ask"].format(language=language, code=code, question=question)
        return await self._generate(prompt)

    async def process_request(
        self, code: str, language: str, prompt_type: str, question: str | None = None
    ) -> tuple[str, str]:
        """Route to the correct AI function based on prompt_type."""
        handlers = {
            "review": self.review_code,
            "explain": self.explain_code,
            "refactor": self.refactor_code,
            "docstring": self.generate_docstring,
        }

        if prompt_type == "ask" and question:
            return await self.ask_question(code, question, language)

        handler = handlers.get(prompt_type)
        if handler:
            return await handler(code, language)

        return "Invalid prompt type.", ""


# Singleton
ai_service = AIService()
