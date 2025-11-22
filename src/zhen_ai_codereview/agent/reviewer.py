"""
Core Code Review Agent
"""

from dataclasses import dataclass
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import Config
from ..github import GitHubClient
from ..llm import OpenAIClient
from ..local import LocalScanner


@dataclass
class ReviewResult:
    """Result of a code review"""
    filename: str
    feedback: str
    status: str = "success"  # success, error, skipped


@dataclass
class ReviewReport:
    """Complete review report"""
    results: list[ReviewResult]
    summary: Optional[str] = None
    total_files: int = 0
    reviewed_files: int = 0
    skipped_files: int = 0


class CodeReviewAgent:
    """Main code review agent that orchestrates the review process"""

    def __init__(self, config: Config):
        self.config = config
        self.llm_client = OpenAIClient(config.openai)
        self.local_scanner = LocalScanner(config.review)
        self.github_client = None
        if config.github:
            self.github_client = GitHubClient(config.github)
        self.console = Console()

    def review_files(
        self,
        file_paths: list[str],
        show_progress: bool = True,
    ) -> ReviewReport:
        """
        Review specific local files

        Args:
            file_paths: List of file paths to review
            show_progress: Whether to show progress indicator

        Returns:
            ReviewReport with results
        """
        files = self.local_scanner.scan_files(file_paths)
        return self._review_file_list(files, show_progress)

    def review_directory(
        self,
        directory: str,
        recursive: bool = True,
        show_progress: bool = True,
    ) -> ReviewReport:
        """
        Review all code files in a directory

        Args:
            directory: Path to directory
            recursive: Whether to scan subdirectories
            show_progress: Whether to show progress indicator

        Returns:
            ReviewReport with results
        """
        files = self.local_scanner.scan_directory(directory, recursive)
        return self._review_file_list(files, show_progress)

    def review_git_changes(
        self,
        repo_path: str,
        base_ref: str = "HEAD~1",
        head_ref: str = "HEAD",
        show_progress: bool = True,
    ) -> ReviewReport:
        """
        Review git changes between two refs

        Args:
            repo_path: Path to git repository
            base_ref: Base reference
            head_ref: Head reference
            show_progress: Whether to show progress indicator

        Returns:
            ReviewReport with results
        """
        changes = self.local_scanner.get_git_changes(repo_path, base_ref, head_ref)
        return self._review_git_changes(changes, show_progress)

    def review_staged(
        self,
        repo_path: str,
        show_progress: bool = True,
    ) -> ReviewReport:
        """
        Review staged git changes

        Args:
            repo_path: Path to git repository
            show_progress: Whether to show progress indicator

        Returns:
            ReviewReport with results
        """
        changes = self.local_scanner.get_staged_changes(repo_path)
        return self._review_git_changes(changes, show_progress)

    def review_pr(
        self,
        repo_full_name: str,
        pr_number: int,
        post_comment: bool = False,
        show_progress: bool = True,
    ) -> ReviewReport:
        """
        Review a GitHub pull request

        Args:
            repo_full_name: Repository full name (owner/repo)
            pr_number: Pull request number
            post_comment: Whether to post review as PR comment
            show_progress: Whether to show progress indicator

        Returns:
            ReviewReport with results
        """
        if not self.github_client:
            raise ValueError("GitHub configuration is required for PR review")

        pr_info = self.github_client.get_pr(repo_full_name, pr_number)
        results = []
        reviewed = 0
        skipped = 0

        files_to_review = [
            f for f in pr_info.files
            if f.patch and f.status != "removed"
        ]

        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task(
                    f"Reviewing PR #{pr_number}...",
                    total=len(files_to_review)
                )

                for pr_file in files_to_review:
                    progress.update(task, description=f"Reviewing {pr_file.filename}...")

                    try:
                        feedback = self.llm_client.review_code(
                            code=pr_file.patch,
                            filename=pr_file.filename,
                            context=f"PR: {pr_info.title}\n{pr_info.body or ''}",
                            diff_mode=True,
                        )
                        results.append(ReviewResult(
                            filename=pr_file.filename,
                            feedback=feedback,
                        ))
                        reviewed += 1
                    except Exception as e:
                        results.append(ReviewResult(
                            filename=pr_file.filename,
                            feedback=str(e),
                            status="error",
                        ))
                        skipped += 1

                    progress.advance(task)
        else:
            for pr_file in files_to_review:
                try:
                    feedback = self.llm_client.review_code(
                        code=pr_file.patch,
                        filename=pr_file.filename,
                        context=f"PR: {pr_info.title}\n{pr_info.body or ''}",
                        diff_mode=True,
                    )
                    results.append(ReviewResult(
                        filename=pr_file.filename,
                        feedback=feedback,
                    ))
                    reviewed += 1
                except Exception as e:
                    results.append(ReviewResult(
                        filename=pr_file.filename,
                        feedback=str(e),
                        status="error",
                    ))
                    skipped += 1

        # Generate summary
        summary = None
        if results:
            summary = self.llm_client.summarize_reviews(
                [{"filename": r.filename, "feedback": r.feedback} for r in results if r.status == "success"]
            )

        report = ReviewReport(
            results=results,
            summary=summary,
            total_files=len(pr_info.files),
            reviewed_files=reviewed,
            skipped_files=skipped,
        )

        # Post comment if requested
        if post_comment and summary:
            comment_body = self._format_pr_comment(report, pr_info.title)
            self.github_client.create_review_comment(
                repo_full_name, pr_number, comment_body
            )

        return report

    def _review_file_list(self, files, show_progress: bool) -> ReviewReport:
        """Review a list of FileInfo objects"""
        results = []
        reviewed = 0
        skipped = 0

        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Reviewing files...", total=len(files))

                for file_info in files:
                    progress.update(task, description=f"Reviewing {file_info.relative_path}...")

                    try:
                        feedback = self.llm_client.review_code(
                            code=file_info.content,
                            filename=file_info.relative_path,
                        )
                        results.append(ReviewResult(
                            filename=file_info.relative_path,
                            feedback=feedback,
                        ))
                        reviewed += 1
                    except Exception as e:
                        results.append(ReviewResult(
                            filename=file_info.relative_path,
                            feedback=str(e),
                            status="error",
                        ))
                        skipped += 1

                    progress.advance(task)
        else:
            for file_info in files:
                try:
                    feedback = self.llm_client.review_code(
                        code=file_info.content,
                        filename=file_info.relative_path,
                    )
                    results.append(ReviewResult(
                        filename=file_info.relative_path,
                        feedback=feedback,
                    ))
                    reviewed += 1
                except Exception as e:
                    results.append(ReviewResult(
                        filename=file_info.relative_path,
                        feedback=str(e),
                        status="error",
                    ))
                    skipped += 1

        summary = None
        if results:
            summary = self.llm_client.summarize_reviews(
                [{"filename": r.filename, "feedback": r.feedback} for r in results if r.status == "success"]
            )

        return ReviewReport(
            results=results,
            summary=summary,
            total_files=len(files),
            reviewed_files=reviewed,
            skipped_files=skipped,
        )

    def _review_git_changes(self, changes, show_progress: bool) -> ReviewReport:
        """Review git changes"""
        results = []
        reviewed = 0
        skipped = 0

        changes_to_review = [c for c in changes if c.status != "D"]

        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Reviewing changes...", total=len(changes_to_review))

                for change in changes_to_review:
                    progress.update(task, description=f"Reviewing {change.filename}...")

                    code = change.diff or change.content
                    if not code:
                        skipped += 1
                        progress.advance(task)
                        continue

                    try:
                        feedback = self.llm_client.review_code(
                            code=code,
                            filename=change.filename,
                            diff_mode=bool(change.diff),
                        )
                        results.append(ReviewResult(
                            filename=change.filename,
                            feedback=feedback,
                        ))
                        reviewed += 1
                    except Exception as e:
                        results.append(ReviewResult(
                            filename=change.filename,
                            feedback=str(e),
                            status="error",
                        ))
                        skipped += 1

                    progress.advance(task)
        else:
            for change in changes_to_review:
                code = change.diff or change.content
                if not code:
                    skipped += 1
                    continue

                try:
                    feedback = self.llm_client.review_code(
                        code=code,
                        filename=change.filename,
                        diff_mode=bool(change.diff),
                    )
                    results.append(ReviewResult(
                        filename=change.filename,
                        feedback=feedback,
                    ))
                    reviewed += 1
                except Exception as e:
                    results.append(ReviewResult(
                        filename=change.filename,
                        feedback=str(e),
                        status="error",
                    ))
                    skipped += 1

        summary = None
        if results:
            summary = self.llm_client.summarize_reviews(
                [{"filename": r.filename, "feedback": r.feedback} for r in results if r.status == "success"]
            )

        return ReviewReport(
            results=results,
            summary=summary,
            total_files=len(changes),
            reviewed_files=reviewed,
            skipped_files=skipped,
        )

    def _format_pr_comment(self, report: ReviewReport, pr_title: str) -> str:
        """Format review report as PR comment"""
        lines = [
            "## AI Code Review",
            "",
            f"**PR:** {pr_title}",
            f"**Files reviewed:** {report.reviewed_files}/{report.total_files}",
            "",
            "---",
            "",
        ]

        if report.summary:
            lines.append("### Summary")
            lines.append("")
            lines.append(report.summary)
            lines.append("")
            lines.append("---")
            lines.append("")

        lines.append("### Detailed Review")
        lines.append("")

        for result in report.results:
            if result.status == "success":
                lines.append(f"<details>")
                lines.append(f"<summary><strong>{result.filename}</strong></summary>")
                lines.append("")
                lines.append(result.feedback)
                lines.append("")
                lines.append("</details>")
                lines.append("")

        lines.append("---")
        lines.append("*Generated by [zhen-ai-codereview](https://github.com/zhenzhen/zhen-ai-codereview)*")

        return "\n".join(lines)

    def print_report(self, report: ReviewReport) -> None:
        """Print review report to console"""
        self.console.print()

        if report.summary:
            self.console.print("[bold cyan]Summary[/bold cyan]")
            self.console.print(Markdown(report.summary))
            self.console.print()

        self.console.print("[bold cyan]Detailed Review[/bold cyan]")
        self.console.print()

        for result in report.results:
            if result.status == "success":
                self.console.print(f"[bold green]>>> {result.filename}[/bold green]")
                self.console.print(Markdown(result.feedback))
                self.console.print()
            elif result.status == "error":
                self.console.print(f"[bold red]>>> {result.filename} (error)[/bold red]")
                self.console.print(f"[red]{result.feedback}[/red]")
                self.console.print()

        self.console.print(
            f"[dim]Reviewed {report.reviewed_files}/{report.total_files} files "
            f"({report.skipped_files} skipped)[/dim]"
        )
