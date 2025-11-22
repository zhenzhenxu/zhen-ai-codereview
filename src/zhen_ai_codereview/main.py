"""
CLI entry point for Zhen AI Code Review
"""

import os
import sys

import click
from rich.console import Console

from .agent import CodeReviewAgent
from .config import load_config

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="zhen-ai-codereview")
def cli():
    """Zhen AI Code Review - AI-powered code review agent"""
    pass


@cli.command()
@click.argument("paths", nargs=-1, required=True)
@click.option("--recursive/--no-recursive", "-r/-R", default=True, help="Scan directories recursively")
def review(paths: tuple, recursive: bool):
    """Review local files or directories

    PATHS can be files or directories to review.

    Examples:
        zhen-review review src/
        zhen-review review main.py utils.py
        zhen-review review . --no-recursive
    """
    try:
        config = load_config()
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(1)

    agent = CodeReviewAgent(config)

    # Separate files and directories
    files = []
    directories = []

    for path in paths:
        if os.path.isfile(path):
            files.append(path)
        elif os.path.isdir(path):
            directories.append(path)
        else:
            console.print(f"[yellow]Warning: {path} does not exist, skipping[/yellow]")

    all_results = []

    # Review individual files
    if files:
        console.print(f"[cyan]Reviewing {len(files)} file(s)...[/cyan]")
        report = agent.review_files(files)
        all_results.extend(report.results)

    # Review directories
    for directory in directories:
        console.print(f"[cyan]Reviewing directory: {directory}[/cyan]")
        report = agent.review_directory(directory, recursive=recursive)
        all_results.extend(report.results)

    # Print combined report
    if all_results:
        from .agent.reviewer import ReviewReport
        combined_report = ReviewReport(
            results=all_results,
            total_files=len(all_results),
            reviewed_files=sum(1 for r in all_results if r.status == "success"),
            skipped_files=sum(1 for r in all_results if r.status != "success"),
        )
        agent.print_report(combined_report)


@cli.command()
@click.option("--base", "-b", default="HEAD~1", help="Base git reference (default: HEAD~1)")
@click.option("--head", "-h", default="HEAD", help="Head git reference (default: HEAD)")
@click.option("--repo", "-r", default=".", help="Path to git repository (default: current directory)")
def diff(base: str, head: str, repo: str):
    """Review git changes between two commits

    Examples:
        zhen-review diff
        zhen-review diff --base main --head feature-branch
        zhen-review diff -b HEAD~5
    """
    try:
        config = load_config()
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(1)

    agent = CodeReviewAgent(config)

    console.print(f"[cyan]Reviewing changes: {base}...{head}[/cyan]")

    try:
        report = agent.review_git_changes(repo, base, head)
        agent.print_report(report)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--repo", "-r", default=".", help="Path to git repository (default: current directory)")
def staged(repo: str):
    """Review staged git changes (pre-commit review)

    Examples:
        zhen-review staged
        zhen-review staged --repo /path/to/repo
    """
    try:
        config = load_config()
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(1)

    agent = CodeReviewAgent(config)

    console.print("[cyan]Reviewing staged changes...[/cyan]")

    try:
        report = agent.review_staged(repo)
        if report.reviewed_files == 0:
            console.print("[yellow]No staged changes to review[/yellow]")
        else:
            agent.print_report(report)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("repo_or_url")
@click.argument("pr_number", type=int)
@click.option("--comment/--no-comment", "-c/-C", default=False, help="Post review as PR comment")
def pr(repo_or_url: str, pr_number: int, comment: bool):
    """Review a GitHub pull request

    REPO_OR_URL: Repository in format 'owner/repo' or full GitHub URL
    PR_NUMBER: Pull request number

    Examples:
        zhen-review pr owner/repo 123
        zhen-review pr https://github.com/owner/repo/pull/123 123
        zhen-review pr owner/repo 123 --comment
    """
    try:
        config = load_config()
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(1)

    if not config.github:
        console.print("[red]Error: GITHUB_TOKEN is required for PR review[/red]")
        console.print("[dim]Set GITHUB_TOKEN environment variable or add it to .env file[/dim]")
        sys.exit(1)

    # Parse repo from URL if needed
    if "github.com" in repo_or_url:
        # Extract owner/repo from URL
        parts = repo_or_url.rstrip("/").split("/")
        if "pull" in parts:
            idx = parts.index("pull")
            repo_full_name = "/".join(parts[idx-2:idx])
        else:
            repo_full_name = "/".join(parts[-2:])
    else:
        repo_full_name = repo_or_url

    agent = CodeReviewAgent(config)

    console.print(f"[cyan]Reviewing PR #{pr_number} in {repo_full_name}...[/cyan]")

    try:
        report = agent.review_pr(repo_full_name, pr_number, post_comment=comment)
        agent.print_report(report)

        if comment:
            console.print("[green]Review posted as PR comment[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
