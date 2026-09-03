import os
from dotenv import load_dotenv
from github import Github

# Load environment variables from .env file
load_dotenv()

token = os.getenv("GITHUB_TOKEN")

if not token:
    print("Error: GITHUB_TOKEN not found in .env file!")
else:
    # Initialize GitHub client
    gh = Github(token)
    
    # Authenticate and fetch your user account info
    user = gh.get_user()
    print(f"Successfully authenticated as: {user.login}")