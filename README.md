# Zhen AI Code Review

🤖 AI驱动的代码审查工具，使用 OpenAI 自动审查 PR 代码并发表中文评论。

[![GitHub Action](https://img.shields.io/badge/GitHub-Action-blue?logo=github)](https://github.com/zhenzhenxu/zhen-ai-codereview)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 特性

- 🔍 **自动代码审查**：PR 创建或更新时自动触发审查
- 🇨🇳 **中文支持**：默认输出中文审查结果
- 🔒 **安全检查**：检测 SQL 注入、XSS、命令注入等安全漏洞
- ⚡ **性能分析**：识别低效算法和性能问题
- 📝 **最佳实践**：检查代码质量和编码规范
- 🎯 **精准定位**：引用具体行号，提供代码修改示例

## 🚀 快速开始

### 1. 在你的项目中添加 Workflow

创建 `.github/workflows/code-review.yml` 文件：

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: zhenzhenxu/zhen-ai-codereview@main
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
```

### 2. 配置 Secret

在你的 GitHub 仓库中添加 Secret：

1. 进入仓库 → Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. Name: `OPENAI_API_KEY`
4. Value: 你的 OpenAI API Key

### 3. 完成！

现在每次创建或更新 PR 时，AI 会自动审查代码并发表评论。

## ⚙️ 配置选项

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `openai_api_key` | ✅ | - | OpenAI API Key |
| `github_token` | ❌ | 自动提供 | GitHub Token |
| `openai_model` | ❌ | `gpt-4o` | OpenAI 模型 |
| `language` | ❌ | `zh` | 输出语言：`zh`(中文) 或 `en`(英文) |
| `post_comment` | ❌ | `true` | 是否在 PR 上发表评论 |
| `exclude_patterns` | ❌ | `*.md,*.txt,...` | 排除的文件模式 |

### 完整配置示例

```yaml
- uses: zhenzhenxu/zhen-ai-codereview@main
  with:
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}
    openai_model: 'gpt-4o'
    language: 'zh'
    post_comment: 'true'
    exclude_patterns: '*.md,*.txt,*.json,*.lock'
```

## 📋 审查内容

AI 会从以下维度审查代码：

| 类别 | 检查内容 |
|------|----------|
| 🔴 **Bug与错误** | 逻辑错误、空指针、竞态条件、边界情况 |
| 🔴 **安全性** | SQL注入、XSS、认证问题、敏感数据泄露 |
| 🟡 **性能** | 低效算法、内存泄漏、不必要的计算 |
| 🔵 **代码质量** | 可读性、可维护性、命名规范、文档注释 |
| 🔵 **最佳实践** | 设计模式、SOLID原则、错误处理 |

## 📦 支持的语言

支持所有主流编程语言：

- Python, JavaScript, TypeScript
- Java, Go, Rust, C/C++
- Ruby, PHP, Swift, Kotlin
- Vue, React, Svelte
- 更多...

## 🖥️ 本地使用

除了 GitHub Action，你也可以在本地使用：

```bash
# 克隆项目
git clone https://github.com/zhenzhenxu/zhen-ai-codereview.git
cd zhen-ai-codereview

# 安装依赖
pip install -r requirements.txt

# 配置
export OPENAI_API_KEY="your-api-key"

# 审查本地文件
./zhen-review.sh review src/

# 审查 git 变更
./zhen-review.sh diff

# 审查暂存区
./zhen-review.sh staged
```

## 📄 示例审查结果

```markdown
## 🤖 AI Code Review

**PR:** 添加用户服务模块
**Files reviewed:** 3/5

### Summary
整体代码质量良好，但存在一些安全隐患需要修复...

### Detailed Review

#### 🔴 严重：SQL注入风险（第34行）
直接将用户输入拼接到SQL语句中，存在注入风险。

**建议修复：**
```python
# 使用参数化查询
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📜 License

MIT License
