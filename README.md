# AI-Pull-Request-Reviewer

An event-driven, reusable CI/CD pipeline and CLI tool that automatically reviews pull requests using Google Gemini AI.

## OVERVIEW

This project automates code reviews across GitHub development workflows. When a contributor opens or updates a Pull Request, the AI reviewer analyzes code diffs, filters out irrelevant assets and lockfiles, and utilizes Google Gemini to detect bugs, security vulnerabilities, edge cases, and performance optimizations. Constructive feedback is posted directly as a comment on the pull request.

This tool can be used directly as a **reusable GitHub Action** across any of your repositories, or executed locally as a **CLI command** to review pull requests from any repository.

---

## USING IN OTHER PROJECTS (GitHub Action)

You can plug this AI code reviewer into any other GitHub project in minutes without cloning or copying code.

### 1. Add Gemini API Key to Your Secrets
1. Obtain an API key from [Google AI Studio](https://aistudio.google.com/).
2. In your target repository, go to **Settings > Secrets and variables > Actions**.
3. Create a new repository secret named `GEMINI_API_KEY` and paste your key.

### 2. Create the Workflow File
In the other project, create a workflow file at `.github/workflows/ai-review.yml`:

```yaml
name: AI PR Code Reviewer

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Run AI Code Reviewer
        uses: TOgun1/AI-Pull-Request-Reviewer@main
        with:
          gemini_api_key: ${{ secrets.GEMINI_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
          model: "gemini-3.6-flash" # Optional (defaults to gemini-3.6-flash)
```

### Action Configuration Options

| Input | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `gemini_api_key` | Google Gemini API Key | **Yes** | — |
| `github_token` | GitHub access token (`pull-requests: write`) | No | `${{ github.token }}` |
| `model` | Gemini model name (e.g., `gemini-3.6-flash`) | No | `gemini-3.6-flash` |
| `repo` | Target repository in `owner/repo` format | No | Current repository |
| `pr_number` | Target PR number (auto-detected from PR event) | No | Current PR number |
| `dry_run` | Set to `"true"` to log review without commenting | No | `"false"` |

---

## LOCAL / CLI USAGE

You can also use this tool from your local terminal to review pull requests across any public or private repository:

```bash
# Clone the repository and install dependencies
git clone https://github.com/TOgun1/AI-Pull-Request-Reviewer.git
cd AI-Pull-Request-Reviewer
python -m venv venv
source venv/bin/activate # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# Set your API keys in .env or environment
export GITHUB_TOKEN="your_github_token"
export GEMINI_API_KEY="your_gemini_api_key"

# Review a pull request from any repository (dry-run prints to terminal)
python review.py --repo owner/Hello-World --pr 12 --dry-run

# Review and post feedback comment directly to the PR
python review.py --repo owner/my-other-project --pr 45
```

### CLI Arguments

```text
options:
  -h, --help            Show help message and exit
  --repo, -r REPO       Target GitHub repository (e.g. owner/repo)
  --pr, -p PR           Target pull request number
  --model, -m MODEL     Gemini model name (default: gemini-3.6-flash)
  --dry-run             Generate review to console without posting PR comment
```

---

## ARCHITECTURE & DATA FLOW

```text
[ Developer Opens/Updates PR in any Repo ]
                   │
                   ▼
    [ GitHub Actions Workflow ]
    (uses: TOgun1/AI-Pull-Request-Reviewer@main)
                   │
                   ▼
         [ review.py Engine ]
   ├── Reads Target PR Diff via GitHub API
   ├── Filters Out Lockfiles, Binaries & Minified Assets
   ├── Truncates Oversized Diffs (Safety Guard)
   └── Builds Review Prompt Payload
                   │
                   ▼
        [ Gemini 3.6 Flash API ]
                   │ (Generates Code Review)
                   ▼
    [ Post Feedback to PR Comments ]
```
