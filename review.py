import json
import os
from dotenv import load_dotenv
from github import Github, Auth
from google import genai

# Load environment variables from .env file
load_dotenv()

token = os.getenv("GITHUB_TOKEN")
key = os.getenv("GEMINI_API_KEY")

event_path = os.getenv("GITHUB_EVENT_PATH")



if not token or not key:
    raise ValueError("Missing Token or API Key.")

auth = Auth.Token(token)
gh = Github(auth=auth)
pr_number = 1

if event_path and os.path.exists(event_path):
    with open(event_path, "r") as f:
        event_data = json.load(f)
    pr_number = event_data["number"]


repo = gh.get_repo("TOgun1/AI-Pull-Request-Reviewer")
pr = repo.get_pull(pr_number)


files_changed = []
for file in pr.get_files():
    if file.status in ["added", "modified"] and not file.filename.endswith(".lock"):
        files_changed.append(f"File: {file.filename}\nPatch:\n{file.patch}")

diff_text = "\n\n".join(files_changed)

print(f"---Fetched Diff for PR #{pr.number}---")
print(diff_text)

ai_client = genai.Client(api_key=key)
prompt = f"""You are an expert software engineer reveiwing a GitHub Pull Request.
Provide concise, constructive feedback on potential bugs, security issues, and performance optimizations. Format your output cleanly in Markdown with bullet points:
Code Diff:
{diff_text}"""

response = ai_client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt,
)

print("\n--- AI Review Output ---")
print(response.text)

pr.create_issue_comment(f"### AI Review Feedback\n\n{response.text}")
print(f"\nSuccessfully posted AI review feedback to PR #{pr.number}.!")