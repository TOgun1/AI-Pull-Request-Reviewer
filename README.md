# AI-Pull-Request-Reviewer

An event-driven CI/CD data pipeline which automatically generates an AI code review upon the event of a pull request.

## OVERVIEW

This project is meant to automate code reviews within GitHub development workflows. When a contributor opens or updates a Pull Request, a GitHub Actions workflow triggers a serverless Python pipeline. The system extracts code patches, filters out irrelevant files, and then uses Gemini to detect any issues worth flagging such as bugs or security vulnerabilites. This AI code review is then posted directly back to the Pull Request.

## KEY FEATURES

* **Event-Driven Automation:** Listens to `pull_request` triggers (`opened`, `synchronize`) using native GitHub Actions runner contexts.
* **Smart Diff Extraction:** Uses `PyGithub` to parse unified diff patches while filtering out lockfiles (`package-lock.json`, `poetry.lock`) to conserve API tokens.
* **Structured AI Feedback:** Leverages prompt engineering to generate concise, high-yield code reviews.

## Architecture & Data Flow

```text
[ Developer Opens/Updates PR ]
               │
               ▼
   [ GitHub Actions Workflow ]
               │
               ▼
     [ review.py Script ]
   ├── Reads PR Diff via GitHub API
   ├── Filters out Lockfiles / Assets
   └── Formats Payload
               │
               ▼
     [ Gemini 3.6 Flash API ]
               │ (Generates Code Review)
               ▼
   [ Post Feedback to PR Comments ]