"""
Developer Influence Graph

Builds and analyzes developer interaction graphs.
"""

import networkx as nx
from typing import Optional


class DeveloperGraph:
    """Graph of developer interactions"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def add_contributor(self, repo: str, contributor: str, contributions: int = 1):
        """Add a contributor to a repo"""
        # Add repo node
        self.graph.add_node(f"repo:{repo}", type="repo")
        
        # Add developer node
        self.graph.add_node(f"dev:{contributor}", type="developer")
        
        # Add edge (developer -> repo)
        self.graph.add_edge(
            f"dev:{contributor}", 
            f"repo:{repo}", 
            weight=contributions,
            type="contributed_to"
        )
    
    def add_follow(self, follower: str, following: str):
        """Add a follow relationship"""
        self.graph.add_node(f"dev:{follower}", type="developer")
        self.graph.add_node(f"dev:{following}", type="developer")
        self.graph.add_edge(
            f"dev:{follower}",
            f"dev:{following}",
            type="follows"
        )
    
    def get_top_developers(self, limit: int = 10) -> list:
        """Get most connected developers"""
        # Calculate degree centrality
        devs = [n for n in self.graph.nodes() if n.startswith("dev:")]
        centrality = nx.degree_centrality(self.graph)
        
        sorted_devs = sorted(
            [(d, centrality[d]) for d in devs if d in centrality],
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_devs[:limit]
    
    def get_influential_devs(self, repo: str) -> list:
        """Get most influential devs in a repo"""
        repo_node = f"repo:{repo}"
        if repo_node not in self.graph:
            return []
        
        # Get contributors to this repo
        contributors = list(self.graph.predecessors(repo_node))
        
        # Calculate their influence ( PageRank)
        pagerank = nx.pagerank(self.graph)
        
        sorted_contributors = sorted(
            [(c, pagerank.get(c, 0)) for c in contributors],
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_contributors
    
    def find_connections(self, dev1: str, dev2: str) -> list:
        """Find shortest path between two developers"""
        try:
            path = nx.shortest_path(
                self.graph, 
                f"dev:{dev1}", 
                f"dev:{dev2}"
            )
            return path
        except nx.NetworkXNoPath:
            return []
    
    def export_graph(self, format: str = "gexf") -> str:
        """Export graph to file"""
        if format == "gexf":
            from networkx.readwrite import json_graph
            return json_graph.gexf.dumps(self.graph)
        return str(self.graph.nodes())


if __name__ == "__main__":
    # Demo
    g = DeveloperGraph()
    
    # Add some contributors
    g.add_contributor("facebook/react", "dan_abramov", 500)
    g.add_contributor("facebook/react", "sebmarkbage", 300)
    g.add_contributor("facebook/react", "acdlite", 200)
    g.add_contributor("vercel/next.js", "leerob", 400)
    g.add_contributor("vercel/next.js", "shu_fff", 300)
    
    # Add cross-repo connections (same dev contributes to multiple)
    g.add_contributor("facebook/react", "acdlite", 100)
    g.add_contributor("vercel/next.js", "acdlite", 50)
    
    print("Top developers:")
    for dev, score in g.get_top_developers():
        print(f"  {dev}: {score:.4f}")
    
    print("\nInfluential in facebook/react:")
    for dev, score in g.get_influential_devs("facebook/react"):
        print(f"  {dev}: {score:.4f}")
