# Zhen AI Code Review

AI-powered code review agent using OpenAI. Supports local files, git changes, and GitHub pull requests.

## Features

- **Local Code Review**: Review files and directories on your machine
- **Git Integration**: Review changes between commits or staged changes
- **GitHub PR Review**: Automatically review pull requests and post comments
- **GitHub Action**: Easy integration into CI/CD pipelines
- **Rich Output**: Beautiful terminal output with syntax highlighting

## Installation

```bash
# Clone the repository
git clone https://github.com/zhenzhen/zhen-ai-codereview.git
cd zhen-ai-codereview

# Install with pip
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

## Configuration

Create a `.env` file or set environment variables:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
OPENAI_MODEL=gpt-4o              # Default model
GITHUB_TOKEN=your_github_token    # Required for PR review
```

## Usage

### CLI Commands

#### Review Local Files

```bash
# Review a single file
zhen-review review main.py

# Review multiple files
zhen-review review src/app.py src/utils.py

# Review a directory
zhen-review review src/

# Review directory non-recursively
zhen-review review src/ --no-recursive
```

#### Review Git Changes

```bash
# Review changes from last commit
zhen-review diff

# Review changes between branches
zhen-review diff --base main --head feature-branch

# Review last 5 commits
zhen-review diff --base HEAD~5
```

#### Review Staged Changes (Pre-commit)

```bash
# Review staged changes before committing
zhen-review staged
```

#### Review GitHub Pull Request

```bash
# Review a PR (output to terminal)
zhen-review pr owner/repo 123

# Review and post comment to PR
zhen-review pr owner/repo 123 --comment
```

## GitHub Action

Add to your workflow (`.github/workflows/code-review.yml`):

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: AI Code Review
        uses: zhenzhen/zhen-ai-codereview@main
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
          post_comment: 'true'
```

### Action Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `openai_api_key` | Yes | - | OpenAI API key |
| `github_token` | Yes | - | GitHub token for posting comments |
| `openai_model` | No | `gpt-4o` | OpenAI model to use |
| `post_comment` | No | `true` | Post review as PR comment |

## Pre-commit Hook

Add AI review to your git workflow:

```bash
# .git/hooks/pre-commit
#!/bin/bash
zhen-review staged
```

Or use with [pre-commit](https://pre-commit.com/):

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ai-code-review
        name: AI Code Review
        entry: zhen-review staged
        language: system
        pass_filenames: false
```

## Docker

```bash
# Build image
docker build -t zhen-ai-codereview .

# Run review
docker run -e OPENAI_API_KEY=xxx -v $(pwd):/code zhen-ai-codereview review /code
```

## Supported Languages

- Python (`.py`)
- JavaScript/TypeScript (`.js`, `.ts`, `.jsx`, `.tsx`)
- Java (`.java`)
- Go (`.go`)
- Rust (`.rs`)
- C/C++ (`.c`, `.cpp`)
- Ruby (`.rb`)
- PHP (`.php`)
- Swift (`.swift`)
- Kotlin (`.kt`)

## Review Focus Areas

The AI reviewer checks for:

- **Bugs & Errors**: Logic errors, null pointers, edge cases
- **Security**: Injection attacks, authentication issues, data exposure
- **Performance**: Inefficient algorithms, memory leaks
- **Code Quality**: Readability, maintainability, documentation
- **Best Practices**: Design patterns, SOLID principles

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/ --fix

# Type checking
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
