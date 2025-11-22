#!/usr/bin/env python3
"""
GitHub Action 入口脚本 - AI代码审查
"""

import json
import os
import sys
import fnmatch

from openai import OpenAI
from github import Github


# 中文 Prompt
SYSTEM_PROMPT_ZH = """你是一位资深的代码审查专家，精通软件工程最佳实践、安全性和性能优化。

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

# 英文 Prompt
SYSTEM_PROMPT_EN = """You are an expert code reviewer with deep knowledge of software engineering best practices, security, and performance optimization.

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

SUMMARY_PROMPT_ZH = "你是一位资深代码审查专家，正在提供代码审查的总结报告。请用中文输出。"
SUMMARY_PROMPT_EN = "You are a senior code reviewer providing an executive summary of code review findings."


def get_system_prompt(language: str) -> str:
    return SYSTEM_PROMPT_ZH if language == 'zh' else SYSTEM_PROMPT_EN


def get_summary_prompt(language: str) -> str:
    return SUMMARY_PROMPT_ZH if language == 'zh' else SUMMARY_PROMPT_EN


def should_review_file(filename: str, exclude_patterns: list) -> bool:
    """检查文件是否应该被审查"""
    # 代码文件扩展名
    code_extensions = [
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
        '.cpp', '.c', '.h', '.hpp', '.rb', '.php', '.swift', '.kt',
        '.scala', '.vue', '.svelte', '.cs', '.m', '.mm'
    ]

    # 检查是否是代码文件
    is_code_file = any(filename.endswith(ext) for ext in code_extensions)
    if not is_code_file:
        return False

    # 检查排除模式
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(filename, pattern.strip()):
            return False

    return True


def review_code(client: OpenAI, model: str, code: str, filename: str, language: str) -> str:
    """使用 OpenAI 审查代码"""
    prompt = f"""请审查以下代码变更（diff格式），文件：`{filename}`

```diff
{code}
```
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": get_system_prompt(language)},
            {"role": "user", "content": prompt}
        ],
        max_tokens=4096,
        temperature=0.1
    )

    return response.choices[0].message.content or ""


def summarize_reviews(client: OpenAI, model: str, reviews: list, language: str) -> str:
    """生成审查总结"""
    review_text = "\n\n".join(
        f"## {r['filename']}\n{r['feedback']}" for r in reviews
    )

    if language == 'zh':
        prompt = f"""基于以下各文件的审查结果，提供一个简洁的总体摘要：

{review_text}

请提供：
1. 整体代码质量评估
2. 发现的最严重问题（如有）
3. 关键改进建议
4. 代码的优点
"""
    else:
        prompt = f"""Based on the following individual file reviews, provide a concise overall summary:

{review_text}

Please provide:
1. Overall code quality assessment
2. Most critical issues found (if any)
3. Key recommendations
4. Positive aspects of the code
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": get_summary_prompt(language)},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2048,
        temperature=0.1
    )

    return response.choices[0].message.content or ""


def format_comment(reviews: list, summary: str, pr_title: str, reviewed_count: int, total_count: int) -> str:
    """格式化 PR 评论"""
    lines = [
        "## 🤖 AI Code Review",
        "",
        f"**PR:** {pr_title}",
        f"**Files reviewed:** {reviewed_count}/{total_count}",
        "",
        "---",
        "",
        "### Summary",
        "",
        summary,
        "",
        "---",
        "",
        "### Detailed Review",
        ""
    ]

    for r in reviews:
        lines.append(f"<details>")
        lines.append(f"<summary><strong>{r['filename']}</strong></summary>")
        lines.append("")
        lines.append(r['feedback'])
        lines.append("")
        lines.append("</details>")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by [zhen-ai-codereview](https://github.com/zhenzhenxu/zhen-ai-codereview)*")

    return "\n".join(lines)


def main():
    # 读取环境变量
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    github_token = os.environ.get('GITHUB_TOKEN')
    model = os.environ.get('OPENAI_MODEL', 'gpt-4o')
    language = os.environ.get('REVIEW_LANGUAGE', 'zh')
    post_comment = os.environ.get('POST_COMMENT', 'true').lower() == 'true'
    exclude_patterns = os.environ.get('EXCLUDE_PATTERNS', '').split(',')
    event_path = os.environ.get('GITHUB_EVENT_PATH', '')
    repo_name = os.environ.get('GITHUB_REPOSITORY', '')

    if not openai_api_key:
        print("❌ Error: OPENAI_API_KEY is required")
        sys.exit(1)

    if not github_token:
        print("❌ Error: GITHUB_TOKEN is required")
        sys.exit(1)

    # 读取 PR 事件信息
    if not event_path or not os.path.exists(event_path):
        print("❌ Error: Could not find GitHub event data")
        sys.exit(1)

    with open(event_path) as f:
        event = json.load(f)

    pr_data = event.get('pull_request', {})
    pr_number = pr_data.get('number')
    pr_title = pr_data.get('title', 'Unknown PR')

    if not pr_number:
        print("❌ Error: Could not determine PR number")
        sys.exit(1)

    print(f"🔍 Reviewing PR #{pr_number}: {pr_title}")
    print(f"📦 Repository: {repo_name}")
    print(f"🌐 Language: {language}")
    print(f"🤖 Model: {model}")

    # 初始化客户端
    openai_client = OpenAI(api_key=openai_api_key)
    github_client = Github(github_token)

    # 获取 PR 文件
    repo = github_client.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    files = list(pr.get_files())

    print(f"📄 Total files changed: {len(files)}")

    # 筛选需要审查的文件
    files_to_review = []
    for f in files:
        if f.patch and should_review_file(f.filename, exclude_patterns):
            files_to_review.append(f)

    print(f"📝 Files to review: {len(files_to_review)}")

    if not files_to_review:
        print("✅ No code files to review")
        return

    # 审查每个文件
    reviews = []
    for f in files_to_review:
        print(f"  → Reviewing: {f.filename}")
        try:
            feedback = review_code(
                openai_client, model,
                f.patch, f.filename, language
            )
            reviews.append({
                'filename': f.filename,
                'feedback': feedback
            })
        except Exception as e:
            print(f"  ⚠️ Error reviewing {f.filename}: {e}")

    if not reviews:
        print("❌ No files were successfully reviewed")
        return

    # 生成总结
    print("📊 Generating summary...")
    summary = summarize_reviews(openai_client, model, reviews, language)

    # 格式化评论
    comment_body = format_comment(
        reviews, summary, pr_title,
        len(reviews), len(files)
    )

    # 发表评论
    if post_comment:
        print("💬 Posting review comment...")
        pr.create_issue_comment(comment_body)
        print("✅ Review comment posted successfully!")
    else:
        print("📋 Review complete (comment posting disabled)")
        print("\n" + "="*50)
        print(comment_body)
        print("="*50)

    print(f"\n✅ Done! Reviewed {len(reviews)}/{len(files)} files")


if __name__ == '__main__':
    main()
