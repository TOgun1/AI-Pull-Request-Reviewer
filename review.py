import argparse
import json
import os
import sys
from dotenv import load_dotenv
from github import Github, Auth, GithubException
from google import genai

# Load environment variables from .env file
load_dotenv()

EXCLUDED_EXTENSIONS = (
    ".lock", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".pdf", ".zip", ".tar.gz", ".tgz", ".woff", ".woff2", ".ttf", ".eot",
    ".mp4", ".mp3", ".wav"
)
EXCLUDED_FILENAMES = (
    "package-lock.json", "poetry.lock", "yarn.lock", "pnpm-lock.yaml",
    "gemfile.lock", "cargo.lock", "composer.lock"
)
MAX_DIFF_CHARS = 60000


def is_reviewable_file(filename: str) -> bool:
    """Checks whether a file should be included in the code review diff."""
    name_lower = filename.lower()
    if any(name_lower.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
        return False
    base_name = os.path.basename(name_lower)
    if base_name in EXCLUDED_FILENAMES:
        return False
    if name_lower.endswith(".min.js") or name_lower.endswith(".min.css"):
        return False
    return True


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="AI Pull Request Reviewer using Google Gemini. Can review PRs across any repository."
    )
    parser.add_argument(
        "--repo", "-r",
        type=str,
        default=None,
        help="Target GitHub repository (e.g. owner/repo). Defaults to GITHUB_REPOSITORY env var."
    )
    parser.add_argument(
        "--pr", "-p",
        type=int,
        default=None,
        help="Target pull request number. Defaults to PR_NUMBER env var or GITHUB_EVENT_PATH payload."
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="Gemini model name. Defaults to GEMINI_MODEL env var or 'gemini-3.6-flash'."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run AI review and print to stdout without posting comment to the pull request."
    )
    return parser.parse_args()


def load_event_data(event_path: str | None) -> dict:
    """Loads GitHub event payload if available."""
    if event_path and os.path.exists(event_path):
        try:
            with open(event_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not parse event file at {event_path}: {e}")
    return {}


def resolve_target(args, event_data: dict) -> tuple[str, int]:
    """Resolve repository full name and pull request number from CLI args, env vars, or event data."""
    # Resolve repository name
    repo_name = (
        args.repo
        or os.getenv("TARGET_REPO")
        or os.getenv("GITHUB_REPOSITORY")
    )
    if not repo_name and event_data:
        repo_name = event_data.get("repository", {}).get("full_name")

    # Fallback to local default if running in original repository without args
    if not repo_name:
        repo_name = "TOgun1/AI-Pull-Request-Reviewer"

    # Resolve PR number
    pr_number = args.pr
    if pr_number is None and os.getenv("PR_NUMBER"):
        try:
            pr_number = int(os.environ["PR_NUMBER"])
        except ValueError:
            pass

    if pr_number is None and event_data:
        if "number" in event_data:
            pr_number = event_data["number"]
        elif "pull_request" in event_data and "number" in event_data["pull_request"]:
            pr_number = event_data["pull_request"]["number"]

    if pr_number is None:
        raise ValueError(
            "Missing Pull Request number. Specify via --pr flag, PR_NUMBER environment variable, "
            "or run inside a GitHub Actions pull_request workflow."
        )

    return repo_name, pr_number


def main():
    args = parse_args()

    token = os.getenv("GITHUB_TOKEN")
    key = os.getenv("GEMINI_API_KEY")
    event_path = os.getenv("GITHUB_EVENT_PATH")
    model = args.model or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    # Validate that required secrets are present
    if not token or not key:
        raise ValueError("Missing GITHUB_TOKEN or GEMINI_API_KEY environment variable.")

    event_data = load_event_data(event_path)
    repo_name, pr_number = resolve_target(args, event_data)

    print(f"Target Repository: {repo_name}")
    print(f"Target PR Number:  #{pr_number}")
    print(f"Gemini Model:     {model}")
    print(f"Dry Run Mode:     {args.dry_run}\n")

    auth = Auth.Token(token)
    gh = Github(auth=auth)

    # Fetch the repository
    try:
        repo = gh.get_repo(repo_name)
    except GithubException as e:
        print(f"Error accessing repository '{repo_name}': {e.data.get('message', str(e))}")
        sys.exit(1)

    # Fetch the pull request
    try:
        pr = repo.get_pull(pr_number)
    except GithubException as e:
        print(f"Error accessing PR #{pr_number} in '{repo_name}': {e.data.get('message', str(e))}")
        sys.exit(1)

    # Check changed files and filter out non-reviewable assets / lockfiles
    files_changed = []
    for file in pr.get_files():
        if file.status in ["added", "modified"] and file.patch:
            if is_reviewable_file(file.filename):
                files_changed.append(f"File: {file.filename}\nPatch:\n{file.patch}")
            else:
                print(f"Skipping non-code/lock file: {file.filename}")

    if not files_changed:
        print(f"No reviewable code changes found in PR #{pr.number}. Exiting review.")
        return

    # Join all the diffs into a single string for the AI prompt
    diff_text = "\n\n".join(files_changed)
    if len(diff_text) > MAX_DIFF_CHARS:
        print(f"Warning: Diff length ({len(diff_text)} chars) exceeds limit. Truncating to {MAX_DIFF_CHARS} chars.")
        diff_text = diff_text[:MAX_DIFF_CHARS] + "\n\n... [Diff truncated due to length limits] ..."

    # Test print the fetched diff for debugging purposes
    print(f"--- Fetched Diff for {repo_name} PR #{pr.number} ---")
    print(diff_text)

    # Initialize the Google Gemini AI client and prepare the prompt for code review
    ai_client = genai.Client(api_key=key)
    prompt = f"""You are an expert software engineer reviewing a GitHub Pull Request for repository '{repo_name}'.
Provide concise, constructive feedback on potential bugs, security issues, edge cases, and performance optimizations. Format your output cleanly in Markdown with bullet points:
Code Diff:
{diff_text}"""

    try:
        response = ai_client.models.generate_content(
            model=model,
            contents=prompt,
        )
    except Exception as e:
        print(f"Error generating AI review with model '{model}': {e}")
        sys.exit(1)

    print("\n--- AI Review Output ---")
    print(response.text)

    # Post comment or print dry-run notice
    if args.dry_run:
        print(f"\n[DRY RUN] Review successfully generated for {repo_name} PR #{pr.number}. Comment was not posted.")
    else:
        try:
            pr.create_issue_comment(f"### AI Review Feedback\n\n{response.text}")
            print(f"\nSuccessfully posted AI review feedback to {repo_name} PR #{pr.number}!")
        except GithubException as e:
            print(f"Error posting review comment to PR #{pr.number}: {e.data.get('message', str(e))}")
            sys.exit(1)


if __name__ == "__main__":
    main()