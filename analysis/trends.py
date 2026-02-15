"""
Technology Trend Analysis

Analyzes technology adoption trends from repo data.
"""

import pandas as pd
from collections import Counter
from datetime import datetime
from typing import Optional


class TrendAnalyzer:
    """Analyzes technology trends"""
    
    def __init__(self):
        self.data = []
    
    def add_repo(self, repo_data: dict):
        """Add repo data for analysis"""
        self.data.append(repo_data)
    
    def get_language_trends(self) -> dict:
        """Get language adoption trends"""
        languages = [r.get("language") for r in self.data if r.get("language")]
        return dict(Counter(languages).most_common(20))
    
    def get_topic_trends(self) -> dict:
        """Get trending topics"""
        topics = []
        for r in self.data:
            topics.extend(r.get("topics", []))
        return dict(Counter(topics).most_common(20))
    
    def get_top_repos(self, metric: str = "stars", limit: int = 10) -> list:
        """Get top repos by metric"""
        sorted_repos = sorted(
            self.data,
            key=lambda x: x.get(metric, 0),
            reverse=True
        )
        return sorted_repos[:limit]
    
    def calculate_growth_rate(self, repo_data: dict) -> float:
        """Calculate growth rate of a repo"""
        # Simple metric: stars / age in days
        if "created_at" not in repo_data:
            return 0
        
        try:
            created = datetime.fromisoformat(repo_data["created_at"].replace("Z", "+00:00"))
            age_days = (datetime.now() - created).days
            if age_days > 0:
                return repo_data.get("stars", 0) / age_days
        except:
            pass
        return 0
    
    def detect_breakout_repos(self, min_stars: int = 100) -> list:
        """Detect breakout repos (high growth)"""
        for r in self.data:
            r["growth_rate"] = self.calculate_growth_rate(r)
        
        breakout = [r for r in self.data if r.get("stars", 0) >= min_stars]
        return sorted(breakout, key=lambda x: x.get("growth_rate", 0), reverse=True)[:10]
    
    def generate_heatmap_data(self) -> dict:
        """Generate heatmap data for visualization"""
        # Language vs Stars
        lang_stars = {}
        for r in self.data:
            lang = r.get("language", "Unknown")
            stars = r.get("stars", 0)
            if lang not in lang_stars:
                lang_stars[lang] = []
            lang_stars[lang].append(stars)
        
        # Average stars per language
        return {
            lang: sum(stars) / len(stars) 
            for lang, stars in lang_stars.items() 
            if len(stars) > 0
        }


if __name__ == "__main__":
    # Demo
    analyzer = TrendAnalyzer()
    
    # Add sample data
    analyzer.add_repo({
        "name": "react",
        "language": "JavaScript",
        "stars": 220000,
        "topics": ["ui", "react", "frontend"]
    })
    analyzer.add_repo({
        "name": "vue",
        "language": "JavaScript",
        "stars": 206000,
        "topics": ["ui", "vue", "frontend"]
    })
    analyzer.add_repo({
        "name": "tensorflow",
        "language": "Python",
        "stars": 180000,
        "topics": ["ml", "deep-learning", "ai"]
    })
    
    print("Language trends:", analyzer.get_language_trends())
    print("\nTopic trends:", analyzer.get_topic_trends())
    print("\nTop repos:", analyzer.get_top_repos())
