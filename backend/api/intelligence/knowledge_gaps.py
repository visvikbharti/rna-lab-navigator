"""
Knowledge Gap Detection System

Analyzes research coverage across papers to identify:
- Unexplored parameter combinations
- Missing experimental validations
- Unanswered questions
- Research topic evolution
"""

import re
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

from django.core.cache import cache
from django.db.models import Count, Q, F
from django.utils import timezone

from api.models import Document, QueryHistory
from api.search.services import SearchService
# from api.llm.local_llm import LLMService  # Not implemented yet


class KnowledgeGapAnalyzer:
    """Analyzes research corpus to identify knowledge gaps and opportunities."""
    
    def __init__(self):
        self.search_service = SearchService()
        # self.llm_service = LLMService()  # Not implemented yet
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 3)
        )
        
    def analyze_research_coverage(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze overall research coverage in the corpus.
        
        Args:
            domain: Optional domain filter (e.g., "RNA editing", "CRISPR")
            
        Returns:
            Dictionary containing coverage analysis
        """
        cache_key = f"knowledge_gaps:coverage:{domain or 'all'}"
        cached = cache.get(cache_key)
        if cached:
            return cached
            
        # Get all documents
        docs_query = Document.objects.all()
        if domain:
            docs_query = docs_query.filter(
                Q(title__icontains=domain) | 
                Q(abstract__icontains=domain)
            )
            
        documents = list(docs_query.values('id', 'title', 'abstract', 'content', 'doc_type', 'created_at'))
        
        if not documents:
            return {"error": "No documents found"}
            
        # Extract research areas and parameters
        research_areas = self._extract_research_areas(documents)
        parameter_space = self._analyze_parameter_space(documents)
        temporal_evolution = self._analyze_temporal_evolution(documents)
        
        # Identify gaps
        coverage_gaps = self._identify_coverage_gaps(research_areas, parameter_space)
        
        result = {
            "total_documents": len(documents),
            "research_areas": research_areas,
            "parameter_space": parameter_space,
            "temporal_evolution": temporal_evolution,
            "coverage_gaps": coverage_gaps,
            "coverage_score": self._calculate_coverage_score(research_areas, parameter_space),
            "last_updated": timezone.now().isoformat()
        }
        
        cache.set(cache_key, result, 3600)  # Cache for 1 hour
        return result
        
    def identify_unexplored_combinations(self) -> List[Dict[str, Any]]:
        """
        Identify unexplored parameter combinations in experiments.
        
        Returns:
            List of unexplored combinations with potential impact scores
        """
        cache_key = "knowledge_gaps:unexplored_combinations"
        cached = cache.get(cache_key)
        if cached:
            return cached
            
        documents = Document.objects.filter(doc_type__in=['paper', 'thesis'])
        
        # Extract experimental parameters from methods sections
        all_parameters = defaultdict(set)
        parameter_combinations = []
        
        for doc in documents:
            params = self._extract_experimental_parameters(doc.content)
            for category, values in params.items():
                all_parameters[category].update(values)
            
            # Track existing combinations
            if len(params) > 1:
                param_combo = tuple(sorted(
                    [(k, tuple(sorted(v))) for k, v in params.items()]
                ))
                parameter_combinations.append(param_combo)
        
        # Generate potential combinations
        unexplored = self._generate_unexplored_combinations(
            all_parameters, 
            parameter_combinations
        )
        
        # Score combinations by potential impact
        scored_combinations = []
        for combo in unexplored[:50]:  # Limit to top 50
            score = self._score_combination_impact(combo, documents)
            scored_combinations.append({
                "combination": dict(combo),
                "impact_score": score,
                "rationale": self._generate_combination_rationale(combo),
                "related_papers": self._find_related_papers(combo, documents)
            })
        
        # Sort by impact score
        scored_combinations.sort(key=lambda x: x['impact_score'], reverse=True)
        
        cache.set(cache_key, scored_combinations[:20], 3600)  # Top 20, cache 1 hour
        return scored_combinations[:20]
        
    def detect_missing_validations(self) -> List[Dict[str, Any]]:
        """
        Detect claims or hypotheses that lack experimental validation.
        
        Returns:
            List of unvalidated claims with supporting evidence
        """
        cache_key = "knowledge_gaps:missing_validations"
        cached = cache.get(cache_key)
        if cached:
            return cached
            
        documents = Document.objects.filter(doc_type='paper')
        unvalidated_claims = []
        
        for doc in documents:
            # Extract hypotheses and claims
            claims = self._extract_claims_and_hypotheses(doc.content)
            
            # Check for validation in same or other papers
            for claim in claims:
                validation_status = self._check_validation_status(claim, documents)
                
                if validation_status['status'] == 'unvalidated':
                    unvalidated_claims.append({
                        "claim": claim['text'],
                        "source_paper": doc.title,
                        "source_id": doc.id,
                        "claim_type": claim['type'],
                        "confidence": claim['confidence'],
                        "potential_validation_methods": validation_status['suggested_methods'],
                        "related_work": validation_status['related_work']
                    })
        
        # Sort by confidence and potential impact
        unvalidated_claims.sort(
            key=lambda x: x['confidence'] * 0.7 + len(x['related_work']) * 0.3,
            reverse=True
        )
        
        cache.set(cache_key, unvalidated_claims[:30], 3600)  # Top 30, cache 1 hour
        return unvalidated_claims[:30]
        
    def find_unanswered_questions(self) -> List[Dict[str, Any]]:
        """
        Extract unanswered questions from discussion sections.
        
        Returns:
            List of unanswered questions with context
        """
        cache_key = "knowledge_gaps:unanswered_questions"
        cached = cache.get(cache_key)
        if cached:
            return cached
            
        documents = Document.objects.filter(doc_type__in=['paper', 'thesis'])
        questions = []
        
        # Patterns for finding questions in discussions
        question_patterns = [
            r"(?:remains?|is|are)\s+(?:to be|still|yet)?\s*(?:unclear|unknown|elusive)",
            r"(?:future|further)\s+(?:studies|research|work)\s+(?:should|could|might|will)",
            r"(?:how|why|what|when|where|which)\s+[^.?!]*\?",
            r"(?:remains?|is)\s+(?:a|an)?\s*(?:open|unanswered|unresolved)\s+question",
            r"(?:warrants?|requires?|needs?)\s+(?:further|additional)\s+(?:investigation|study)",
        ]
        
        for doc in documents:
            # Extract discussion section
            discussion = self._extract_discussion_section(doc.content)
            if not discussion:
                continue
                
            # Find questions and future work mentions
            for pattern in question_patterns:
                matches = re.finditer(pattern, discussion, re.IGNORECASE)
                for match in matches:
                    context = self._extract_question_context(match, discussion)
                    
                    questions.append({
                        "question": context['question'],
                        "context": context['context'],
                        "source_paper": doc.title,
                        "source_id": doc.id,
                        "question_type": context['type'],
                        "keywords": self._extract_keywords(context['question']),
                        "potential_approaches": self._suggest_approaches(context['question'])
                    })
        
        # Remove duplicates and rank by importance
        unique_questions = self._deduplicate_questions(questions)
        ranked_questions = self._rank_questions_by_importance(unique_questions)
        
        cache.set(cache_key, ranked_questions[:25], 3600)  # Top 25, cache 1 hour
        return ranked_questions[:25]
        
    def track_topic_evolution(self, time_window: int = 365) -> Dict[str, Any]:
        """
        Track how research topics have evolved over time.
        
        Args:
            time_window: Days to analyze (default: 365)
            
        Returns:
            Topic evolution analysis
        """
        cache_key = f"knowledge_gaps:topic_evolution:{time_window}"
        cached = cache.get(cache_key)
        if cached:
            return cached
            
        end_date = timezone.now()
        start_date = end_date - timedelta(days=time_window)
        
        # Get documents in time window
        documents = Document.objects.filter(
            created_at__range=[start_date, end_date]
        ).order_by('created_at')
        
        if not documents:
            return {"error": "No documents in time window"}
            
        # Analyze topics over time periods
        time_periods = self._create_time_periods(start_date, end_date, periods=6)
        topic_timeline = []
        
        for i, (period_start, period_end) in enumerate(time_periods):
            period_docs = documents.filter(
                created_at__range=[period_start, period_end]
            )
            
            if period_docs:
                topics = self._extract_topics(period_docs)
                topic_timeline.append({
                    "period": f"Period {i+1}",
                    "start": period_start.isoformat(),
                    "end": period_end.isoformat(),
                    "document_count": period_docs.count(),
                    "topics": topics,
                    "emerging_topics": self._identify_emerging_topics(topics, topic_timeline)
                })
        
        # Analyze trends
        evolution_analysis = {
            "timeline": topic_timeline,
            "trending_up": self._identify_trending_topics(topic_timeline, direction="up"),
            "trending_down": self._identify_trending_topics(topic_timeline, direction="down"),
            "stable_topics": self._identify_stable_topics(topic_timeline),
            "topic_transitions": self._analyze_topic_transitions(topic_timeline),
            "predicted_future_topics": self._predict_future_topics(topic_timeline)
        }
        
        cache.set(cache_key, evolution_analysis, 7200)  # Cache for 2 hours
        return evolution_analysis
        
    def suggest_research_opportunities(self, 
                                     researcher_interests: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Suggest specific research opportunities based on gaps and trends.
        
        Args:
            researcher_interests: Optional list of researcher's interests
            
        Returns:
            List of research opportunity suggestions
        """
        # Gather all gap analyses
        coverage = self.analyze_research_coverage()
        unexplored = self.identify_unexplored_combinations()
        unvalidated = self.detect_missing_validations()
        questions = self.find_unanswered_questions()
        evolution = self.track_topic_evolution()
        
        opportunities = []
        
        # Generate opportunities from different sources
        # 1. From unexplored combinations
        for combo in unexplored[:5]:
            opportunities.append({
                "type": "unexplored_combination",
                "title": f"Explore {self._format_combination_title(combo['combination'])}",
                "description": combo['rationale'],
                "impact_score": combo['impact_score'],
                "difficulty": self._estimate_difficulty(combo),
                "resources_needed": self._estimate_resources(combo),
                "related_work": combo['related_papers']
            })
        
        # 2. From missing validations
        for validation in unvalidated[:5]:
            opportunities.append({
                "type": "validation_needed",
                "title": f"Validate: {validation['claim'][:100]}...",
                "description": f"Experimental validation needed for claim from {validation['source_paper']}",
                "impact_score": validation['confidence'],
                "difficulty": "medium",
                "resources_needed": validation['potential_validation_methods'],
                "related_work": validation['related_work']
            })
        
        # 3. From unanswered questions
        for question in questions[:5]:
            opportunities.append({
                "type": "open_question",
                "title": f"Investigate: {question['question'][:100]}...",
                "description": question['context'],
                "impact_score": self._score_question_importance(question),
                "difficulty": self._estimate_question_difficulty(question),
                "resources_needed": question['potential_approaches'],
                "related_work": [question['source_paper']]
            })
        
        # 4. From emerging topics
        if 'trending_up' in evolution:
            for topic in evolution['trending_up'][:3]:
                opportunities.append({
                    "type": "emerging_topic",
                    "title": f"Contribute to emerging area: {topic['topic']}",
                    "description": f"This topic shows {topic['growth_rate']:.1%} growth",
                    "impact_score": topic['growth_rate'],
                    "difficulty": "varies",
                    "resources_needed": ["Literature review", "Experimental setup"],
                    "related_work": topic.get('recent_papers', [])
                })
        
        # Filter by researcher interests if provided
        if researcher_interests:
            opportunities = self._filter_by_interests(opportunities, researcher_interests)
        
        # Sort by combined score
        opportunities.sort(
            key=lambda x: x['impact_score'] * 0.6 + (1.0 - self._difficulty_to_score(x['difficulty'])) * 0.4,
            reverse=True
        )
        
        return opportunities[:10]  # Top 10 opportunities
        
    # Helper methods
    def _extract_research_areas(self, documents: List[Dict]) -> Dict[str, Any]:
        """Extract and categorize research areas from documents."""
        areas = defaultdict(int)
        area_documents = defaultdict(list)
        
        # Common RNA research areas
        area_keywords = {
            "RNA editing": ["editing", "ADAR", "A-to-I", "C-to-U"],
            "RNA splicing": ["splicing", "spliceosome", "intron", "exon"],
            "RNA interference": ["RNAi", "siRNA", "miRNA", "shRNA"],
            "CRISPR": ["CRISPR", "Cas9", "Cas13", "guide RNA", "gRNA"],
            "RNA structure": ["structure", "folding", "secondary structure", "tertiary"],
            "RNA therapeutics": ["therapeutic", "drug", "treatment", "clinical"],
            "RNA sequencing": ["RNA-seq", "sequencing", "transcriptome", "NGS"],
            "lncRNA": ["lncRNA", "long non-coding", "lincRNA"],
            "RNA metabolism": ["metabolism", "degradation", "stability", "turnover"],
            "RNA localization": ["localization", "transport", "trafficking", "compartment"]
        }
        
        for doc in documents:
            text = f"{doc['title']} {doc['abstract']} {doc.get('content', '')[:1000]}".lower()
            
            for area, keywords in area_keywords.items():
                if any(keyword.lower() in text for keyword in keywords):
                    areas[area] += 1
                    area_documents[area].append(doc['id'])
        
        return {
            "areas": dict(areas),
            "document_mapping": dict(area_documents),
            "total_areas": len(areas),
            "coverage_distribution": self._calculate_distribution(areas)
        }
        
    def _analyze_parameter_space(self, documents: List[Dict]) -> Dict[str, Any]:
        """Analyze experimental parameter space coverage."""
        parameters = defaultdict(set)
        
        # Common experimental parameters in RNA research
        param_patterns = {
            "temperature": r"(\d+)\s*°C|(\d+)\s*degrees",
            "concentration": r"(\d+\.?\d*)\s*(mM|μM|nM|mg/ml|μg/ml)",
            "time": r"(\d+)\s*(hours?|hrs?|minutes?|mins?|seconds?|s)\b",
            "pH": r"pH\s*(\d+\.?\d*)",
            "cell_type": r"(HEK293|HeLa|MCF-?7|A549|U2OS|MEF|ESC|iPSC)",
            "organism": r"(human|mouse|rat|zebrafish|drosophila|yeast|E\.\s*coli)",
            "technique": r"(qPCR|RT-PCR|Western|FACS|microscopy|CLIP|ChIP)"
        }
        
        for doc in documents:
            content = doc.get('content', '')[:5000]  # Analyze first 5000 chars
            
            for param_type, pattern in param_patterns.items():
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    value = match.group(1) if match.group(1) else match.group(0)
                    parameters[param_type].add(value)
        
        return {
            "parameters": {k: list(v) for k, v in parameters.items()},
            "parameter_counts": {k: len(v) for k, v in parameters.items()},
            "total_unique_values": sum(len(v) for v in parameters.values()),
            "sparsity": self._calculate_parameter_sparsity(parameters)
        }
        
    def _analyze_temporal_evolution(self, documents: List[Dict]) -> Dict[str, Any]:
        """Analyze how research has evolved over time."""
        # Group documents by time period
        time_groups = defaultdict(list)
        
        for doc in documents:
            date = doc.get('created_at')
            if date:
                year_month = date.strftime('%Y-%m')
                time_groups[year_month].append(doc)
        
        # Analyze topics per time period
        evolution = []
        for period, docs in sorted(time_groups.items()):
            topics = self._extract_topics_from_docs(docs)
            evolution.append({
                "period": period,
                "document_count": len(docs),
                "topics": topics,
                "diversity_score": self._calculate_topic_diversity(topics)
            })
        
        return {
            "timeline": evolution,
            "total_periods": len(evolution),
            "growth_rate": self._calculate_growth_rate(evolution)
        }
        
    def _identify_coverage_gaps(self, research_areas: Dict, parameter_space: Dict) -> List[Dict]:
        """Identify gaps in research coverage."""
        gaps = []
        
        # Check for underrepresented areas
        area_counts = research_areas['areas']
        avg_coverage = np.mean(list(area_counts.values())) if area_counts else 0
        
        for area, count in area_counts.items():
            if count < avg_coverage * 0.5:  # Less than 50% of average
                gaps.append({
                    "type": "underrepresented_area",
                    "area": area,
                    "current_coverage": count,
                    "average_coverage": avg_coverage,
                    "gap_severity": "high" if count < avg_coverage * 0.25 else "medium"
                })
        
        # Check for parameter combinations
        param_counts = parameter_space['parameter_counts']
        if len(param_counts) > 1:
            # Simple combination analysis
            for param1 in param_counts:
                for param2 in param_counts:
                    if param1 < param2:  # Avoid duplicates
                        combination_key = f"{param1}-{param2}"
                        gaps.append({
                            "type": "parameter_combination",
                            "combination": combination_key,
                            "individual_coverage": {
                                param1: param_counts[param1],
                                param2: param_counts[param2]
                            },
                            "gap_severity": "low"  # Would need actual combination count
                        })
        
        return gaps
        
    def _extract_experimental_parameters(self, content: str) -> Dict[str, Set[str]]:
        """Extract experimental parameters from methods section."""
        parameters = defaultdict(set)
        
        # Find methods section
        methods_section = self._extract_methods_section(content)
        if not methods_section:
            methods_section = content[:3000]  # Fallback to beginning
        
        # Parameter extraction patterns
        patterns = {
            "temperature": r"(\d+)\s*°C",
            "concentration": r"(\d+\.?\d*)\s*(mM|μM|nM)",
            "time": r"(\d+)\s*(hours?|hrs?|minutes?|mins?)",
            "cell_line": r"(HEK293|HeLa|MCF-?7|A549|U2OS)",
            "buffer": r"(PBS|DMEM|RPMI|Tris|HEPES)",
            "enzyme": r"(polymerase|ligase|kinase|phosphatase|nuclease)"
        }
        
        for param_type, pattern in patterns.items():
            matches = re.finditer(pattern, methods_section, re.IGNORECASE)
            for match in matches:
                parameters[param_type].add(match.group(0))
        
        return dict(parameters)
        
    def _extract_claims_and_hypotheses(self, content: str) -> List[Dict]:
        """Extract claims and hypotheses from paper content."""
        claims = []
        
        # Patterns for claims and hypotheses
        claim_patterns = [
            (r"we (?:demonstrate|show|prove|establish) that ([^.]+)", "demonstrated"),
            (r"our (?:results|data|findings) (?:suggest|indicate) that ([^.]+)", "suggested"),
            (r"we (?:hypothesize|propose|postulate) that ([^.]+)", "hypothesis"),
            (r"(?:surprisingly|interestingly|notably), ([^.]+)", "observation"),
            (r"for the first time, ([^.]+)", "novel_finding")
        ]
        
        for pattern, claim_type in claim_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                claim_text = match.group(1).strip()
                claims.append({
                    "text": claim_text,
                    "type": claim_type,
                    "confidence": self._assess_claim_confidence(claim_text, content),
                    "context": self._extract_surrounding_context(match, content)
                })
        
        return claims
        
    def _check_validation_status(self, claim: Dict, documents) -> Dict:
        """Check if a claim has been validated in other papers."""
        # Search for validations
        validation_keywords = ["validated", "confirmed", "verified", "reproduced", "replicated"]
        claim_keywords = self._extract_keywords(claim['text'])
        
        related_work = []
        validation_found = False
        
        for doc in documents:
            doc_text = f"{doc.title} {doc.abstract} {doc.content[:2000]}".lower()
            
            # Check if document mentions the claim keywords
            if any(keyword.lower() in doc_text for keyword in claim_keywords):
                # Check for validation language
                if any(val_keyword in doc_text for val_keyword in validation_keywords):
                    validation_found = True
                
                related_work.append({
                    "title": doc.title,
                    "id": doc.id,
                    "relevance": self._calculate_relevance(claim_keywords, doc_text)
                })
        
        # Sort by relevance
        related_work.sort(key=lambda x: x['relevance'], reverse=True)
        
        return {
            "status": "validated" if validation_found else "unvalidated",
            "related_work": related_work[:5],
            "suggested_methods": self._suggest_validation_methods(claim) if not validation_found else []
        }
        
    def _extract_discussion_section(self, content: str) -> Optional[str]:
        """Extract discussion section from paper."""
        # Common section headers
        discussion_patterns = [
            r"discussion\s*\n",
            r"discussion and conclusions?\s*\n",
            r"results and discussion\s*\n",
            r"concluding remarks\s*\n"
        ]
        
        for pattern in discussion_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                start = match.end()
                # Find next section or end
                next_section = re.search(
                    r"\n(?:methods|references|acknowledgments|supplementary)\s*\n",
                    content[start:],
                    re.IGNORECASE
                )
                end = start + next_section.start() if next_section else len(content)
                return content[start:end]
        
        return None
        
    def _extract_question_context(self, match, text: str) -> Dict:
        """Extract context around a question or future work mention."""
        start = max(0, match.start() - 200)
        end = min(len(text), match.end() + 200)
        context = text[start:end]
        
        # Determine question type
        question_text = match.group(0)
        question_type = "unknown"
        
        if "how" in question_text.lower():
            question_type = "mechanism"
        elif "why" in question_text.lower():
            question_type = "causation"
        elif "what" in question_text.lower():
            question_type = "identification"
        elif "future" in question_text.lower():
            question_type = "future_work"
        
        return {
            "question": question_text.strip(),
            "context": context.strip(),
            "type": question_type
        }
        
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text using TF-IDF."""
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                    'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        
        keywords = [w for w in words if len(w) > 3 and w not in stopwords]
        
        # Get most frequent
        keyword_counts = Counter(keywords)
        return [kw for kw, _ in keyword_counts.most_common(5)]
        
    def _suggest_approaches(self, question: str) -> List[str]:
        """Suggest potential approaches to answer a question."""
        approaches = []
        
        question_lower = question.lower()
        
        # Suggest based on question type
        if "mechanism" in question_lower or "how" in question_lower:
            approaches.extend([
                "Biochemical assays",
                "Structure-function analysis",
                "Mutagenesis studies",
                "Single-molecule experiments"
            ])
        elif "function" in question_lower or "role" in question_lower:
            approaches.extend([
                "Loss-of-function studies",
                "Gain-of-function experiments",
                "Phenotypic screening",
                "Proteomics analysis"
            ])
        elif "regulation" in question_lower:
            approaches.extend([
                "ChIP-seq analysis",
                "Expression profiling",
                "Promoter analysis",
                "Post-translational modification studies"
            ])
        else:
            approaches.extend([
                "Systematic literature review",
                "Experimental validation",
                "Computational modeling",
                "High-throughput screening"
            ])
        
        return approaches[:3]
        
    def _deduplicate_questions(self, questions: List[Dict]) -> List[Dict]:
        """Remove duplicate questions based on similarity."""
        if not questions:
            return []
            
        # Extract question texts
        question_texts = [q['question'] for q in questions]
        
        # Calculate similarity matrix
        if len(question_texts) > 1:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(question_texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Keep questions with low similarity to others
            unique_indices = []
            for i in range(len(questions)):
                is_unique = True
                for j in unique_indices:
                    if similarity_matrix[i][j] > 0.8:  # 80% similarity threshold
                        is_unique = False
                        break
                if is_unique:
                    unique_indices.append(i)
            
            return [questions[i] for i in unique_indices]
        
        return questions
        
    def _rank_questions_by_importance(self, questions: List[Dict]) -> List[Dict]:
        """Rank questions by potential importance and impact."""
        for question in questions:
            # Calculate importance score
            score = 0.0
            
            # Factor 1: Question type
            type_scores = {
                "mechanism": 0.9,
                "causation": 0.85,
                "identification": 0.7,
                "future_work": 0.6,
                "unknown": 0.5
            }
            score += type_scores.get(question['question_type'], 0.5) * 0.3
            
            # Factor 2: Number of keywords
            score += min(len(question['keywords']) / 5.0, 1.0) * 0.2
            
            # Factor 3: Number of potential approaches
            score += min(len(question['potential_approaches']) / 3.0, 1.0) * 0.2
            
            # Factor 4: Context length (longer context usually means more important)
            score += min(len(question['context']) / 500.0, 1.0) * 0.3
            
            question['importance_score'] = score
        
        # Sort by importance
        questions.sort(key=lambda x: x['importance_score'], reverse=True)
        
        return questions
        
    def _create_time_periods(self, start_date, end_date, periods: int) -> List[Tuple]:
        """Create evenly spaced time periods."""
        total_days = (end_date - start_date).days
        period_days = total_days / periods
        
        time_periods = []
        for i in range(periods):
            period_start = start_date + timedelta(days=i * period_days)
            period_end = start_date + timedelta(days=(i + 1) * period_days)
            time_periods.append((period_start, period_end))
        
        return time_periods
        
    def _extract_topics(self, documents) -> List[Dict]:
        """Extract topics from a set of documents."""
        # Combine all text
        all_text = []
        for doc in documents:
            text = f"{doc.title} {doc.abstract}"
            all_text.append(text)
        
        if not all_text:
            return []
        
        # Use TF-IDF to find important terms
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_text)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # Get top terms
            tfidf_scores = tfidf_matrix.sum(axis=0).A1
            top_indices = tfidf_scores.argsort()[-20:][::-1]
            
            topics = []
            for idx in top_indices:
                topics.append({
                    "term": feature_names[idx],
                    "score": float(tfidf_scores[idx]),
                    "document_frequency": int((tfidf_matrix[:, idx] > 0).sum())
                })
            
            return topics
        except:
            return []
            
    def _identify_emerging_topics(self, current_topics: List[Dict], 
                                history: List[Dict]) -> List[str]:
        """Identify newly emerging topics."""
        if not history:
            return []
            
        # Get topics from previous periods
        historical_terms = set()
        for period in history:
            for topic in period.get('topics', []):
                historical_terms.add(topic['term'])
        
        # Find new topics
        emerging = []
        for topic in current_topics:
            if topic['term'] not in historical_terms and topic['score'] > 0.5:
                emerging.append(topic['term'])
        
        return emerging[:5]
        
    def _identify_trending_topics(self, timeline: List[Dict], direction: str) -> List[Dict]:
        """Identify topics trending up or down."""
        if len(timeline) < 2:
            return []
            
        # Track topic scores across time
        topic_trends = defaultdict(list)
        
        for period in timeline:
            period_topics = {t['term']: t['score'] for t in period.get('topics', [])}
            
            # Add scores for all topics (0 if not present)
            all_topics = set()
            for p in timeline:
                all_topics.update(t['term'] for t in p.get('topics', []))
            
            for topic in all_topics:
                topic_trends[topic].append(period_topics.get(topic, 0.0))
        
        # Calculate trends
        trending = []
        for topic, scores in topic_trends.items():
            if len(scores) >= 2:
                # Simple linear regression
                x = np.arange(len(scores))
                y = np.array(scores)
                
                if np.sum(y) > 0:  # Skip topics with all zeros
                    slope = np.polyfit(x, y, 1)[0]
                    
                    if (direction == "up" and slope > 0) or (direction == "down" and slope < 0):
                        trending.append({
                            "topic": topic,
                            "growth_rate": float(slope),
                            "recent_score": float(scores[-1]),
                            "trend_strength": abs(float(slope)) / (np.mean(y) + 0.001)
                        })
        
        # Sort by trend strength
        trending.sort(key=lambda x: x['trend_strength'], reverse=True)
        
        return trending[:10]
        
    def _identify_stable_topics(self, timeline: List[Dict]) -> List[Dict]:
        """Identify consistently present topics."""
        if not timeline:
            return []
            
        # Count topic appearances
        topic_appearances = defaultdict(int)
        topic_scores = defaultdict(list)
        
        for period in timeline:
            for topic in period.get('topics', []):
                topic_appearances[topic['term']] += 1
                topic_scores[topic['term']].append(topic['score'])
        
        # Find stable topics (appear in most periods)
        stable = []
        min_appearances = len(timeline) * 0.7  # Present in 70% of periods
        
        for topic, count in topic_appearances.items():
            if count >= min_appearances:
                scores = topic_scores[topic]
                stable.append({
                    "topic": topic,
                    "consistency": count / len(timeline),
                    "average_score": np.mean(scores),
                    "score_variance": np.var(scores)
                })
        
        # Sort by consistency and low variance
        stable.sort(key=lambda x: x['consistency'] - x['score_variance'] * 0.1, reverse=True)
        
        return stable[:10]
        
    def _analyze_topic_transitions(self, timeline: List[Dict]) -> List[Dict]:
        """Analyze how topics transition or evolve."""
        transitions = []
        
        for i in range(len(timeline) - 1):
            current_topics = {t['term'] for t in timeline[i].get('topics', [])}
            next_topics = {t['term'] for t in timeline[i + 1].get('topics', [])}
            
            # Find topics that disappeared
            disappeared = current_topics - next_topics
            
            # Find topics that appeared
            appeared = next_topics - current_topics
            
            if disappeared and appeared:
                # Look for potential transitions
                for old_topic in disappeared:
                    for new_topic in appeared:
                        similarity = self._calculate_topic_similarity(old_topic, new_topic)
                        if similarity > 0.5:
                            transitions.append({
                                "from": old_topic,
                                "to": new_topic,
                                "period": f"{timeline[i]['period']} -> {timeline[i+1]['period']}",
                                "similarity": similarity
                            })
        
        return transitions
        
    def _predict_future_topics(self, timeline: List[Dict]) -> List[Dict]:
        """Predict potential future research topics."""
        if not timeline:
            return []
            
        # Get trending topics
        trending_up = self._identify_trending_topics(timeline, "up")
        
        predictions = []
        for trend in trending_up[:5]:
            # Simple prediction based on trend
            predictions.append({
                "topic": trend['topic'],
                "confidence": min(trend['trend_strength'] * 0.3, 0.9),
                "rationale": f"Shows {trend['growth_rate']:.2f} growth rate",
                "suggested_focus": self._suggest_research_focus(trend['topic'])
            })
        
        # Add predictions based on topic combinations
        recent_topics = timeline[-1].get('topics', []) if timeline else []
        for i, topic1 in enumerate(recent_topics[:5]):
            for topic2 in recent_topics[i+1:6]:
                combined = f"{topic1['term']}-{topic2['term']}"
                predictions.append({
                    "topic": combined,
                    "confidence": 0.4,
                    "rationale": "Potential intersection of active research areas",
                    "suggested_focus": f"Explore connections between {topic1['term']} and {topic2['term']}"
                })
        
        return predictions[:8]
        
    def _calculate_coverage_score(self, research_areas: Dict, parameter_space: Dict) -> float:
        """Calculate overall coverage score."""
        # Area coverage
        area_count = len(research_areas.get('areas', {}))
        area_score = min(area_count / 10.0, 1.0)  # Normalize to 10 areas
        
        # Parameter coverage
        param_count = parameter_space.get('total_unique_values', 0)
        param_score = min(param_count / 100.0, 1.0)  # Normalize to 100 values
        
        # Distribution score (penalize uneven distribution)
        distribution = research_areas.get('coverage_distribution', {})
        if distribution:
            variance = distribution.get('variance', 1.0)
            distribution_score = 1.0 / (1.0 + variance * 0.1)
        else:
            distribution_score = 0.5
        
        # Combined score
        return (area_score * 0.4 + param_score * 0.3 + distribution_score * 0.3)
        
    def _calculate_distribution(self, areas: Dict[str, int]) -> Dict:
        """Calculate distribution statistics."""
        if not areas:
            return {"mean": 0, "variance": 0, "std": 0}
            
        values = list(areas.values())
        return {
            "mean": np.mean(values),
            "variance": np.var(values),
            "std": np.std(values),
            "min": min(values),
            "max": max(values)
        }
        
    def _calculate_parameter_sparsity(self, parameters: Dict) -> float:
        """Calculate how sparse the parameter space is."""
        if not parameters:
            return 1.0
            
        # Count total possible combinations
        total_values = [len(values) for values in parameters.values()]
        if not total_values:
            return 1.0
            
        # Estimate sparsity (simplified)
        max_combinations = np.prod(total_values[:3]) if len(total_values) >= 3 else np.prod(total_values)
        
        # Assume we've explored very few combinations
        explored_estimate = sum(total_values) * 2  # Rough estimate
        
        return 1.0 - min(explored_estimate / max_combinations, 1.0)
        
    def _generate_unexplored_combinations(self, 
                                        all_parameters: Dict[str, Set],
                                        existing_combinations: List) -> List[Tuple]:
        """Generate potentially interesting unexplored combinations."""
        # Convert existing combinations to a set for faster lookup
        existing_set = set(existing_combinations)
        
        unexplored = []
        
        # Focus on 2-3 parameter combinations for feasibility
        param_categories = list(all_parameters.keys())
        
        # 2-parameter combinations
        for i, cat1 in enumerate(param_categories):
            for cat2 in param_categories[i+1:]:
                for val1 in list(all_parameters[cat1])[:5]:  # Limit values
                    for val2 in list(all_parameters[cat2])[:5]:
                        combo = tuple(sorted([(cat1, (val1,)), (cat2, (val2,))]))
                        if combo not in existing_set:
                            unexplored.append(combo)
        
        # Sample to avoid too many combinations
        if len(unexplored) > 100:
            import random
            unexplored = random.sample(unexplored, 100)
        
        return unexplored
        
    def _score_combination_impact(self, combination: Tuple, documents) -> float:
        """Score potential impact of an unexplored combination."""
        # Extract parameter categories
        categories = [item[0] for item in combination]
        
        # Base score on parameter importance
        importance_scores = {
            "cell_type": 0.8,
            "technique": 0.9,
            "organism": 0.7,
            "temperature": 0.5,
            "concentration": 0.6,
            "time": 0.5
        }
        
        base_score = sum(importance_scores.get(cat, 0.5) for cat in categories) / len(categories)
        
        # Adjust based on novelty (simplified)
        novelty_bonus = 0.2 if len(categories) > 2 else 0.1
        
        return min(base_score + novelty_bonus, 1.0)
        
    def _generate_combination_rationale(self, combination: Tuple) -> str:
        """Generate explanation for why a combination is interesting."""
        params = dict(combination)
        
        rationales = []
        
        if "cell_type" in params and "technique" in params:
            rationales.append(f"Testing {params['technique'][0]} in {params['cell_type'][0]} cells could reveal cell-type specific effects")
        
        if "temperature" in params and "time" in params:
            rationales.append(f"The combination of {params['temperature'][0]} and {params['time'][0]} may affect reaction kinetics")
        
        if "organism" in params:
            rationales.append(f"Cross-species validation in {params['organism'][0]} would strengthen findings")
        
        if not rationales:
            param_list = ", ".join(f"{k}: {v[0]}" for k, v in params.items())
            rationales.append(f"Exploring {param_list} could reveal new parameter dependencies")
        
        return ". ".join(rationales)
        
    def _find_related_papers(self, combination: Tuple, documents) -> List[Dict]:
        """Find papers related to the parameter combination."""
        related = []
        params = dict(combination)
        
        for doc in documents[:50]:  # Limit search
            text = f"{doc.title} {doc.abstract}".lower()
            
            # Count how many parameters match
            matches = 0
            for category, values in params.items():
                if any(str(val).lower() in text for val in values):
                    matches += 1
            
            if matches > 0:
                related.append({
                    "title": doc.title,
                    "id": doc.id,
                    "match_count": matches
                })
        
        # Sort by match count
        related.sort(key=lambda x: x['match_count'], reverse=True)
        
        return related[:5]
        
    def _extract_methods_section(self, content: str) -> Optional[str]:
        """Extract methods section from paper content."""
        # Common methods section headers
        methods_patterns = [
            r"materials? and methods?\s*\n",
            r"experimental procedures?\s*\n",
            r"methods?\s*\n",
            r"experimental section\s*\n"
        ]
        
        for pattern in methods_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                start = match.end()
                # Find next section
                next_section = re.search(
                    r"\n(?:results|discussion|references|acknowledgments)\s*\n",
                    content[start:],
                    re.IGNORECASE
                )
                end = start + next_section.start() if next_section else start + 3000
                return content[start:end]
        
        return None
        
    def _assess_claim_confidence(self, claim_text: str, full_content: str) -> float:
        """Assess confidence level of a claim."""
        confidence = 0.5  # Base confidence
        
        # Look for supporting evidence
        if "p < 0.0" in full_content or "significant" in claim_text:
            confidence += 0.2
        
        if "data not shown" in claim_text or "preliminary" in claim_text:
            confidence -= 0.2
        
        if "multiple" in claim_text or "several" in claim_text:
            confidence += 0.1
        
        # Hedging language reduces confidence
        hedging_words = ["might", "could", "possibly", "perhaps", "may"]
        if any(word in claim_text.lower() for word in hedging_words):
            confidence -= 0.15
        
        return max(0.1, min(0.9, confidence))
        
    def _extract_surrounding_context(self, match, content: str, context_size: int = 200) -> str:
        """Extract context around a match."""
        start = max(0, match.start() - context_size)
        end = min(len(content), match.end() + context_size)
        return content[start:end].strip()
        
    def _calculate_relevance(self, keywords: List[str], text: str) -> float:
        """Calculate relevance score based on keyword matches."""
        if not keywords:
            return 0.0
            
        text_lower = text.lower()
        matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        
        return matches / len(keywords)
        
    def _suggest_validation_methods(self, claim: Dict) -> List[str]:
        """Suggest methods to validate a claim."""
        methods = []
        claim_text = claim['text'].lower()
        
        if "binding" in claim_text or "interaction" in claim_text:
            methods.extend(["Co-immunoprecipitation", "Pull-down assay", "Surface plasmon resonance"])
        elif "expression" in claim_text or "transcription" in claim_text:
            methods.extend(["qRT-PCR", "Western blot", "RNA-seq"])
        elif "localization" in claim_text:
            methods.extend(["Immunofluorescence", "Cell fractionation", "Live cell imaging"])
        elif "activity" in claim_text or "function" in claim_text:
            methods.extend(["Enzymatic assay", "Functional complementation", "Phenotypic analysis"])
        else:
            methods.extend(["Independent replication", "Alternative methodology", "Extended sample size"])
        
        return methods[:3]
        
    def _extract_topics_from_docs(self, docs: List[Dict]) -> List[Dict]:
        """Extract topics from a list of document dictionaries."""
        if not docs:
            return []
            
        # Combine text from documents
        texts = []
        for doc in docs:
            text = f"{doc.get('title', '')} {doc.get('abstract', '')}"
            texts.append(text)
        
        if not texts:
            return []
            
        try:
            # Use TF-IDF
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # Get top terms
            scores = tfidf_matrix.sum(axis=0).A1
            top_indices = scores.argsort()[-10:][::-1]
            
            topics = []
            for idx in top_indices:
                topics.append({
                    "term": feature_names[idx],
                    "score": float(scores[idx])
                })
            
            return topics
        except:
            return []
            
    def _calculate_topic_diversity(self, topics: List[Dict]) -> float:
        """Calculate diversity score for topics."""
        if not topics:
            return 0.0
            
        # Simple diversity based on number of unique topics
        return min(len(topics) / 10.0, 1.0)
        
    def _calculate_growth_rate(self, evolution: List[Dict]) -> float:
        """Calculate growth rate over time periods."""
        if len(evolution) < 2:
            return 0.0
            
        # Simple growth calculation
        first_count = evolution[0]['document_count']
        last_count = evolution[-1]['document_count']
        
        if first_count == 0:
            return 1.0 if last_count > 0 else 0.0
            
        return (last_count - first_count) / first_count
        
    def _format_combination_title(self, combination: Dict) -> str:
        """Format parameter combination for display."""
        parts = []
        for param, values in combination.items():
            if isinstance(values, tuple):
                value_str = values[0] if len(values) == 1 else f"{values[0]}-{values[1]}"
            else:
                value_str = str(values)
            parts.append(f"{param}: {value_str}")
        
        return " with ".join(parts)
        
    def _estimate_difficulty(self, combo: Dict) -> str:
        """Estimate difficulty of exploring a combination."""
        param_count = len(combo['combination'])
        
        if param_count <= 2:
            return "low"
        elif param_count <= 3:
            return "medium"
        else:
            return "high"
            
    def _estimate_resources(self, combo: Dict) -> List[str]:
        """Estimate resources needed for a combination."""
        resources = []
        params = combo['combination']
        
        if 'cell_type' in params:
            resources.append("Cell culture facility")
        if 'organism' in params:
            resources.append("Animal facility")
        if 'technique' in params:
            resources.append("Specialized equipment")
        
        resources.append("Reagents and consumables")
        
        return resources
        
    def _score_question_importance(self, question: Dict) -> float:
        """Score importance of an unanswered question."""
        base_score = 0.5
        
        # Type-based scoring
        type_scores = {
            "mechanism": 0.3,
            "causation": 0.25,
            "identification": 0.2,
            "future_work": 0.15
        }
        
        base_score += type_scores.get(question['question_type'], 0.1)
        
        # Keyword count bonus
        keyword_bonus = min(len(question['keywords']) * 0.05, 0.2)
        
        return min(base_score + keyword_bonus, 1.0)
        
    def _estimate_question_difficulty(self, question: Dict) -> str:
        """Estimate difficulty of answering a question."""
        approaches = question['potential_approaches']
        
        if len(approaches) <= 2:
            return "high"
        elif len(approaches) <= 3:
            return "medium"
        else:
            return "low"
            
    def _difficulty_to_score(self, difficulty: str) -> float:
        """Convert difficulty to numeric score."""
        scores = {
            "low": 0.3,
            "medium": 0.5,
            "high": 0.7,
            "varies": 0.5
        }
        return scores.get(difficulty, 0.5)
        
    def _calculate_topic_similarity(self, topic1: str, topic2: str) -> float:
        """Calculate similarity between two topics."""
        # Simple character-based similarity
        set1 = set(topic1.lower().split())
        set2 = set(topic2.lower().split())
        
        if not set1 or not set2:
            return 0.0
            
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
        
    def _suggest_research_focus(self, topic: str) -> str:
        """Suggest specific research focus for a topic."""
        topic_lower = topic.lower()
        
        if "rna" in topic_lower:
            return "Investigate novel RNA modifications and their functional implications"
        elif "crispr" in topic_lower:
            return "Develop improved CRISPR variants with enhanced specificity"
        elif "therapeutic" in topic_lower:
            return "Explore clinical translation and safety profiles"
        elif "structure" in topic_lower:
            return "Determine high-resolution structures and dynamics"
        else:
            return f"Conduct systematic investigation of {topic} mechanisms"
            
    def _filter_by_interests(self, opportunities: List[Dict], 
                           interests: List[str]) -> List[Dict]:
        """Filter opportunities by researcher interests."""
        filtered = []
        
        for opp in opportunities:
            # Check if opportunity matches any interest
            opp_text = f"{opp['title']} {opp['description']}".lower()
            
            for interest in interests:
                if interest.lower() in opp_text:
                    filtered.append(opp)
                    break
        
        return filtered if filtered else opportunities  # Return all if no matches