"""
GitHub API client for PR review integration
"""

from dataclasses import dataclass
from typing import Optional

from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository

from ..config import GitHubConfig


@dataclass
class PRFile:
    """Represents a file changed in a PR"""
    filename: str
    status: str  # added, modified, removed, renamed
    patch: Optional[str]  # diff content
    additions: int
    deletions: int
    content: Optional[str] = None  # full file content


@dataclass
class PRInfo:
    """Pull request information"""
    number: int
    title: str
    body: Optional[str]
    author: str
    base_branch: str
    head_branch: str
    files: list[PRFile]


class GitHubClient:
    """GitHub API client for PR operations"""

    def __init__(self, config: GitHubConfig):
        self.config = config
        self.github = Github(config.token, base_url=config.api_url)

    def get_repo(self, repo_full_name: str) -> Repository:
        """Get repository by full name (owner/repo)"""
        return self.github.get_repo(repo_full_name)

    def get_pr(self, repo_full_name: str, pr_number: int) -> PRInfo:
        """
        Get pull request information including changed files

        Args:
            repo_full_name: Repository full name (e.g., "owner/repo")
            pr_number: Pull request number

        Returns:
            PRInfo object with PR details and files
        """
        repo = self.get_repo(repo_full_name)
        pr: PullRequest = repo.get_pull(pr_number)

        files = []
        for file in pr.get_files():
            pr_file = PRFile(
                filename=file.filename,
                status=file.status,
                patch=file.patch,
                additions=file.additions,
                deletions=file.deletions,
            )
            files.append(pr_file)

        return PRInfo(
            number=pr.number,
            title=pr.title,
            body=pr.body,
            author=pr.user.login,
            base_branch=pr.base.ref,
            head_branch=pr.head.ref,
            files=files,
        )

    def get_file_content(
        self, repo_full_name: str, file_path: str, ref: str
    ) -> Optional[str]:
        """
        Get file content from repository

        Args:
            repo_full_name: Repository full name
            file_path: Path to file in repository
            ref: Git reference (branch, tag, commit SHA)

        Returns:
            File content as string, or None if not found
        """
        try:
            repo = self.get_repo(repo_full_name)
            content = repo.get_contents(file_path, ref=ref)
            if isinstance(content, list):
                return None  # It's a directory
            return content.decoded_content.decode("utf-8")
        except Exception:
            return None

    def create_review_comment(
        self,
        repo_full_name: str,
        pr_number: int,
        body: str,
    ) -> None:
        """
        Create a general comment on a PR

        Args:
            repo_full_name: Repository full name
            pr_number: Pull request number
            body: Comment body (markdown)
        """
        repo = self.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        pr.create_issue_comment(body)

    def create_review(
        self,
        repo_full_name: str,
        pr_number: int,
        body: str,
        event: str = "COMMENT",
    ) -> None:
        """
        Create a PR review

        Args:
            repo_full_name: Repository full name
            pr_number: Pull request number
            body: Review body (markdown)
            event: Review event type (COMMENT, APPROVE, REQUEST_CHANGES)
        """
        repo = self.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        pr.create_review(body=body, event=event)
