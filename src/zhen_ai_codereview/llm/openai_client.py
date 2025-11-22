"""
OpenAI API client for code review
"""

from typing import Optional

from openai import OpenAI

from ..config import OpenAIConfig


class OpenAIClient:
    """OpenAI API client wrapper for code review"""

    SYSTEM_PROMPT = """你是一位资深的代码审查专家，精通软件工程最佳实践、安全性和性能优化。

你的任务是审查代码变更，并提供建设性的、可操作的反馈。请用中文输出所有审查结果。

审查重点：
1. **Bug与错误**：逻辑错误、空指针问题、竞态条件、边界情况
2. **安全性**：SQL注入、XSS、认证问题、敏感数据泄露
3. **性能**：低效算法、内存泄漏、不必要的计算
4. **代码质量**：可读性、可维护性、命名规范、文档注释
5. **最佳实践**：设计模式、SOLID原则、错误处理

输出格式要求：
- 尽可能具体，引用行号
- 提供改进建议的代码示例
- 按严重程度分类：🔴 严重、🟡 警告、🔵 建议
- 保持建设性和专业性
- 如果代码写得好，也要指出优点

请用Markdown格式输出审查结果，全部使用中文。"""

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

        prompt = f"""基于以下各文件的审查结果，提供一个简洁的总体摘要：

{review_text}

请提供：
1. 整体代码质量评估
2. 发现的最严重问题（如有）
3. 关键改进建议
4. 代码的优点
"""

        messages = [
            {"role": "system", "content": "你是一位资深代码审查专家，正在提供代码审查的总结报告。请用中文输出。"},
            {"role": "user", "content": prompt},
        ]

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=2048,
            temperature=0.1,
        )

        return response.choices[0].message.content or ""
