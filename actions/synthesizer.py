import logging
import random
from typing import List, Dict
from actions.knowledge_base import KnowledgeBase

import os

class Synthesizer:
    """
    The Idea Generator Engine.
    Queries the Knowledge Base for disparate concepts and synthesizes new ideas.
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, 'data', 'knowledge_base')
            
        self.kb = KnowledgeBase(db_path=db_path)
        self.logger = logging.getLogger("Synthesizer")
        
    def generate_ideas(self, domain_a: str, domain_b: str, count: int = 3) -> List[str]:
        """
        Cross-pollinate two domains (e.g., "ComfyUI" + "Laser").
        """
        self.logger.info(f"Synthesizing ideas between '{domain_a}' and '{domain_b}'...")
        
        # 1. Fetch "Wisdom" from Domain A
        results_a = self.kb.query(query_text=domain_a, n_results=5)
        docs_a = results_a['documents'][0] if results_a['documents'] else []
        meta_a = results_a['metadatas'][0] if results_a['metadatas'] else []

        # 2. Fetch "Wisdom" from Domain B
        results_b = self.kb.query(query_text=domain_b, n_results=5)
        docs_b = results_b['documents'][0] if results_b['documents'] else []
        meta_b = results_b['metadatas'][0] if results_b['metadatas'] else []

        if not docs_a or not docs_b:
            self.logger.warning("Insufficient data in Knowledge Base to synthesize.")
            return ["Need more data ingested first."]

        ideas = []
        
        # 3. Synthesize (Simulated "LLM Process" for now)
        # In a real scenario, this would send `doc_a` and `doc_b` to Gemini/Generic LLM 
        # with a prompt: "Combine these techniques into a new workflow."
        
        for i in range(min(count, len(docs_a), len(docs_b))):
            idea_a = meta_a[i].get('subject', 'Unknown Concept')
            idea_b = meta_b[i].get('subject', 'Unknown Concept')
            
            # Simple heuristic combination for the MVP
            prompt = (
                f"IDEA #{i+1}: COMBINE '{domain_a}' AND '{domain_b}'\n"
                f"   Source A ({domain_a}): {idea_a}\n"
                f"   Source B ({domain_b}): {idea_b}\n"
                f"   PROPOSED WORKFLOW: Use the technique from '{idea_a}' to generate assets, "
                f"then process them using the method described in '{idea_b}'.\n"
            )
            ideas.append(prompt)
            
        return ideas

    def run_daily_synthesis(self):
        """Run a standard set of cross-pollinations."""
        report = "DAILY SYNTHESIS REPORT\n" + "="*40 + "\n\n"
        
        combinations = [
            ("ComfyUI", "Laser Engraving"),
            ("Gemini CLI", "History Project"),
            ("Python Script", "Video Generation")
        ]
        
        for dom_a, dom_b in combinations:
            ideas = self.generate_ideas(dom_a, dom_b, count=2)
            for idea in ideas:
                report += idea + "\n" + "-"*40 + "\n"
                
        with open("idea_synthesis.txt", "w", encoding="utf-8") as f:
            f.write(report)
            
        self.logger.info("Synthesis complete. Report written to 'idea_synthesis.txt'.")
