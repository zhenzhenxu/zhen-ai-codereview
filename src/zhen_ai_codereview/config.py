"""
Configuration management for Zhen AI Code Review
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv


@dataclass
class OpenAIConfig:
    """OpenAI API configuration"""
    api_key: str
    model: str = "gpt-4o"
    api_base: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.1


@dataclass
class GitHubConfig:
    """GitHub API configuration"""
    token: str
    api_url: str = "https://api.github.com"


@dataclass
class ReviewConfig:
    """Code review configuration"""
    # File patterns to include
    include_patterns: list[str] = field(default_factory=lambda: [
        "*.py", "*.js", "*.ts", "*.jsx", "*.tsx",
        "*.java", "*.go", "*.rs", "*.cpp", "*.c",
        "*.rb", "*.php", "*.swift", "*.kt"
    ])
    # File patterns to exclude
    exclude_patterns: list[str] = field(default_factory=lambda: [
        "*.min.js", "*.bundle.js", "package-lock.json",
        "yarn.lock", "*.lock", "*.generated.*"
    ])
    # Maximum file size to review (in bytes)
    max_file_size: int = 100000
    # Review focus areas
    focus_areas: list[str] = field(default_factory=lambda: [
        "bugs", "security", "performance", "readability", "best_practices"
    ])


@dataclass
class Config:
    """Main configuration"""
    openai: OpenAIConfig
    github: Optional[GitHubConfig] = None
    review: ReviewConfig = field(default_factory=ReviewConfig)


def load_config() -> Config:
    """Load configuration from environment variables"""
    load_dotenv()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    openai_config = OpenAIConfig(
        api_key=openai_api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        api_base=os.getenv("OPENAI_API_BASE"),
    )

    github_token = os.getenv("GITHUB_TOKEN")
    github_config = None
    if github_token:
        github_config = GitHubConfig(token=github_token)

    return Config(
        openai=openai_config,
        github=github_config,
    )
