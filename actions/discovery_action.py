from typing import Dict, Any, List, Set
from actions.base_action import Action
import re
from collections import Counter
import string

class DiscoveryAction(Action):
    """
    Action: Detect emerging keywords/topics not currently in the rules.
    """
    
    def execute(self):
        min_occurrence = self.params.get('min_occurrence', 3)
        limit = self.params.get('limit', 100)
        report_path = self.params.get('report_file', 'emerging_keywords.txt')
        
        # 1. Gather all "Known" keywords from other actions in the same profile (if possible)
        # For simplicity, we assume the config structure contains 'organize_keywords' rules
        known_keywords = self._get_known_keywords()
        self.logger.info(f"Loaded {len(known_keywords)} known keywords to ignore.")

        items = self.automator.folder.Items
        items.Sort("[ReceivedTime]", True)
        
        processed_count = 0
        text_corpus = []
        
        for item in items:
            if processed_count >= limit:
                break
            
            if item.Class != 43:
                continue

            processed_count += 1
            subject = getattr(item, 'Subject', '') or ''
            try:
                # Limit body to avoid analyzing massive reply chains
                body = getattr(item, 'Body', '') or ''
                body = body[:2000] 
            except:
                body = ''
            
            text_corpus.append(f"{subject} {body}")

        self.logger.info(f"Analyzing {processed_count} emails for novel terms...")
        
        # 2. Analyze
        emerging_terms = self._find_emerging_terms(text_corpus, known_keywords, min_occurrence)
        
        # 3. Report
        self._write_report(report_path, emerging_terms, processed_count)
    
    def _get_known_keywords(self) -> Set[str]:
        """Extract all keywords currently used in the organization rules."""
        keywords = set()
        # Look for the 'organize_keywords' action in the config
        for action in self.automator.config.get('actions', []):
            if action.get('name') == 'organize_keywords':
                rules = action.get('params', {}).get('rules', {})
                for cat_keywords in rules.values():
                    for kw in cat_keywords:
                        keywords.add(kw.lower())
        return keywords

    def _find_emerging_terms(self, corpus: List[str], known: Set[str], min_count: int) -> List[tuple]:
        """Tokenize and count frequent unknown terms."""
        # Minimal stopword list
        stopwords = {
            'the', 'and', 'to', 'of', 'a', 'in', 'is', 'that', 'for', 'it', 'as', 'was', 'with', 
            'on', 'at', 'by', 'an', 'be', 'this', 'which', 'or', 'from', 'but', 'not', 'are', 
            'your', 'you', 'can', 'will', 'have', 'all', 'if', 'we', 'my', 'has', 'so', 'one',
            'just', 'about', 'me', 'up', 'out', 'what', 'when', 'get', 'like', 'time', 'new',
            'more', 'no', 'do', 'any', 'how', 'see', 'don\'t', 'http', 'https', 'www', 'com',
            'thanks', 'regards', 'sent', 'subject', 'original', 'message', 'wrote', 'date',
            'from:', 'sent:', 'to:', 'subject:', 'cc:', 'pm', 'am', 're:', 'fw:', 'fwd:'
        }
        
        word_counter = Counter()
        bigram_counter = Counter()
        
        clean_regex = re.compile(r'[^\w\s]')
        
        for text in corpus:
            # Clean text: lowercase, remove punctuation
            text = text.lower()
            text = clean_regex.sub('', text)
            
            words = text.split()
            valid_words = []
            
            for i, word in enumerate(words):
                if len(word) < 4: continue # Skip short words
                if word in stopwords: continue
                if word.isdigit(): continue
                # Check if word is already "Known" (strictly or as substring?)
                # Strict check is safer to start
                if word in known: continue
                
                valid_words.append(word)
                word_counter[word] += 1
                
                # Bigrams (two words)
                if i < len(words) - 1:
                    next_word = words[i+1]
                    if len(next_word) >= 4 and next_word not in stopwords and not next_word.isdigit():
                         bigram_counter[f"{word} {next_word}"] += 1

        # Filter by min_count
        common_words = [
            (w, c) for w, c in word_counter.most_common(50) 
            if c >= min_count and w not in known
        ]
        
        common_bigrams = [
            (w, c) for w, c in bigram_counter.most_common(20) 
            if c >= min_count
        ]
        
        return common_words + common_bigrams

    def _write_report(self, path: str, terms: List[tuple], email_count: int):
        if self.automator.dry_run:
            self.logger.info("\n--- EMERGING KEYWORDS REPORT (Dry Run) ---")
            for term, count in terms:
                self.logger.info(f"  {term}: {count}")
            return

        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"Discovery Report\nAnalyzed {email_count} emails\n")
                f.write("-" * 40 + "\n")
                f.write(f"{'Term':<30} | Frequency\n")
                f.write("-" * 40 + "\n")
                for term, count in terms:
                    f.write(f"{term:<30} | {count}\n")
            
            self.logger.info(f"Written discovery report to {path}")
        except Exception as e:
            self.logger.error(f"Failed to write report: {e}")
