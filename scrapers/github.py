"""
GitHub API Client

Enhanced GitHub scraper with rate limiting and pagination.
"""

import asyncio
import os
from typing import Optional
import httpx
from pydantic import BaseModel, Field


class GitHubClient:
    """Enhanced GitHub API client"""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {
            "User-Agent": "GitHub-Intelligence/1.0",
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        self.client = httpx.AsyncClient(headers=self.headers)
    
    async def close(self):
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def get(self, url: str, **kwargs):
        """Make request with rate limit handling"""
        response = await self.client.get(url, **kwargs)
        
        # Check rate limit
        remaining = int(response.headers.get("X-RateLimit-Remaining", 60))
        if remaining < 5:
            reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
            wait_time = max(0, reset_time - asyncio.get_event_loop().time())
            if wait_time > 0:
                print(f"Rate limit low ({remaining}), waiting {wait_time}s")
                await asyncio.sleep(wait_time)
        
        response.raise_for_status()
        return response
    
    async def search_repos(self, query: str, sort: str = "stars", per_page: int = 100) -> list:
        """Search repositories with pagination"""
        all_repos = []
        page = 1
        
        while len(all_repos) < per_page:
            response = await self.get(
                f"{self.BASE_URL}/search/repositories",
                params={
                    "q": query,
                    "sort": sort,
                    "per_page": min(100, per_page - len(all_repos)),
                    "page": page
                }
            )
            
            items = response.json().get("items", [])
            if not items:
                break
            
            all_repos.extend(items)
            page += 1
            
            # Check if we hit the search limit
            if len(items) < 100:
                break
        
        return all_repos
    
    async def get_user(self, username: str) -> dict:
        """Get user profile"""
        response = await self.get(f"{self.BASE_URL}/users/{username}")
        return response.json()
    
    async def get_user_repos(self, username: str, sort: str = "updated") -> list:
        """Get user repositories"""
        repos = []
        page = 1
        
        while len(repos) < 100:
            response = await self.get(
                f"{self.BASE_URL}/users/{username}/repos",
                params={"per_page": 100, "page": page, "sort": sort}
            )
            
            items = response.json()
            if not items:
                break
            
            repos.extend(items)
            page += 1
        
        return repos
    
    async def get_repo(self, owner: str, repo: str) -> dict:
        """Get repository"""
        response = await self.get(f"{self.BASE_URL}/repos/{owner}/{repo}")
        return response.json()
    
    async def get_contributors(self, owner: str, repo: str) -> list:
        """Get contributors"""
        contributors = []
        page = 1
        
        while len(contributors) < 100:
            response = await self.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/contributors",
                params={"per_page": 100, "page": page}
            )
            
            items = response.json()
            if not items:
                break
            
            contributors.extend(items)
            page += 1
        
        return contributors
    
    async def get_stargazers(self, owner: str, repo: str) -> list:
        """Get stargazers"""
        stars = []
        page = 1
        
        while len(stars) < 1000:
            response = await self.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/stargazers",
                params={"per_page": 100, "page": page}
            )
            
            items = response.json()
            if not items:
                break
            
            stars.extend([s.get("login") for s in items])
            page += 1
        
        return stars


async def search_trending_repos(language: str = "", since: str = "daily") -> list:
    """Search trending repositories"""
    
    query = f"stars:>100"
    if language:
        query += f" language:{language}"
    
    async with GitHubClient() as client:
        return await client.search_repos(query, sort="stars", per_page=100)


async def analyze_user(username: str) -> dict:
    """Analyze a GitHub user"""
    
    async with GitHubClient() as client:
        # Get user profile
        user = await client.get_user(username)
        
        # Get repos
        repos = await client.get_user_repos(username)
        
        # Analyze
        total_stars = sum(r.get("stargazers_count", 0) for r in repos)
        total_forks = sum(r.get("forks_count", 0) for r in repos)
        
        languages = {}
        for repo in repos:
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
        
        return {
            "username": username,
            "name": user.get("name"),
            "bio": user.get("bio"),
            "followers": user.get("followers"),
            "following": user.get("following"),
            "public_repos": user.get("public_repos"),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "languages": languages,
            "top_repos": sorted(
                repos, 
                key=lambda r: r.get("stargazers_count", 0),
                reverse=True
            )[:10]
        }


if __name__ == "__main__":
    import json
    
    async def main():
        # Search trending
        print("Finding trending Python repos...")
        repos = await search_trending_repos("python")
        print(f"Found {len(repos)} repos")
        
        # Analyze a user
        print("\nAnalyzing torvalds...")
        data = await analyze_user("torvalds")
        print(f"Name: {data['name']}")
        print(f"Followers: {data['followers']}")
        print(f"Total stars: {data['total_stars']}")
        print(f"Languages: {data['languages']}")
        
        with open("data/github_analysis.json", "w") as f:
            json.dump(data, f, indent=2)
    
    asyncio.run(main())
