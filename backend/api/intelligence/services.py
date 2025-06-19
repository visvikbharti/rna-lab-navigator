import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from datetime import datetime, timedelta
import json

from django.db.models import Q, Count, Avg
from api.models import Document
from api.search.services import SearchService
# from api.llm.local_llm import LLMService  # Not implemented yet
from .models import (
    ResearchHypothesis, ExperimentPrediction, 
    CrossStudyInsight, ResearchTimeline
)

logger = logging.getLogger(__name__)


class HypothesisGenerator:
    """Generate novel research hypotheses from literature analysis"""
    
    def __init__(self):
        # self.llm_service = LLMService()  # Not implemented yet
        self.search_service = SearchService()
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    
    def generate_hypotheses(self, domain: str, recent_papers: Optional[List[Document]] = None) -> List[ResearchHypothesis]:
        """Generate hypotheses based on domain and recent papers"""
        
        # Get relevant papers if not provided
        if not recent_papers:
            recent_papers = self._get_recent_papers(domain)
        
        # Analyze knowledge gaps
        knowledge_gaps = self._identify_knowledge_gaps(recent_papers)
        
        # Find contradictions and unexplored connections
        contradictions = self._find_contradictions(recent_papers)
        connections = self._find_unexplored_connections(recent_papers)
        
        # Generate hypotheses
        hypotheses = []
        
        # Gap-based hypotheses
        for gap in knowledge_gaps[:3]:  # Top 3 gaps
            hypothesis = self._generate_gap_hypothesis(gap, recent_papers)
            if hypothesis:
                hypotheses.append(hypothesis)
        
        # Contradiction-based hypotheses
        for contradiction in contradictions[:2]:
            hypothesis = self._generate_contradiction_hypothesis(contradiction, recent_papers)
            if hypothesis:
                hypotheses.append(hypothesis)
        
        # Connection-based hypotheses
        for connection in connections[:2]:
            hypothesis = self._generate_connection_hypothesis(connection, recent_papers)
            if hypothesis:
                hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _get_recent_papers(self, domain: str, limit: int = 50) -> List[Document]:
        """Get recent papers in the domain"""
        try:
            # Search for papers in the domain
            results = self.search_service.search(
                query=f"RNA {domain} recent advances mechanisms",
                doc_types=['paper'],
                limit=limit
            )
            
            return [r['document'] for r in results['results']]
        except Exception as e:
            logger.error(f"Error fetching recent papers: {e}")
            return []
    
    def _identify_knowledge_gaps(self, papers: List[Document]) -> List[Dict[str, Any]]:
        """Identify gaps in current knowledge"""
        
        # Extract all discussed topics
        all_text = " ".join([p.content for p in papers])
        
        # Common RNA research areas that should be covered
        expected_topics = [
            "mechanism", "structure", "function", "regulation",
            "modification", "interaction", "disease", "therapeutic",
            "evolution", "biogenesis", "localization", "stability"
        ]
        
        gaps = []
        
        # Check coverage of each topic
        for topic in expected_topics:
            coverage = self._calculate_topic_coverage(topic, papers)
            if coverage < 0.3:  # Low coverage threshold
                gap = {
                    'topic': topic,
                    'coverage': coverage,
                    'related_papers': self._find_topic_papers(topic, papers)[:3]
                }
                gaps.append(gap)
        
        # Use LLM to identify more nuanced gaps
        prompt = f"""
        Analyze these RNA research papers and identify 3 major knowledge gaps:
        
        Papers analyzed: {len(papers)}
        Topics covered: {', '.join([p.title[:50] for p in papers[:5]])}...
        
        Identify specific gaps in:
        1. Mechanistic understanding
        2. Experimental techniques
        3. Clinical applications
        
        Format: JSON list of gaps with 'area', 'description', and 'importance'
        """
        
        try:
            llm_gaps = self.llm_service.generate(prompt, max_tokens=500)
            parsed_gaps = json.loads(llm_gaps)
            
            for llm_gap in parsed_gaps:
                gaps.append({
                    'topic': llm_gap['area'],
                    'description': llm_gap['description'],
                    'importance': llm_gap.get('importance', 0.5)
                })
        except Exception as e:
            logger.error(f"Error using LLM for gap analysis: {e}")
        
        return sorted(gaps, key=lambda x: x.get('importance', x.get('coverage', 0)), reverse=True)
    
    def _find_contradictions(self, papers: List[Document]) -> List[Dict[str, Any]]:
        """Find contradictory results in papers"""
        contradictions = []
        
        # Group papers by similar topics
        paper_groups = self._group_papers_by_topic(papers)
        
        for topic, topic_papers in paper_groups.items():
            if len(topic_papers) < 2:
                continue
            
            # Compare conclusions between papers
            for i, paper1 in enumerate(topic_papers):
                for paper2 in topic_papers[i+1:]:
                    contradiction_score = self._calculate_contradiction_score(paper1, paper2)
                    
                    if contradiction_score > 0.7:
                        contradictions.append({
                            'topic': topic,
                            'paper1': paper1,
                            'paper2': paper2,
                            'score': contradiction_score,
                            'details': self._extract_contradiction_details(paper1, paper2)
                        })
        
        return sorted(contradictions, key=lambda x: x['score'], reverse=True)
    
    def _find_unexplored_connections(self, papers: List[Document]) -> List[Dict[str, Any]]:
        """Find potential connections between disparate research areas"""
        connections = []
        
        # Build a knowledge graph
        knowledge_graph = self._build_knowledge_graph(papers)
        
        # Find nodes that should be connected but aren't
        all_nodes = list(knowledge_graph.nodes())
        
        for i, node1 in enumerate(all_nodes):
            for node2 in all_nodes[i+1:]:
                if not knowledge_graph.has_edge(node1, node2):
                    # Calculate potential connection strength
                    connection_strength = self._calculate_connection_potential(
                        node1, node2, knowledge_graph, papers
                    )
                    
                    if connection_strength > 0.6:
                        connections.append({
                            'concept1': node1,
                            'concept2': node2,
                            'strength': connection_strength,
                            'rationale': self._generate_connection_rationale(node1, node2, papers)
                        })
        
        return sorted(connections, key=lambda x: x['strength'], reverse=True)
    
    def _generate_gap_hypothesis(self, gap: Dict[str, Any], papers: List[Document]) -> Optional[ResearchHypothesis]:
        """Generate hypothesis to address a knowledge gap"""
        
        prompt = f"""
        Generate a testable hypothesis to address this knowledge gap in RNA research:
        
        Gap: {gap.get('description', gap['topic'])}
        Current coverage: {gap.get('coverage', 'Low')}
        
        Consider:
        1. What specific mechanism or relationship could explain this gap?
        2. How could this be experimentally tested?
        3. What would be the impact of understanding this?
        
        Format the response as JSON with:
        - title: Concise hypothesis statement
        - description: Detailed explanation
        - rationale: Why this is important
        - experimental_approaches: List of 3-5 specific experiments
        - expected_outcomes: What we might discover
        """
        
        try:
            response = self.llm_service.generate(prompt, max_tokens=600)
            hypothesis_data = json.loads(response)
            
            # Create hypothesis object
            hypothesis = ResearchHypothesis(
                title=hypothesis_data['title'],
                description=hypothesis_data['description'],
                rationale=hypothesis_data['rationale'],
                testability_score=0.8,  # High for gap-based
                novelty_score=0.9,      # Very novel
                impact_score=self._calculate_impact_score(hypothesis_data),
                knowledge_gaps=[gap],
                experimental_approaches=hypothesis_data['experimental_approaches']
            )
            
            # Add supporting papers
            if 'related_papers' in gap:
                hypothesis.supporting_papers.set(gap['related_papers'])
            
            return hypothesis
            
        except Exception as e:
            logger.error(f"Error generating gap hypothesis: {e}")
            return None
    
    def _generate_contradiction_hypothesis(self, contradiction: Dict[str, Any], papers: List[Document]) -> Optional[ResearchHypothesis]:
        """Generate hypothesis to resolve contradictory findings"""
        
        paper1 = contradiction['paper1']
        paper2 = contradiction['paper2']
        
        prompt = f"""
        Generate a hypothesis to resolve these contradictory findings:
        
        Paper 1: {paper1.title}
        Key finding: {contradiction['details'].get('finding1', 'N/A')}
        
        Paper 2: {paper2.title}  
        Key finding: {contradiction['details'].get('finding2', 'N/A')}
        
        Propose a unifying hypothesis that could explain both results.
        Consider: experimental conditions, cell types, RNA isoforms, or temporal dynamics.
        
        Format as JSON with:
        - title: Hypothesis statement
        - description: How this resolves the contradiction
        - rationale: Scientific basis
        - experimental_approaches: Experiments to test this
        - predictions: What each experiment should show
        """
        
        try:
            response = self.llm_service.generate(prompt, max_tokens=600)
            hypothesis_data = json.loads(response)
            
            hypothesis = ResearchHypothesis(
                title=hypothesis_data['title'],
                description=hypothesis_data['description'],
                rationale=hypothesis_data['rationale'],
                testability_score=0.9,  # Very testable
                novelty_score=0.7,      # Moderately novel
                impact_score=0.8,       # High impact if resolved
                knowledge_gaps=[{'type': 'contradiction', 'details': contradiction}],
                experimental_approaches=hypothesis_data['experimental_approaches']
            )
            
            hypothesis.supporting_papers.add(paper1)
            hypothesis.contradicting_papers.add(paper2)
            
            return hypothesis
            
        except Exception as e:
            logger.error(f"Error generating contradiction hypothesis: {e}")
            return None
    
    def _generate_connection_hypothesis(self, connection: Dict[str, Any], papers: List[Document]) -> Optional[ResearchHypothesis]:
        """Generate hypothesis exploring unexplored connections"""
        
        prompt = f"""
        Generate a hypothesis connecting these RNA research concepts:
        
        Concept 1: {connection['concept1']}
        Concept 2: {connection['concept2']}
        Connection rationale: {connection['rationale']}
        
        Create a specific, testable hypothesis about how these might be related.
        Focus on molecular mechanisms, regulatory networks, or functional relationships.
        
        Format as JSON with:
        - title: Clear hypothesis statement
        - description: Detailed mechanism
        - rationale: Why this connection matters
        - experimental_approaches: How to test this connection
        - potential_applications: If proven true
        """
        
        try:
            response = self.llm_service.generate(prompt, max_tokens=600)
            hypothesis_data = json.loads(response)
            
            hypothesis = ResearchHypothesis(
                title=hypothesis_data['title'],
                description=hypothesis_data['description'],
                rationale=hypothesis_data['rationale'],
                testability_score=0.7,  # Moderate testability
                novelty_score=0.95,     # Extremely novel
                impact_score=self._calculate_impact_score(hypothesis_data),
                knowledge_gaps=[{'type': 'unexplored_connection', 'details': connection}],
                experimental_approaches=hypothesis_data['experimental_approaches']
            )
            
            return hypothesis
            
        except Exception as e:
            logger.error(f"Error generating connection hypothesis: {e}")
            return None
    
    def _calculate_topic_coverage(self, topic: str, papers: List[Document]) -> float:
        """Calculate how well a topic is covered in papers"""
        coverage_count = 0
        
        for paper in papers:
            if topic.lower() in paper.content.lower():
                # More sophisticated: count frequency and context
                topic_frequency = paper.content.lower().count(topic.lower())
                coverage_count += min(topic_frequency / 10, 1.0)  # Normalize
        
        return coverage_count / len(papers) if papers else 0
    
    def _find_topic_papers(self, topic: str, papers: List[Document]) -> List[Document]:
        """Find papers related to a specific topic"""
        topic_papers = []
        
        for paper in papers:
            if topic.lower() in paper.content.lower():
                topic_papers.append(paper)
        
        # Sort by relevance (simple frequency-based)
        topic_papers.sort(
            key=lambda p: p.content.lower().count(topic.lower()), 
            reverse=True
        )
        
        return topic_papers
    
    def _group_papers_by_topic(self, papers: List[Document]) -> Dict[str, List[Document]]:
        """Group papers by their main topics"""
        if not papers:
            return {}
        
        # Extract text for clustering
        texts = [p.content[:2000] for p in papers]  # First 2000 chars
        
        # TF-IDF vectorization
        try:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Simple clustering based on similarity
            groups = defaultdict(list)
            
            for i, paper in enumerate(papers):
                # Find most similar papers
                similarities = cosine_similarity(tfidf_matrix[i:i+1], tfidf_matrix).flatten()
                similar_indices = np.where(similarities > 0.3)[0]
                
                # Use first similar paper's title as group key (simplified)
                if len(similar_indices) > 1:
                    group_key = f"group_{similar_indices[0]}"
                    groups[group_key].append(paper)
            
            return dict(groups)
            
        except Exception as e:
            logger.error(f"Error grouping papers: {e}")
            return {'all': papers}
    
    def _calculate_contradiction_score(self, paper1: Document, paper2: Document) -> float:
        """Calculate how contradictory two papers are"""
        
        # Simple heuristic: look for opposite conclusions
        contradiction_keywords = [
            ('increases', 'decreases'), ('upregulates', 'downregulates'),
            ('promotes', 'inhibits'), ('enhances', 'suppresses'),
            ('positive', 'negative'), ('required', 'dispensable')
        ]
        
        score = 0.0
        paper1_lower = paper1.content.lower()
        paper2_lower = paper2.content.lower()
        
        for word1, word2 in contradiction_keywords:
            if word1 in paper1_lower and word2 in paper2_lower:
                score += 0.2
            elif word2 in paper1_lower and word1 in paper2_lower:
                score += 0.2
        
        return min(score, 1.0)
    
    def _extract_contradiction_details(self, paper1: Document, paper2: Document) -> Dict[str, str]:
        """Extract specific contradictory findings"""
        
        # This would ideally use NLP to extract findings
        # For now, return paper titles as placeholder
        return {
            'finding1': paper1.title,
            'finding2': paper2.title,
            'domain': 'RNA regulation'  # Placeholder
        }
    
    def _build_knowledge_graph(self, papers: List[Document]) -> nx.Graph:
        """Build a graph of concepts from papers"""
        G = nx.Graph()
        
        # Extract key concepts (simplified - would use NER in production)
        concepts = set()
        for paper in papers:
            # Extract RNA-related terms
            words = paper.content.lower().split()
            for word in words:
                if any(term in word for term in ['rna', 'mirna', 'lncrna', 'sirna', 'mrna']):
                    concepts.add(word)
        
        # Add nodes
        G.add_nodes_from(concepts)
        
        # Add edges based on co-occurrence
        for paper in papers:
            paper_concepts = [c for c in concepts if c in paper.content.lower()]
            for i, concept1 in enumerate(paper_concepts):
                for concept2 in paper_concepts[i+1:]:
                    G.add_edge(concept1, concept2)
        
        return G
    
    def _calculate_connection_potential(self, node1: str, node2: str, 
                                      graph: nx.Graph, papers: List[Document]) -> float:
        """Calculate potential for connection between two concepts"""
        
        # Check if they share common neighbors
        neighbors1 = set(graph.neighbors(node1)) if graph.has_node(node1) else set()
        neighbors2 = set(graph.neighbors(node2)) if graph.has_node(node2) else set()
        
        common_neighbors = neighbors1 & neighbors2
        
        if common_neighbors:
            return len(common_neighbors) / max(len(neighbors1), len(neighbors2))
        
        return 0.0
    
    def _generate_connection_rationale(self, concept1: str, concept2: str, 
                                     papers: List[Document]) -> str:
        """Generate rationale for why two concepts might be connected"""
        
        # Simple heuristic
        return f"{concept1} and {concept2} may share regulatory mechanisms or functional relationships"
    
    def _calculate_impact_score(self, hypothesis_data: Dict[str, Any]) -> float:
        """Calculate potential impact score of a hypothesis"""
        
        # Factors: number of applications, disease relevance, fundamental understanding
        score = 0.5  # Base score
        
        applications = hypothesis_data.get('potential_applications', [])
        if applications:
            score += min(len(applications) * 0.1, 0.3)
        
        # Check for disease relevance
        description = hypothesis_data.get('description', '').lower()
        if any(term in description for term in ['disease', 'therapeutic', 'clinical', 'treatment']):
            score += 0.2
        
        return min(score, 1.0)


class ExperimentPredictor:
    """Predict experimental outcomes and optimize designs"""
    
    def __init__(self):
        # self.llm_service = LLMService()  # Not implemented yet
        self.search_service = SearchService()
    
    def predict_experiment(self, experiment_description: str, 
                         technique: str = None) -> ExperimentPrediction:
        """Predict outcome of an experiment based on similar studies"""
        
        # Find similar experiments
        similar_experiments = self._find_similar_experiments(
            experiment_description, technique
        )
        
        # Analyze patterns in similar experiments
        outcome_patterns = self._analyze_outcome_patterns(similar_experiments)
        
        # Generate prediction
        prediction = self._generate_prediction(
            experiment_description, similar_experiments, outcome_patterns
        )
        
        # Add technical recommendations
        prediction.recommended_techniques = self._recommend_techniques(
            experiment_description, similar_experiments
        )
        
        prediction.potential_pitfalls = self._identify_pitfalls(
            experiment_description, similar_experiments
        )
        
        # Calculate success probability
        prediction.success_factors = self._calculate_success_factors(
            experiment_description, similar_experiments
        )
        
        # Estimate resources
        prediction.estimated_duration_days = self._estimate_duration(
            experiment_description, similar_experiments
        )
        
        prediction.required_equipment = self._identify_required_equipment(
            experiment_description, technique
        )
        
        # Link similar experiments
        prediction.similar_experiments.set(similar_experiments)
        
        return prediction
    
    def optimize_experimental_design(self, experiment: ExperimentPrediction) -> Dict[str, Any]:
        """Optimize experimental design for better outcomes"""
        
        optimizations = {
            'sample_size': self._optimize_sample_size(experiment),
            'controls': self._optimize_controls(experiment),
            'variables': self._optimize_variables(experiment),
            'timeline': self._optimize_timeline(experiment),
            'techniques': self._optimize_techniques(experiment)
        }
        
        return optimizations
    
    def _find_similar_experiments(self, description: str, technique: str = None) -> List[Document]:
        """Find experiments similar to the proposed one"""
        
        # Build search query
        query = description
        if technique:
            query += f" {technique}"
        
        try:
            results = self.search_service.search(
                query=query,
                doc_types=['paper', 'thesis'],
                limit=20
            )
            
            # Filter for experimental papers
            experimental_papers = []
            for result in results['results']:
                doc = result['document']
                if self._is_experimental_paper(doc):
                    experimental_papers.append(doc)
            
            return experimental_papers[:10]
            
        except Exception as e:
            logger.error(f"Error finding similar experiments: {e}")
            return []
    
    def _analyze_outcome_patterns(self, experiments: List[Document]) -> Dict[str, Any]:
        """Analyze patterns in experimental outcomes"""
        
        patterns = {
            'success_rate': 0.0,
            'common_outcomes': [],
            'failure_modes': [],
            'key_factors': []
        }
        
        if not experiments:
            return patterns
        
        # Analyze each experiment
        successful = 0
        outcomes = defaultdict(int)
        failures = defaultdict(int)
        
        for exp in experiments:
            # Simple heuristic - look for success indicators
            content_lower = exp.content.lower()
            
            if any(term in content_lower for term in ['successful', 'confirmed', 'validated', 'demonstrated']):
                successful += 1
            
            # Extract outcomes (simplified)
            if 'increased' in content_lower:
                outcomes['increased expression'] += 1
            if 'decreased' in content_lower:
                outcomes['decreased expression'] += 1
            if 'no change' in content_lower or 'no effect' in content_lower:
                outcomes['no significant change'] += 1
            
            # Extract failure modes
            if 'failed' in content_lower or 'unsuccessful' in content_lower:
                if 'contamination' in content_lower:
                    failures['contamination'] += 1
                if 'degradation' in content_lower:
                    failures['RNA degradation'] += 1
        
        patterns['success_rate'] = successful / len(experiments) if experiments else 0
        patterns['common_outcomes'] = sorted(outcomes.items(), key=lambda x: x[1], reverse=True)[:3]
        patterns['failure_modes'] = sorted(failures.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return patterns
    
    def _generate_prediction(self, description: str, similar_experiments: List[Document], 
                           patterns: Dict[str, Any]) -> ExperimentPrediction:
        """Generate prediction based on analysis"""
        
        prompt = f"""
        Predict the outcome of this RNA experiment based on similar studies:
        
        Experiment: {description}
        
        Analysis of {len(similar_experiments)} similar experiments:
        - Success rate: {patterns['success_rate']:.1%}
        - Common outcomes: {patterns['common_outcomes']}
        - Common failure modes: {patterns['failure_modes']}
        
        Provide:
        1. Most likely outcome (be specific)
        2. Confidence level (0-1)
        3. Key factors affecting success
        4. Recommended controls (list)
        5. Critical variables to monitor (list)
        
        Format as JSON.
        """
        
        try:
            response = self.llm_service.generate(prompt, max_tokens=500)
            pred_data = json.loads(response)
            
            prediction = ExperimentPrediction(
                experiment_title=description[:200],
                experiment_description=description,
                predicted_outcome=pred_data['outcome'],
                confidence_score=pred_data['confidence'],
                recommended_controls=pred_data['controls'],
                recommended_variables=pred_data['variables']
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error generating prediction: {e}")
            # Return basic prediction
            return ExperimentPrediction(
                experiment_title=description[:200],
                experiment_description=description,
                predicted_outcome="Uncertain - requires further analysis",
                confidence_score=0.3,
                recommended_controls=['Negative control', 'Positive control'],
                recommended_variables=['RNA concentration', 'Incubation time']
            )
    
    def _recommend_techniques(self, description: str, similar_experiments: List[Document]) -> List[str]:
        """Recommend optimal techniques"""
        
        techniques = set()
        
        # Extract techniques from similar successful experiments
        technique_keywords = [
            'qPCR', 'RT-PCR', 'Northern blot', 'RNA-seq', 'FISH',
            'Western blot', 'Flow cytometry', 'Microscopy', 'CRISPR',
            'RNAi', 'Transfection', 'Electroporation'
        ]
        
        for exp in similar_experiments:
            for technique in technique_keywords:
                if technique.lower() in exp.content.lower():
                    techniques.add(technique)
        
        return list(techniques)[:5]
    
    def _identify_pitfalls(self, description: str, similar_experiments: List[Document]) -> List[str]:
        """Identify potential pitfalls"""
        
        pitfalls = set()
        
        # Common RNA experiment pitfalls
        pitfall_patterns = {
            'degradation': 'RNA degradation - use RNase-free conditions',
            'contamination': 'Contamination - ensure sterile technique',
            'efficiency': 'Low transfection efficiency - optimize conditions',
            'specificity': 'Off-target effects - validate specificity',
            'variation': 'High biological variation - increase replicates'
        }
        
        for exp in similar_experiments:
            content_lower = exp.content.lower()
            for key, pitfall in pitfall_patterns.items():
                if key in content_lower:
                    pitfalls.add(pitfall)
        
        return list(pitfalls)
    
    def _calculate_success_factors(self, description: str, 
                                 similar_experiments: List[Document]) -> Dict[str, float]:
        """Calculate factors affecting success probability"""
        
        factors = {
            'technique_maturity': 0.7,  # Default
            'reagent_quality': 0.8,
            'operator_experience': 0.5,
            'protocol_clarity': 0.6
        }
        
        # Adjust based on similar experiments
        if similar_experiments:
            success_count = sum(1 for exp in similar_experiments 
                              if 'successful' in exp.content.lower())
            factors['historical_success'] = success_count / len(similar_experiments)
        
        return factors
    
    def _estimate_duration(self, description: str, similar_experiments: List[Document]) -> int:
        """Estimate experiment duration in days"""
        
        # Simple heuristic based on technique
        if 'transfection' in description.lower():
            return 3
        elif 'rna-seq' in description.lower():
            return 14
        elif 'qpcr' in description.lower():
            return 2
        else:
            return 7  # Default
    
    def _identify_required_equipment(self, description: str, technique: str = None) -> List[str]:
        """Identify required equipment"""
        
        equipment = []
        
        desc_lower = description.lower()
        if technique:
            desc_lower += f" {technique.lower()}"
        
        # Map techniques to equipment
        equipment_map = {
            'qpcr': ['Real-time PCR machine', 'Pipettes', 'PCR tubes'],
            'transfection': ['Cell culture hood', 'Incubator', 'Microscope'],
            'rna-seq': ['Sequencer', 'Bioanalyzer', 'Qubit'],
            'western': ['Gel apparatus', 'Transfer system', 'Imager']
        }
        
        for tech, equip in equipment_map.items():
            if tech in desc_lower:
                equipment.extend(equip)
        
        return list(set(equipment))
    
    def _is_experimental_paper(self, document: Document) -> bool:
        """Check if document contains experimental data"""
        
        experimental_keywords = [
            'methods', 'materials', 'results', 'figure', 'table',
            'performed', 'measured', 'analyzed', 'experiment'
        ]
        
        content_lower = document.content.lower()
        keyword_count = sum(1 for keyword in experimental_keywords 
                          if keyword in content_lower)
        
        return keyword_count >= 3
    
    def _optimize_sample_size(self, experiment: ExperimentPrediction) -> Dict[str, Any]:
        """Optimize sample size for statistical power"""
        
        return {
            'recommended_n': 6,  # Standard for RNA experiments
            'power_analysis': 'Based on 80% power to detect 2-fold change',
            'replicates': {
                'biological': 3,
                'technical': 2
            }
        }
    
    def _optimize_controls(self, experiment: ExperimentPrediction) -> List[Dict[str, str]]:
        """Optimize control selection"""
        
        controls = experiment.recommended_controls or []
        
        # Always include these essential controls
        essential_controls = [
            {'name': 'No treatment', 'purpose': 'Baseline expression'},
            {'name': 'Vehicle only', 'purpose': 'Solvent effects'},
            {'name': 'Scrambled RNA', 'purpose': 'Sequence-specific effects'}
        ]
        
        # Combine with existing recommendations
        control_names = [c.lower() for c in controls]
        
        for control in essential_controls:
            if control['name'].lower() not in control_names:
                controls.append(control)
        
        return controls[:5]  # Limit to 5 controls
    
    def _optimize_variables(self, experiment: ExperimentPrediction) -> Dict[str, Any]:
        """Optimize variable selection and ranges"""
        
        variables = {}
        
        # Standard RNA experiment variables
        if 'concentration' in experiment.experiment_description.lower():
            variables['RNA_concentration'] = {
                'range': '10nM - 1µM',
                'recommended': '100nM',
                'increments': 'Log scale'
            }
        
        if 'time' in experiment.experiment_description.lower():
            variables['timepoints'] = {
                'range': '0-48 hours',
                'recommended': [0, 6, 12, 24, 48],
                'critical': '24h (peak expression)'
            }
        
        return variables
    
    def _optimize_timeline(self, experiment: ExperimentPrediction) -> Dict[str, Any]:
        """Optimize experimental timeline"""
        
        duration = experiment.estimated_duration_days or 7
        
        timeline = {
            'total_days': duration,
            'phases': [
                {'day': 1, 'task': 'Sample preparation'},
                {'day': 2, 'task': 'Treatment/transfection'},
                {'day': 3-4, 'task': 'Incubation period'},
                {'day': 5, 'task': 'Sample collection'},
                {'day': 6-7, 'task': 'Analysis'}
            ],
            'critical_timepoints': ['Day 2 - treatment', 'Day 5 - collection']
        }
        
        return timeline
    
    def _optimize_techniques(self, experiment: ExperimentPrediction) -> List[Dict[str, str]]:
        """Optimize technique selection"""
        
        techniques = []
        
        # Recommend complementary techniques
        if 'expression' in experiment.experiment_description.lower():
            techniques.append({
                'primary': 'qPCR',
                'validation': 'Western blot',
                'reason': 'Confirm at protein level'
            })
        
        if 'localization' in experiment.experiment_description.lower():
            techniques.append({
                'primary': 'FISH',
                'validation': 'Subcellular fractionation',
                'reason': 'Quantitative validation'
            })
        
        return techniques


class CrossStudyAnalyzer:
    """Analyze connections and insights across multiple studies"""
    
    def __init__(self):
        # self.llm_service = LLMService()  # Not implemented yet
        self.search_service = SearchService()
    
    def find_cross_study_insights(self, domain: str = None, 
                                papers: List[Document] = None) -> List[CrossStudyInsight]:
        """Find insights across multiple studies"""
        
        if not papers and domain:
            papers = self._get_domain_papers(domain)
        
        insights = []
        
        # Find different types of insights
        insights.extend(self._find_hidden_connections(papers))
        insights.extend(self._find_contradictions(papers))
        insights.extend(self._find_emerging_patterns(papers))
        insights.extend(self._identify_collaboration_opportunities(papers))
        
        # Rank by importance
        insights.sort(key=lambda x: x.connection_strength * x.evidence_quality, reverse=True)
        
        return insights[:20]  # Top 20 insights
    
    def _find_hidden_connections(self, papers: List[Document]) -> List[CrossStudyInsight]:
        """Find hidden connections between studies"""
        
        insights = []
        
        # Build concept network
        concept_network = self._build_concept_network(papers)
        
        # Find indirect connections
        for i, paper1 in enumerate(papers):
            for paper2 in papers[i+1:]:
                connection = self._analyze_connection(paper1, paper2, concept_network)
                
                if connection and connection['strength'] > 0.6:
                    insight = CrossStudyInsight(
                        insight_type='connection',
                        title=f"Hidden link: {connection['concept1']} ↔ {connection['concept2']}",
                        description=connection['description'],
                        connection_strength=connection['strength'],
                        evidence_quality=0.8,
                        key_findings=connection['findings']
                    )
                    
                    insight.primary_studies.add(paper1)
                    insight.primary_studies.add(paper2)
                    
                    insights.append(insight)
        
        return insights
    
    def _find_contradictions(self, papers: List[Document]) -> List[CrossStudyInsight]:
        """Find contradictory results"""
        
        insights = []
        
        # Group papers by topic
        topic_groups = self._group_by_research_topic(papers)
        
        for topic, topic_papers in topic_groups.items():
            contradictions = self._analyze_contradictions_in_group(topic_papers)
            
            for contradiction in contradictions:
                insight = CrossStudyInsight(
                    insight_type='contradiction',
                    title=f"Contradictory findings in {topic}",
                    description=contradiction['description'],
                    connection_strength=contradiction['severity'],
                    evidence_quality=contradiction['evidence_quality'],
                    contradiction_details=contradiction['details'],
                    possible_explanations=contradiction['explanations']
                )
                
                for paper in contradiction['papers']:
                    insight.primary_studies.add(paper)
                
                insights.append(insight)
        
        return insights
    
    def _find_emerging_patterns(self, papers: List[Document]) -> List[CrossStudyInsight]:
        """Identify emerging patterns across studies"""
        
        insights = []
        
        # Time-based analysis
        papers_by_year = self._group_papers_by_year(papers)
        
        # Trend analysis
        trends = self._analyze_research_trends(papers_by_year)
        
        for trend in trends:
            if trend['significance'] > 0.7:
                insight = CrossStudyInsight(
                    insight_type='pattern',
                    title=f"Emerging pattern: {trend['name']}",
                    description=trend['description'],
                    connection_strength=trend['significance'],
                    evidence_quality=0.9,
                    key_findings=trend['evidence']
                )
                
                for paper in trend['papers']:
                    insight.primary_studies.add(paper)
                
                insights.append(insight)
        
        return insights
    
    def _identify_collaboration_opportunities(self, papers: List[Document]) -> List[CrossStudyInsight]:
        """Identify opportunities for collaboration"""
        
        insights = []
        
        # Analyze complementary expertise
        expertise_map = self._map_research_expertise(papers)
        
        # Find complementary pairs
        for group1, data1 in expertise_map.items():
            for group2, data2 in expertise_map.items():
                if group1 >= group2:  # Avoid duplicates
                    continue
                
                synergy = self._calculate_synergy(data1, data2)
                
                if synergy['score'] > 0.75:
                    insight = CrossStudyInsight(
                        insight_type='opportunity',
                        title=f"Collaboration opportunity: {group1} + {group2}",
                        description=synergy['rationale'],
                        connection_strength=synergy['score'],
                        evidence_quality=0.85,
                        suggested_collaborators=[
                            {'group': group1, 'expertise': data1['expertise']},
                            {'group': group2, 'expertise': data2['expertise']}
                        ],
                        collaboration_rationale=synergy['joint_potential']
                    )
                    
                    insights.append(insight)
        
        return insights
    
    def _build_concept_network(self, papers: List[Document]) -> nx.Graph:
        """Build network of concepts from papers"""
        
        G = nx.Graph()
        
        # Extract concepts from each paper
        for paper in papers:
            concepts = self._extract_key_concepts(paper)
            
            # Add nodes
            for concept in concepts:
                if not G.has_node(concept):
                    G.add_node(concept, papers=[paper])
                else:
                    G.nodes[concept]['papers'].append(paper)
            
            # Add edges between co-occurring concepts
            for i, c1 in enumerate(concepts):
                for c2 in concepts[i+1:]:
                    if G.has_edge(c1, c2):
                        G[c1][c2]['weight'] += 1
                    else:
                        G.add_edge(c1, c2, weight=1)
        
        return G
    
    def _extract_key_concepts(self, paper: Document) -> List[str]:
        """Extract key concepts from a paper"""
        
        # Simplified concept extraction
        concepts = []
        
        # RNA-specific terms
        rna_terms = ['miRNA', 'lncRNA', 'mRNA', 'siRNA', 'CRISPR', 'RNAi']
        
        content_lower = paper.content.lower()
        for term in rna_terms:
            if term.lower() in content_lower:
                concepts.append(term)
        
        # Extract from title
        title_words = paper.title.split()
        for word in title_words:
            if len(word) > 4 and word[0].isupper():  # Likely important term
                concepts.append(word)
        
        return concepts[:10]  # Limit concepts per paper
    
    def _analyze_connection(self, paper1: Document, paper2: Document, 
                          network: nx.Graph) -> Optional[Dict[str, Any]]:
        """Analyze potential connection between papers"""
        
        # Get concepts from each paper
        concepts1 = self._extract_key_concepts(paper1)
        concepts2 = self._extract_key_concepts(paper2)
        
        # Find bridging concepts
        bridges = []
        for c1 in concepts1:
            for c2 in concepts2:
                if c1 != c2 and network.has_node(c1) and network.has_node(c2):
                    try:
                        # Find shortest path
                        path = nx.shortest_path(network, c1, c2)
                        if 2 < len(path) <= 4:  # Indirect but not too distant
                            bridges.append({
                                'path': path,
                                'length': len(path),
                                'concepts': (c1, c2)
                            })
                    except nx.NetworkXNoPath:
                        pass
        
        if not bridges:
            return None
        
        # Select best bridge
        best_bridge = min(bridges, key=lambda x: x['length'])
        
        return {
            'concept1': best_bridge['concepts'][0],
            'concept2': best_bridge['concepts'][1],
            'strength': 1.0 / best_bridge['length'],
            'description': f"Connected through: {' → '.join(best_bridge['path'])}",
            'findings': [
                f"Paper 1 studies {best_bridge['concepts'][0]}",
                f"Paper 2 studies {best_bridge['concepts'][1]}",
                f"Connected via {best_bridge['path'][1:-1]}"
            ]
        }
    
    def _group_by_research_topic(self, papers: List[Document]) -> Dict[str, List[Document]]:
        """Group papers by research topic"""
        
        # Simple keyword-based grouping
        topics = {
            'gene_regulation': ['regulation', 'expression', 'transcription'],
            'rna_modification': ['modification', 'editing', 'methylation'],
            'disease': ['disease', 'cancer', 'disorder', 'therapy'],
            'methodology': ['method', 'technique', 'protocol', 'assay']
        }
        
        grouped = defaultdict(list)
        
        for paper in papers:
            content_lower = paper.content.lower()
            
            for topic, keywords in topics.items():
                if any(keyword in content_lower for keyword in keywords):
                    grouped[topic].append(paper)
        
        return dict(grouped)
    
    def _analyze_contradictions_in_group(self, papers: List[Document]) -> List[Dict[str, Any]]:
        """Analyze contradictions within a group of papers"""
        
        contradictions = []
        
        # Simple contradiction detection
        for i, paper1 in enumerate(papers):
            for paper2 in papers[i+1:]:
                # Check for opposite conclusions
                if self._papers_contradict(paper1, paper2):
                    contradiction = {
                        'papers': [paper1, paper2],
                        'description': f"{paper1.title} vs {paper2.title}",
                        'severity': 0.8,
                        'evidence_quality': 0.7,
                        'details': {
                            'paper1_claim': 'Positive effect observed',
                            'paper2_claim': 'Negative effect observed'
                        },
                        'explanations': [
                            'Different experimental conditions',
                            'Different cell types or model systems',
                            'Temporal differences in measurement'
                        ]
                    }
                    contradictions.append(contradiction)
        
        return contradictions
    
    def _papers_contradict(self, paper1: Document, paper2: Document) -> bool:
        """Check if two papers have contradictory findings"""
        
        # Simplified check
        opposite_pairs = [
            ('increase', 'decrease'), ('upregulate', 'downregulate'),
            ('promote', 'inhibit'), ('enhance', 'suppress')
        ]
        
        p1_lower = paper1.content.lower()
        p2_lower = paper2.content.lower()
        
        for word1, word2 in opposite_pairs:
            if (word1 in p1_lower and word2 in p2_lower) or \
               (word2 in p1_lower and word1 in p2_lower):
                return True
        
        return False
    
    def _group_papers_by_year(self, papers: List[Document]) -> Dict[int, List[Document]]:
        """Group papers by publication year"""
        
        grouped = defaultdict(list)
        
        for paper in papers:
            # Extract year from metadata or title
            year = getattr(paper, 'year', None)
            if not year and paper.title:
                # Try to extract year from title (e.g., "2023_Author_...")
                import re
                year_match = re.search(r'20\d{2}', paper.title)
                if year_match:
                    year = int(year_match.group())
            
            if year:
                grouped[year].append(paper)
        
        return dict(grouped)
    
    def _analyze_research_trends(self, papers_by_year: Dict[int, List[Document]]) -> List[Dict[str, Any]]:
        """Analyze trends over time"""
        
        trends = []
        
        # Track concept frequency over time
        concept_timeline = defaultdict(lambda: defaultdict(int))
        
        for year, papers in sorted(papers_by_year.items()):
            for paper in papers:
                concepts = self._extract_key_concepts(paper)
                for concept in concepts:
                    concept_timeline[concept][year] += 1
        
        # Identify rising concepts
        for concept, yearly_counts in concept_timeline.items():
            years = sorted(yearly_counts.keys())
            if len(years) >= 3:  # Need at least 3 years
                counts = [yearly_counts[year] for year in years]
                
                # Simple trend detection
                if counts[-1] > counts[0] * 2:  # Doubled over time
                    trend = {
                        'name': concept,
                        'description': f"Rising interest in {concept} research",
                        'significance': min(counts[-1] / counts[0] / 3, 1.0),
                        'evidence': [f"{year}: {count} papers" for year, count in yearly_counts.items()],
                        'papers': [p for papers in papers_by_year.values() for p in papers 
                                 if concept in self._extract_key_concepts(p)]
                    }
                    trends.append(trend)
        
        return trends
    
    def _map_research_expertise(self, papers: List[Document]) -> Dict[str, Dict[str, Any]]:
        """Map research expertise from papers"""
        
        expertise_map = {}
        
        # Group by author/institution (simplified - using paper source)
        for paper in papers:
            # Extract group identifier (could be author, institution, etc.)
            group_id = paper.source if hasattr(paper, 'source') else 'Unknown'
            
            if group_id not in expertise_map:
                expertise_map[group_id] = {
                    'papers': [],
                    'expertise': set(),
                    'techniques': set()
                }
            
            expertise_map[group_id]['papers'].append(paper)
            
            # Extract expertise areas
            concepts = self._extract_key_concepts(paper)
            expertise_map[group_id]['expertise'].update(concepts)
            
            # Extract techniques
            techniques = self._extract_techniques(paper)
            expertise_map[group_id]['techniques'].update(techniques)
        
        # Convert sets to lists
        for data in expertise_map.values():
            data['expertise'] = list(data['expertise'])
            data['techniques'] = list(data['techniques'])
        
        return expertise_map
    
    def _extract_techniques(self, paper: Document) -> List[str]:
        """Extract experimental techniques from paper"""
        
        techniques = []
        
        technique_keywords = [
            'PCR', 'sequencing', 'microscopy', 'flow cytometry',
            'western blot', 'CRISPR', 'transfection', 'cloning'
        ]
        
        content_lower = paper.content.lower()
        for technique in technique_keywords:
            if technique.lower() in content_lower:
                techniques.append(technique)
        
        return techniques
    
    def _calculate_synergy(self, group1_data: Dict[str, Any], 
                         group2_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate potential synergy between research groups"""
        
        # Find complementary expertise
        expertise1 = set(group1_data['expertise'])
        expertise2 = set(group2_data['expertise'])
        techniques1 = set(group1_data['techniques'])
        techniques2 = set(group2_data['techniques'])
        
        # Complementary if minimal overlap in expertise but good technique overlap
        expertise_overlap = len(expertise1 & expertise2) / min(len(expertise1), len(expertise2))
        technique_complement = len(techniques1 ^ techniques2) / len(techniques1 | techniques2)
        
        synergy_score = technique_complement * (1 - expertise_overlap)
        
        return {
            'score': synergy_score,
            'rationale': f"Complementary expertise with shared techniques",
            'joint_potential': f"Combining {list(expertise1 - expertise2)[:2]} with {list(expertise2 - expertise1)[:2]}"
        }
    
    def _get_domain_papers(self, domain: str) -> List[Document]:
        """Get papers in a specific domain"""
        
        try:
            results = self.search_service.search(
                query=f"{domain} RNA research recent",
                doc_types=['paper'],
                limit=50
            )
            return [r['document'] for r in results['results']]
        except Exception as e:
            logger.error(f"Error fetching domain papers: {e}")
            return []


class TimelineOptimizer:
    """Optimize research timelines and resource allocation"""
    
    def __init__(self):
        # self.llm_service = LLMService()  # Not implemented yet
    
    def optimize_research_timeline(self, 
                                 experiments: List[ExperimentPrediction],
                                 constraints: Dict[str, Any] = None) -> ResearchTimeline:
        """Create optimized timeline for multiple experiments"""
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(experiments)
        
        # Find critical path
        critical_path = self._find_critical_path(dependency_graph, experiments)
        
        # Identify parallel tracks
        parallel_tracks = self._identify_parallel_tracks(dependency_graph, experiments)
        
        # Optimize resource allocation
        resource_allocation = self._optimize_resources(experiments, parallel_tracks, constraints)
        
        # Calculate total duration
        total_duration = self._calculate_total_duration(critical_path, experiments)
        
        # Create timeline
        timeline = ResearchTimeline(
            project_name="RNA Research Project",
            project_description=f"Timeline for {len(experiments)} experiments",
            total_duration_days=total_duration,
            critical_path=[exp.id for exp in critical_path],
            parallel_tracks=parallel_tracks,
            experiment_dependencies=self._serialize_graph(dependency_graph),
            resource_allocation=resource_allocation,
            milestones=self._define_milestones(experiments, total_duration),
            decision_points=self._identify_decision_points(experiments)
        )
        
        # Add experiments
        timeline.experiments.set(experiments)
        
        return timeline
    
    def _build_dependency_graph(self, experiments: List[ExperimentPrediction]) -> nx.DiGraph:
        """Build directed graph of experiment dependencies"""
        
        G = nx.DiGraph()
        
        # Add nodes
        for exp in experiments:
            G.add_node(exp.id, experiment=exp)
        
        # Add edges based on logical dependencies
        for i, exp1 in enumerate(experiments):
            for exp2 in experiments[i+1:]:
                if self._depends_on(exp2, exp1):
                    G.add_edge(exp1.id, exp2.id)
        
        return G
    
    def _depends_on(self, exp1: ExperimentPrediction, exp2: ExperimentPrediction) -> bool:
        """Check if exp1 depends on exp2"""
        
        # Simple heuristics
        exp1_desc = exp1.experiment_description.lower()
        exp2_desc = exp2.experiment_description.lower()
        
        # Validation experiments depend on primary experiments
        if 'validation' in exp1_desc and 'primary' in exp2_desc:
            return True
        
        # Downstream depends on upstream
        if 'downstream' in exp1_desc and 'upstream' in exp2_desc:
            return True
        
        # Check for explicit mentions
        if any(word in exp1_desc for word in ['following', 'after', 'based on']):
            return True
        
        return False
    
    def _find_critical_path(self, graph: nx.DiGraph, 
                          experiments: List[ExperimentPrediction]) -> List[ExperimentPrediction]:
        """Find critical path through experiments"""
        
        if not graph.nodes():
            return experiments[:1]  # Return first experiment if no dependencies
        
        # Find longest path (critical path)
        try:
            # Get all paths from sources to sinks
            sources = [n for n in graph.nodes() if graph.in_degree(n) == 0]
            sinks = [n for n in graph.nodes() if graph.out_degree(n) == 0]
            
            longest_path = []
            max_length = 0
            
            for source in sources:
                for sink in sinks:
                    try:
                        paths = list(nx.all_simple_paths(graph, source, sink))
                        for path in paths:
                            if len(path) > max_length:
                                max_length = len(path)
                                longest_path = path
                    except nx.NetworkXNoPath:
                        pass
            
            # Convert IDs back to experiments
            exp_dict = {exp.id: exp for exp in experiments}
            return [exp_dict[node_id] for node_id in longest_path if node_id in exp_dict]
            
        except Exception as e:
            logger.error(f"Error finding critical path: {e}")
            return experiments[:3]  # Fallback
    
    def _identify_parallel_tracks(self, graph: nx.DiGraph, 
                                experiments: List[ExperimentPrediction]) -> List[List[int]]:
        """Identify experiments that can run in parallel"""
        
        parallel_tracks = []
        
        # Find independent subgraphs
        if graph.nodes():
            components = list(nx.weakly_connected_components(graph))
            
            for component in components:
                track = list(component)
                if len(track) > 1:
                    parallel_tracks.append(track)
        
        # Also find experiments with no dependencies
        independent = []
        for exp in experiments:
            if exp.id not in graph or (graph.in_degree(exp.id) == 0 and graph.out_degree(exp.id) == 0):
                independent.append(exp.id)
        
        if independent:
            parallel_tracks.append(independent)
        
        return parallel_tracks
    
    def _optimize_resources(self, experiments: List[ExperimentPrediction],
                          parallel_tracks: List[List[int]],
                          constraints: Dict[str, Any] = None) -> Dict[str, Any]:
        """Optimize resource allocation across experiments"""
        
        if not constraints:
            constraints = {
                'max_parallel': 3,
                'equipment_sharing': True,
                'personnel': 5
            }
        
        allocation = {
            'schedule': [],
            'equipment_usage': {},
            'personnel_assignment': {}
        }
        
        # Simple scheduling algorithm
        time_slots = {}
        current_slot = 0
        
        for track in parallel_tracks:
            # Assign experiments in track to time slots
            for exp_id in track:
                exp = next((e for e in experiments if e.id == exp_id), None)
                if exp:
                    # Find available slot
                    assigned = False
                    for slot in range(current_slot, current_slot + 10):
                        if slot not in time_slots:
                            time_slots[slot] = []
                        
                        if len(time_slots[slot]) < constraints['max_parallel']:
                            time_slots[slot].append(exp)
                            assigned = True
                            break
                    
                    if not assigned:
                        current_slot += 1
                        time_slots[current_slot] = [exp]
        
        # Convert to schedule
        for slot, exps in sorted(time_slots.items()):
            allocation['schedule'].append({
                'time_slot': slot,
                'experiments': [e.experiment_title for e in exps],
                'resources_needed': sum(len(e.required_equipment) for e in exps)
            })
        
        return allocation
    
    def _calculate_total_duration(self, critical_path: List[ExperimentPrediction], 
                                all_experiments: List[ExperimentPrediction]) -> int:
        """Calculate total project duration"""
        
        if not critical_path:
            # Sum all experiment durations if no critical path
            return sum(exp.estimated_duration_days or 7 for exp in all_experiments)
        
        # Sum durations along critical path
        return sum(exp.estimated_duration_days or 7 for exp in critical_path)
    
    def _serialize_graph(self, graph: nx.DiGraph) -> Dict[str, List[int]]:
        """Serialize dependency graph to JSON-compatible format"""
        
        dependencies = {}
        
        for node in graph.nodes():
            dependencies[str(node)] = [str(successor) for successor in graph.successors(node)]
        
        return dependencies
    
    def _define_milestones(self, experiments: List[ExperimentPrediction], 
                         total_duration: int) -> List[Dict[str, Any]]:
        """Define project milestones"""
        
        milestones = []
        
        # Start milestone
        milestones.append({
            'day': 0,
            'name': 'Project Start',
            'deliverables': ['Project plan', 'Resource allocation']
        })
        
        # Quarter milestones
        for quarter in [0.25, 0.5, 0.75]:
            day = int(total_duration * quarter)
            milestones.append({
                'day': day,
                'name': f'{int(quarter*100)}% Complete',
                'deliverables': [f'Progress report {int(quarter*4)}']
            })
        
        # Completion
        milestones.append({
            'day': total_duration,
            'name': 'Project Completion',
            'deliverables': ['Final report', 'Data package']
        })
        
        return milestones
    
    def _identify_decision_points(self, experiments: List[ExperimentPrediction]) -> List[Dict[str, Any]]:
        """Identify key decision points in the timeline"""
        
        decision_points = []
        
        # After validation experiments
        for exp in experiments:
            if 'validation' in exp.experiment_title.lower():
                decision_points.append({
                    'after_experiment': exp.experiment_title,
                    'decision': 'Continue with approach or pivot',
                    'criteria': 'Validation success rate > 80%'
                })
        
        # After pilot experiments
        for exp in experiments:
            if 'pilot' in exp.experiment_title.lower():
                decision_points.append({
                    'after_experiment': exp.experiment_title,
                    'decision': 'Scale up or optimize further',
                    'criteria': 'Pilot shows promising results'
                })
        
        return decision_points