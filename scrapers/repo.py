"""
GitHub Repository Scraper

Scrapes repository metadata, stars, issues, PRs, and contributors.
"""

import asyncio
import re
from datetime import datetime
from typing import Optional

import httpx
from pydantic import BaseModel, Field


class Repository(BaseModel):
    """GitHub repository data"""
    name: str
    full_name: str
    owner: str
    description: str = ""
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    open_issues: int = 0
    language: Optional[str] = None
    license: Optional[str] = None
    topics: list[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    pushed_at: str = ""
    url: str
    
    def to_dict(self):
        return self.model_dump()


class Contributor(BaseModel):
    """Repository contributor"""
    login: str
    avatar_url: str
    contributions: int = 0
    url: str


class Issue(BaseModel):
    """GitHub issue"""
    number: int
    title: str
    state: str
    author: str
    created_at: str
    closed_at: Optional[str] = None
    labels: list[str] = Field(default_factory=list)
    comments: int = 0


class GitHubScraper:
    """Scraper for GitHub repositories"""
    
    BASE_URL = "https://api.github.com"
    HEADERS = {
        "User-Agent": "GitHub-Intelligence/1.0",
        "Accept": "application/vnd.github.v3+json"
    }
    
    def __init__(self, timeout: int = 30, token: Optional[str] = None):
        if token:
            self.HEADERS["Authorization"] = f"token {token}"
        self.client = httpx.AsyncClient(headers=self.HEADERS, timeout=timeout)
    
    async def close(self):
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def get_repo(self, owner: str, repo: str) -> Repository:
        """Get repository metadata"""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        
        return Repository(
            name=data.get("name", ""),
            full_name=data.get("full_name", ""),
            owner=owner,
            description=data.get("description", ""),
            stars=data.get("stargazers_count", 0),
            forks=data.get("forks_count", 0),
            watchers=data.get("watchers_count", 0),
            open_issues=data.get("open_issues_count", 0),
            language=data.get("language"),
            license=data.get("license", {}).get("name") if data.get("license") else None,
            topics=data.get("topics", []),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            pushed_at=data.get("pushed_at", ""),
            url=data.get("html_url", "")
        )
    
    async def get_contributors(self, owner: str, repo: str, limit: int = 30) -> list[Contributor]:
        """Get repository contributors"""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contributors"
        response = await self.client.get(url, params={"per_page": limit})
        response.raise_for_status()
        
        contributors = []
        for c in response.json():
            contributors.append(Contributor(
                login=c.get("login", ""),
                avatar_url=c.get("avatar_url", ""),
                contributions=c.get("contributions", 0),
                url=c.get("html_url", "")
            ))
        return contributors
    
    async def get_issues(self, owner: str, repo: str, state: str = "open", limit: int = 30) -> list[Issue]:
        """Get repository issues"""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues"
        response = await self.client.get(url, params={"state": state, "per_page": limit})
        response.raise_for_status()
        
        issues = []
        for i in response.json():
            # Skip PRs
            if i.get("pull_request"):
                continue
            issues.append(Issue(
                number=i.get("number", 0),
                title=i.get("title", ""),
                state=i.get("state", ""),
                author=i.get("user", {}).get("login", ""),
                created_at=i.get("created_at", ""),
                closed_at=i.get("closed_at"),
                labels=[l.get("name", "") for l in i.get("labels", [])],
                comments=i.get("comments", 0)
            ))
        return issues
    
    async def get_languages(self, owner: str, repo: str) -> dict:
        """Get language breakdown"""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/languages"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()
    
    async def search_repos(self, query: str, sort: str = "stars", limit: int = 30) -> list[dict]:
        """Search repositories"""
        url = f"{self.BASE_URL}/search/repositories"
        response = await self.client.get(url, params={"q": query, "sort": sort, "per_page": limit})
        response.raise_for_status()
        
        return [r.get("full_name") for r in response.json().get("items", [])]
    
    async def get_repo_full(self, owner: str, repo: str) -> dict:
        """Get complete repo data"""
        repo_data = await self.get_repo(owner, repo)
        contributors = await self.get_contributors(owner, repo)
        issues = await self.get_issues(owner, repo)
        languages = await self.get_languages(owner, repo)
        
        return {
            "repo": repo_data.to_dict(),
            "contributors": [c.model_dump() for c in contributors],
            "issues": [i.model_dump() for i in issues],
            "languages": languages
        }


async def scrape_repo(full_name: str) -> Repository:
    """Convenience function"""
    owner, repo = full_name.split("/")
    async with GitHubScraper() as scraper:
        return await scraper.get_repo(owner, repo)


if __name__ == "__main__":
    import json
    import sys
    
    async def main():
        full_name = sys.argv[1] if len(sys.argv) > 1 else "facebook/react"
        
        print(f"Scraping {full_name}...")
        owner, repo = full_name.split("/")
        
        async with GitHubScraper() as scraper:
            data = await scraper.get_repo_full(owner, repo)
        
        print(f"Stars: {data['repo']['stars']}")
        print(f"Contributors: {len(data['contributors'])}")
        print(f"Issues: {len(data['issues'])}")
        
        with open(f"data/{full_name.replace('/', '_')}.json", "w") as f:
            json.dump(data, f, indent=2)
    
    asyncio.run(main())
