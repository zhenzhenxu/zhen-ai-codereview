"""
OpenAI API client for code review
"""

from typing import Optional

from openai import OpenAI

from ..config import OpenAIConfig


class OpenAIClient:
    """OpenAI API client wrapper for code review"""

    SYSTEM_PROMPT = """You are an expert code reviewer with deep knowledge of software engineering best practices, security, and performance optimization.

Your task is to review code changes and provide constructive, actionable feedback.

Review Focus Areas:
1. **Bugs & Errors**: Logic errors, null pointer issues, race conditions, edge cases
2. **Security**: SQL injection, XSS, authentication issues, sensitive data exposure
3. **Performance**: Inefficient algorithms, memory leaks, unnecessary computations
4. **Code Quality**: Readability, maintainability, naming conventions, documentation
5. **Best Practices**: Design patterns, SOLID principles, error handling

Response Format:
- Be specific and reference line numbers when possible
- Provide code examples for suggested improvements
- Categorize issues by severity: 🔴 Critical, 🟡 Warning, 🔵 Suggestion
- Be constructive and professional
- If the code looks good, acknowledge what's done well

Output your review in Markdown format."""

    def __init__(self, config: OpenAIConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_base,
        )

    def review_code(
        self,
        code: str,
        filename: str,
        context: Optional[str] = None,
        diff_mode: bool = False,
    ) -> str:
        """
        Review code and return feedback

        Args:
            code: The code content to review
            filename: Name of the file being reviewed
            context: Additional context about the code
            diff_mode: Whether the code is a diff (for PR reviews)

        Returns:
            Review feedback as markdown string
        """
        if diff_mode:
            user_prompt = f"""Please review the following code diff for file `{filename}`:

```diff
{code}
```
"""
        else:
            user_prompt = f"""Please review the following code from file `{filename}`:

```
{code}
```
"""

        if context:
            user_prompt += f"\n\nAdditional context:\n{context}"

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )

        return response.choices[0].message.content or ""

    def summarize_reviews(self, reviews: list[dict]) -> str:
        """
        Summarize multiple file reviews into an overall summary

        Args:
            reviews: List of review results with filename and feedback

        Returns:
            Summary as markdown string
        """
        review_text = "\n\n".join(
            f"## {r['filename']}\n{r['feedback']}" for r in reviews
        )

        prompt = f"""Based on the following individual file reviews, provide a concise overall summary:

{review_text}

Please provide:
1. Overall code quality assessment
2. Most critical issues found (if any)
3. Key recommendations
4. Positive aspects of the code
"""

        messages = [
            {"role": "system", "content": "You are a senior code reviewer providing an executive summary of code review findings."},
            {"role": "user", "content": prompt},
        ]

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=2048,
            temperature=0.1,
        )

        return response.choices[0].message.content or ""
