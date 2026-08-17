# agent/tools.py
import os
import requests
from pypdf import PdfReader

# Global cache for resume text
_RESUME_CACHE = None

def extract_text_from_pdf(pdf_path: str = "Resume_Sadat_Mahmud-2.pdf") -> str:
    """Extracts all text content from Sadat's resume PDF file with built-in caching."""
    global _RESUME_CACHE
    
    if _RESUME_CACHE is not None:
        return _RESUME_CACHE

    if not os.path.exists(pdf_path):
        return "Resume PDF not found in project root directory."
    
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        
        _RESUME_CACHE = text.strip()
        return _RESUME_CACHE
    except Exception as e:
        return f"Error extracting resume text: {e}"

def get_github_projects(username: str = "SADAT334") -> str:
    """Fetches public repositories and tech stacks for a given GitHub user."""
    try:
        url = f"https://api.github.com/users/{username}/repos"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            repos = response.json()
            project_summaries = []
            for repo in repos[:8]:  # Grabs the top 8 public repositories
                name = repo.get("name")
                desc = repo.get("description", "No description provided")
                lang = repo.get("language", "Various")
                project_summaries.append(f"- **{name}** ({lang}): {desc}")
            return "\n".join(project_summaries)
        return "Could not retrieve GitHub data at the moment."
    except Exception as e:
        return f"GitHub fetch error: {e}"
    