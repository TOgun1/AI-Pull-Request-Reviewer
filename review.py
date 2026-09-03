import os
from dotenv import load_dotenv
from github import Github, Auth

# Load environment variables from .env file
load_dotenv()

token = os.getenv("GITHUB_TOKEN")
key = os.getenv("GEMINI_API_KEY")

if not token:
    print("Error: GITHUB_TOKEN not found in .env file!")
elif not key:
    print("Error: GEMINI_API_KEY not found in .env file!")
else:
    # Initialize GitHub client
    auth = Auth.Token(token)
    gh = Github(auth=auth)
    
    # Authenticate and fetch your user account info
    user = gh.get_user()
    print(f"Successfully authenticated as: {user.login}")