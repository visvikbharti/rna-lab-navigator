"""
Cross-Paper Insight Generator
Discovers hidden connections between papers and generates research insights
"""
import re
import json
import logging
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from api.models import Document
from api.search.services import SearchService

logger = logging.getLogger(__name__)


class ResearchEntity(BaseModel):
    """Extracted research entity"""
    name: str
    entity_type: str  # method, protein, pathway, disease, etc.
    context: str
    confidence: float = Field(ge=0, le=1)


class MethodologyPattern(BaseModel):
    """Extracted methodology pattern"""
    technique: str
    application: str
    advantages: List[str]
    limitations: List[str]
    suitable_for: List[str]


class ResearchConnection(BaseModel):
    """Connection between papers"""
    paper1_id: str
    paper2_id: str
    connection_type: str  # complementary, contradictory, methodological, etc.
    strength: float = Field(ge=0, le=1)
    evidence: List[str]
    insight: str
    actionable_recommendation: str


class CrossPaperInsight(BaseModel):
    """Generated cross-paper insight"""
    insight_type: str
    title: str
    description: str
    papers_involved: List[str]
    evidence_snippets: List[str]
    confidence_score: float = Field(ge=0, le=1)
    potential_impact: str
    suggested_actions: List[str]
    novelty_score: float = Field(ge=0, le=1)


@dataclass
class InsightCandidate:
    """Internal representation of insight candidate"""
    papers: List[Document]
    connection_type: str
    evidence: List[str]
    score: float
    

class CrossPaperInsightGenerator:
    """Generates insights by analyzing connections across papers"""
    
    def __init__(self):
        self.search_service = SearchService()
        self.llm = ChatOpenAI(
            model_name=settings.LLM_MODEL,
            temperature=0.3,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.entity_cache = {}
        self.method_cache = {}
        
    def generate_insights(
        self,
        query: Optional[str] = None,
        paper_ids: Optional[List[str]] = None,
        insight_types: Optional[List[str]] = None,
        min_confidence: float = 0.6
    ) -> List[CrossPaperInsight]:
        """Generate cross-paper insights"""
        try:
            # Get papers to analyze
            papers = self._get_papers_for_analysis(query, paper_ids)
            if len(papers) < 2:
                return []
                
            # Extract entities and methods from papers
            entities_by_paper = self._extract_entities_batch(papers)
            methods_by_paper = self._extract_methods_batch(papers)
            
            # Build knowledge graph
            knowledge_graph = self._build_knowledge_graph(
                papers, entities_by_paper, methods_by_paper
            )
            
            # Generate different types of insights
            insights = []
            
            if not insight_types or "complementary" in insight_types:
                insights.extend(
                    self._find_complementary_approaches(
                        papers, methods_by_paper, knowledge_graph
                    )
                )
                
            if not insight_types or "contradictory" in insight_types:
                insights.extend(
                    self._find_contradictory_findings(
                        papers, entities_by_paper, knowledge_graph
                    )
                )
                
            if not insight_types or "methodological" in insight_types:
                insights.extend(
                    self._suggest_method_transfers(
                        papers, methods_by_paper, knowledge_graph
                    )
                )
                
            if not insight_types or "missing_citations" in insight_types:
                insights.extend(
                    self._find_missing_citations(
                        papers, entities_by_paper, knowledge_graph
                    )
                )
                
            if not insight_types or "converging_trends" in insight_types:
                insights.extend(
                    self._detect_converging_trends(
                        papers, entities_by_paper, methods_by_paper
                    )
                )
            
            # Filter by confidence and rank
            insights = [i for i in insights if i.confidence_score >= min_confidence]
            insights.sort(key=lambda x: x.novelty_score * x.confidence_score, reverse=True)
            
            # Cache insights
            if query:
                cache_key = f"cross_paper_insights:{query}"
                cache.set(cache_key, insights, timeout=3600)
                
            return insights[:20]  # Return top 20 insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return []
    
    def _get_papers_for_analysis(
        self,
        query: Optional[str],
        paper_ids: Optional[List[str]]
    ) -> List[Document]:
        """Get relevant papers for analysis"""
        if paper_ids:
            return list(Document.objects.filter(
                doc_id__in=paper_ids,
                doc_type="paper"
            ))
            
        if query:
            # Use search to find relevant papers
            search_results = self.search_service.enhanced_search(
                query=query,
                doc_types=["paper"],
                limit=30
            )
            doc_ids = [r["doc_id"] for r in search_results["results"]]
            return list(Document.objects.filter(doc_id__in=doc_ids))
            
        # Default: get recent papers
        return list(Document.objects.filter(
            doc_type="paper"
        ).order_by("-created_at")[:30])
    
    def _extract_entities_batch(
        self,
        papers: List[Document]
    ) -> Dict[str, List[ResearchEntity]]:
        """Extract research entities from papers"""
        entities_by_paper = {}
        
        entity_prompt = ChatPromptTemplate.from_template("""
        Extract key research entities from this paper excerpt:
        
        Title: {title}
        Content: {content}
        
        Identify:
        1. Key proteins, genes, pathways mentioned
        2. Diseases or conditions studied
        3. Cell types or organisms used
        4. Important molecular mechanisms
        
        Return as JSON list of entities with name, type, context, and confidence.
        """)
        
        for paper in papers:
            cache_key = f"entities:{paper.doc_id}"
            cached = cache.get(cache_key)
            
            if cached:
                entities_by_paper[paper.doc_id] = cached
                continue
                
            try:
                # Get paper content
                content = paper.content[:3000]  # First 3000 chars
                
                response = self.llm.invoke(
                    entity_prompt.format(
                        title=paper.title,
                        content=content
                    )
                )
                
                # Parse entities
                entities = self._parse_entity_response(response.content)
                entities_by_paper[paper.doc_id] = entities
                
                # Cache results
                cache.set(cache_key, entities, timeout=86400)
                
            except Exception as e:
                logger.error(f"Error extracting entities from {paper.doc_id}: {str(e)}")
                entities_by_paper[paper.doc_id] = []
                
        return entities_by_paper
    
    def _extract_methods_batch(
        self,
        papers: List[Document]
    ) -> Dict[str, List[MethodologyPattern]]:
        """Extract methodology patterns from papers"""
        methods_by_paper = {}
        
        method_prompt = ChatPromptTemplate.from_template("""
        Extract key methodological approaches from this paper:
        
        Title: {title}
        Content: {content}
        
        For each method identify:
        1. The technique name
        2. How it's applied
        3. Advantages mentioned
        4. Limitations noted
        5. What it's suitable for
        
        Return as JSON list of methodology patterns.
        """)
        
        for paper in papers:
            cache_key = f"methods:{paper.doc_id}"
            cached = cache.get(cache_key)
            
            if cached:
                methods_by_paper[paper.doc_id] = cached
                continue
                
            try:
                content = paper.content[:3000]
                
                response = self.llm.invoke(
                    method_prompt.format(
                        title=paper.title,
                        content=content
                    )
                )
                
                methods = self._parse_method_response(response.content)
                methods_by_paper[paper.doc_id] = methods
                
                cache.set(cache_key, methods, timeout=86400)
                
            except Exception as e:
                logger.error(f"Error extracting methods from {paper.doc_id}: {str(e)}")
                methods_by_paper[paper.doc_id] = []
                
        return methods_by_paper
    
    def _build_knowledge_graph(
        self,
        papers: List[Document],
        entities_by_paper: Dict[str, List[ResearchEntity]],
        methods_by_paper: Dict[str, List[MethodologyPattern]]
    ) -> nx.Graph:
        """Build knowledge graph from extracted information"""
        G = nx.Graph()
        
        # Add papers as nodes
        for paper in papers:
            G.add_node(
                paper.doc_id,
                node_type="paper",
                title=paper.title,
                year=paper.metadata.get("year", "unknown")
            )
        
        # Add entities and connections
        entity_to_papers = defaultdict(list)
        for paper_id, entities in entities_by_paper.items():
            for entity in entities:
                entity_key = f"{entity.entity_type}:{entity.name.lower()}"
                entity_to_papers[entity_key].append(paper_id)
                
                # Add entity node if not exists
                if entity_key not in G:
                    G.add_node(
                        entity_key,
                        node_type="entity",
                        entity_type=entity.entity_type,
                        name=entity.name
                    )
                
                # Add edge between paper and entity
                G.add_edge(
                    paper_id,
                    entity_key,
                    edge_type="mentions",
                    confidence=entity.confidence
                )
        
        # Add method connections
        method_to_papers = defaultdict(list)
        for paper_id, methods in methods_by_paper.items():
            for method in methods:
                method_key = f"method:{method.technique.lower()}"
                method_to_papers[method_key].append(paper_id)
                
                if method_key not in G:
                    G.add_node(
                        method_key,
                        node_type="method",
                        technique=method.technique
                    )
                
                G.add_edge(
                    paper_id,
                    method_key,
                    edge_type="uses",
                    application=method.application
                )
        
        # Add paper-to-paper edges based on shared entities/methods
        for entity_key, paper_ids in entity_to_papers.items():
            if len(paper_ids) > 1:
                for i, p1 in enumerate(paper_ids):
                    for p2 in paper_ids[i+1:]:
                        if G.has_edge(p1, p2):
                            G[p1][p2]["shared_entities"] = G[p1][p2].get("shared_entities", 0) + 1
                        else:
                            G.add_edge(p1, p2, edge_type="related", shared_entities=1)
        
        return G
    
    def _find_complementary_approaches(
        self,
        papers: List[Document],
        methods_by_paper: Dict[str, List[MethodologyPattern]],
        knowledge_graph: nx.Graph
    ) -> List[CrossPaperInsight]:
        """Find papers with complementary methodological approaches"""
        insights = []
        
        # Group papers by problem domain
        problem_clusters = self._cluster_by_problem_domain(papers)
        
        for cluster in problem_clusters:
            if len(cluster) < 2:
                continue
                
            # Compare methods within cluster
            for i, paper1 in enumerate(cluster):
                methods1 = methods_by_paper.get(paper1.doc_id, [])
                
                for paper2 in cluster[i+1:]:
                    methods2 = methods_by_paper.get(paper2.doc_id, [])
                    
                    # Check for complementary methods
                    complementary = self._identify_complementary_methods(
                        methods1, methods2, paper1, paper2
                    )
                    
                    if complementary:
                        insight = CrossPaperInsight(
                            insight_type="complementary_methods",
                            title=f"Complementary Approaches: {paper1.title[:50]}... & {paper2.title[:50]}...",
                            description=complementary["description"],
                            papers_involved=[paper1.doc_id, paper2.doc_id],
                            evidence_snippets=complementary["evidence"],
                            confidence_score=complementary["confidence"],
                            potential_impact=complementary["impact"],
                            suggested_actions=complementary["actions"],
                            novelty_score=self._calculate_novelty_score(
                                paper1, paper2, knowledge_graph
                            )
                        )
                        insights.append(insight)
        
        return insights
    
    def _find_contradictory_findings(
        self,
        papers: List[Document],
        entities_by_paper: Dict[str, List[ResearchEntity]],
        knowledge_graph: nx.Graph
    ) -> List[CrossPaperInsight]:
        """Find papers with contradictory findings about same entities"""
        insights = []
        
        # Group papers by shared entities
        entity_to_papers = defaultdict(list)
        for paper_id, entities in entities_by_paper.items():
            paper = next(p for p in papers if p.doc_id == paper_id)
            for entity in entities:
                if entity.confidence > 0.7:
                    key = f"{entity.entity_type}:{entity.name.lower()}"
                    entity_to_papers[key].append((paper, entity.context))
        
        # Look for contradictions
        for entity_key, paper_contexts in entity_to_papers.items():
            if len(paper_contexts) < 2:
                continue
                
            # Analyze contexts for contradictions
            contradictions = self._analyze_contradictions(
                entity_key, paper_contexts
            )
            
            for contradiction in contradictions:
                insight = CrossPaperInsight(
                    insight_type="contradictory_findings",
                    title=f"Contradictory Findings on {entity_key.split(':')[1]}",
                    description=contradiction["description"],
                    papers_involved=contradiction["paper_ids"],
                    evidence_snippets=contradiction["evidence"],
                    confidence_score=contradiction["confidence"],
                    potential_impact=contradiction["impact"],
                    suggested_actions=[
                        "Investigate experimental conditions differences",
                        "Consider meta-analysis of conflicting results",
                        "Design experiments to resolve contradiction"
                    ],
                    novelty_score=0.8  # Contradictions are inherently interesting
                )
                insights.append(insight)
        
        return insights
    
    def _suggest_method_transfers(
        self,
        papers: List[Document],
        methods_by_paper: Dict[str, List[MethodologyPattern]],
        knowledge_graph: nx.Graph
    ) -> List[CrossPaperInsight]:
        """Suggest method transfers between different research areas"""
        insights = []
        
        # Build method-problem matrix
        method_applications = defaultdict(list)
        for paper_id, methods in methods_by_paper.items():
            paper = next(p for p in papers if p.doc_id == paper_id)
            problem_domain = self._extract_problem_domain(paper)
            
            for method in methods:
                method_applications[method.technique].append({
                    "paper": paper,
                    "domain": problem_domain,
                    "application": method.application,
                    "advantages": method.advantages
                })
        
        # Find transfer opportunities
        for method, applications in method_applications.items():
            if len(applications) < 2:
                continue
                
            # Look for successful applications in one domain
            # that could benefit another
            for i, app1 in enumerate(applications):
                for app2 in applications[i+1:]:
                    if app1["domain"] != app2["domain"]:
                        transfer = self._evaluate_method_transfer(
                            method, app1, app2
                        )
                        
                        if transfer and transfer["score"] > 0.7:
                            insight = CrossPaperInsight(
                                insight_type="method_transfer",
                                title=f"Method Transfer: {method} from {app1['domain']} to {app2['domain']}",
                                description=transfer["description"],
                                papers_involved=[app1["paper"].doc_id, app2["paper"].doc_id],
                                evidence_snippets=transfer["evidence"],
                                confidence_score=transfer["score"],
                                potential_impact=transfer["impact"],
                                suggested_actions=transfer["actions"],
                                novelty_score=transfer["novelty"]
                            )
                            insights.append(insight)
        
        return insights
    
    def _find_missing_citations(
        self,
        papers: List[Document],
        entities_by_paper: Dict[str, List[ResearchEntity]],
        knowledge_graph: nx.Graph
    ) -> List[CrossPaperInsight]:
        """Find papers that should cite each other but don't"""
        insights = []
        
        # Build citation network
        citation_graph = self._build_citation_network(papers)
        
        # Find strongly related papers without citations
        for paper1 in papers:
            for paper2 in papers:
                if paper1.doc_id >= paper2.doc_id:  # Avoid duplicates
                    continue
                    
                # Check if they cite each other
                if self._papers_cite_each_other(paper1, paper2, citation_graph):
                    continue
                
                # Calculate relatedness
                relatedness = self._calculate_paper_relatedness(
                    paper1, paper2, entities_by_paper, knowledge_graph
                )
                
                if relatedness["score"] > 0.8:
                    insight = CrossPaperInsight(
                        insight_type="missing_citation",
                        title=f"Potential Missing Citation Between Related Papers",
                        description=f"These papers share {relatedness['shared_entities']} entities and {relatedness['shared_methods']} methods but don't cite each other",
                        papers_involved=[paper1.doc_id, paper2.doc_id],
                        evidence_snippets=relatedness["evidence"],
                        confidence_score=relatedness["score"],
                        potential_impact="Connecting these works could reveal new insights",
                        suggested_actions=[
                            "Review both papers for complementary findings",
                            "Consider collaboration between research groups",
                            "Investigate why citation is missing"
                        ],
                        novelty_score=0.7
                    )
                    insights.append(insight)
        
        return insights
    
    def _detect_converging_trends(
        self,
        papers: List[Document],
        entities_by_paper: Dict[str, List[ResearchEntity]],
        methods_by_paper: Dict[str, List[MethodologyPattern]]
    ) -> List[CrossPaperInsight]:
        """Detect converging research trends across papers"""
        insights = []
        
        # Time-based analysis of entity/method popularity
        temporal_trends = self._analyze_temporal_trends(
            papers, entities_by_paper, methods_by_paper
        )
        
        # Find converging trends
        for trend in temporal_trends:
            if trend["convergence_score"] > 0.7:
                insight = CrossPaperInsight(
                    insight_type="converging_trend",
                    title=f"Converging Trend: {trend['name']}",
                    description=trend["description"],
                    papers_involved=trend["paper_ids"],
                    evidence_snippets=trend["evidence"],
                    confidence_score=trend["confidence"],
                    potential_impact=trend["impact"],
                    suggested_actions=[
                        "Monitor this emerging trend",
                        "Consider early adoption of converging approaches",
                        "Identify collaboration opportunities"
                    ],
                    novelty_score=trend["novelty"]
                )
                insights.append(insight)
        
        return insights
    
    def _parse_entity_response(self, response: str) -> List[ResearchEntity]:
        """Parse LLM response for entities"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                entities_data = json.loads(json_match.group())
                return [
                    ResearchEntity(
                        name=e.get("name", ""),
                        entity_type=e.get("type", "unknown"),
                        context=e.get("context", ""),
                        confidence=e.get("confidence", 0.5)
                    )
                    for e in entities_data
                ]
        except Exception as e:
            logger.error(f"Error parsing entity response: {str(e)}")
        return []
    
    def _parse_method_response(self, response: str) -> List[MethodologyPattern]:
        """Parse LLM response for methods"""
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                methods_data = json.loads(json_match.group())
                return [
                    MethodologyPattern(
                        technique=m.get("technique", ""),
                        application=m.get("application", ""),
                        advantages=m.get("advantages", []),
                        limitations=m.get("limitations", []),
                        suitable_for=m.get("suitable_for", [])
                    )
                    for m in methods_data
                ]
        except Exception as e:
            logger.error(f"Error parsing method response: {str(e)}")
        return []
    
    def _cluster_by_problem_domain(self, papers: List[Document]) -> List[List[Document]]:
        """Cluster papers by problem domain using TF-IDF"""
        if len(papers) < 2:
            return [papers]
            
        # Extract text for clustering
        texts = [f"{p.title} {p.content[:1000]}" for p in papers]
        
        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Simple clustering based on similarity threshold
        clusters = []
        clustered = set()
        
        for i, paper in enumerate(papers):
            if i in clustered:
                continue
                
            cluster = [paper]
            clustered.add(i)
            
            # Find similar papers
            for j, other_paper in enumerate(papers):
                if j != i and j not in clustered and similarity_matrix[i][j] > 0.3:
                    cluster.append(other_paper)
                    clustered.add(j)
            
            clusters.append(cluster)
        
        return clusters
    
    def _identify_complementary_methods(
        self,
        methods1: List[MethodologyPattern],
        methods2: List[MethodologyPattern],
        paper1: Document,
        paper2: Document
    ) -> Optional[Dict]:
        """Identify if methods are complementary"""
        if not methods1 or not methods2:
            return None
            
        complementary_pairs = []
        
        for m1 in methods1:
            for m2 in methods2:
                # Check if methods address different aspects of same problem
                if m1.technique != m2.technique:
                    # Compare limitations and advantages
                    m1_limitations = set(m1.limitations)
                    m2_advantages = set(m2.advantages)
                    
                    # If m2 addresses m1's limitations
                    if m1_limitations & m2_advantages:
                        complementary_pairs.append({
                            "method1": m1.technique,
                            "method2": m2.technique,
                            "synergy": f"{m2.technique} addresses limitations of {m1.technique}"
                        })
        
        if complementary_pairs:
            return {
                "description": f"These papers use complementary methods that could be combined for better results",
                "evidence": [f"{p['method1']} + {p['method2']}: {p['synergy']}" for p in complementary_pairs],
                "confidence": min(0.9, 0.6 + 0.1 * len(complementary_pairs)),
                "impact": "Combining these approaches could overcome individual limitations",
                "actions": [
                    f"Consider combining {p['method1']} with {p['method2']}"
                    for p in complementary_pairs[:2]
                ]
            }
        
        return None
    
    def _calculate_novelty_score(
        self,
        paper1: Document,
        paper2: Document,
        knowledge_graph: nx.Graph
    ) -> float:
        """Calculate novelty score for a connection"""
        # Base novelty on graph distance and temporal distance
        try:
            # Check if papers are connected in graph
            if nx.has_path(knowledge_graph, paper1.doc_id, paper2.doc_id):
                path_length = nx.shortest_path_length(
                    knowledge_graph, paper1.doc_id, paper2.doc_id
                )
                distance_score = min(1.0, path_length / 5.0)
            else:
                distance_score = 1.0  # Very novel if not connected
            
            # Temporal distance
            year1 = int(paper1.metadata.get("year", 2020))
            year2 = int(paper2.metadata.get("year", 2020))
            temporal_score = min(1.0, abs(year1 - year2) / 10.0)
            
            # Different fields bonus
            field_score = 0.5 if paper1.metadata.get("field") != paper2.metadata.get("field") else 0
            
            return min(1.0, distance_score * 0.5 + temporal_score * 0.3 + field_score * 0.2)
            
        except Exception:
            return 0.5  # Default novelty
    
    def _analyze_contradictions(
        self,
        entity_key: str,
        paper_contexts: List[Tuple[Document, str]]
    ) -> List[Dict]:
        """Analyze contexts for contradictory findings"""
        contradictions = []
        
        contradiction_prompt = ChatPromptTemplate.from_template("""
        Analyze these research findings about {entity} for contradictions:
        
        Paper 1: {title1}
        Context 1: {context1}
        
        Paper 2: {title2}
        Context 2: {context2}
        
        Are these findings contradictory? If yes, explain the contradiction
        and its significance. Return JSON with:
        - is_contradictory: boolean
        - description: explanation
        - significance: why it matters
        """)
        
        for i, (paper1, context1) in enumerate(paper_contexts):
            for paper2, context2 in paper_contexts[i+1:]:
                try:
                    response = self.llm.invoke(
                        contradiction_prompt.format(
                            entity=entity_key.split(':')[1],
                            title1=paper1.title,
                            context1=context1,
                            title2=paper2.title,
                            context2=context2
                        )
                    )
                    
                    result = self._parse_json_response(response.content)
                    if result.get("is_contradictory"):
                        contradictions.append({
                            "paper_ids": [paper1.doc_id, paper2.doc_id],
                            "description": result.get("description", ""),
                            "evidence": [context1[:200], context2[:200]],
                            "confidence": 0.8,
                            "impact": result.get("significance", "")
                        })
                        
                except Exception as e:
                    logger.error(f"Error analyzing contradiction: {str(e)}")
        
        return contradictions
    
    def _extract_problem_domain(self, paper: Document) -> str:
        """Extract the problem domain from a paper"""
        # Simple keyword-based extraction
        title_lower = paper.title.lower()
        content_preview = paper.content[:500].lower()
        
        domains = {
            "cancer": ["cancer", "tumor", "oncolog", "carcinoma"],
            "neurodegenerative": ["alzheimer", "parkinson", "neurodegenerat", "dementia"],
            "infectious": ["virus", "bacteria", "infection", "pathogen"],
            "metabolic": ["diabetes", "metabol", "insulin", "glucose"],
            "cardiovascular": ["heart", "cardiac", "vascular", "hypertension"],
            "immunology": ["immune", "antibody", "t cell", "b cell"],
            "development": ["stem cell", "differentiation", "embryo", "development"],
            "genetics": ["mutation", "gene", "genetic", "hereditary"]
        }
        
        for domain, keywords in domains.items():
            if any(kw in title_lower or kw in content_preview for kw in keywords):
                return domain
        
        return "general"
    
    def _evaluate_method_transfer(
        self,
        method: str,
        app1: Dict,
        app2: Dict
    ) -> Optional[Dict]:
        """Evaluate potential for method transfer between domains"""
        # Check if domains are different but method shows promise
        if app1["domain"] == app2["domain"]:
            return None
            
        transfer_prompt = ChatPromptTemplate.from_template("""
        Evaluate if {method} used in {domain1} for {application1}
        could be transferred to {domain2} for {application2}.
        
        Advantages in domain1: {advantages1}
        
        Consider:
        1. Technical feasibility
        2. Potential benefits
        3. Possible challenges
        
        Return JSON with score (0-1), description, impact, and suggested actions.
        """)
        
        try:
            response = self.llm.invoke(
                transfer_prompt.format(
                    method=method,
                    domain1=app1["domain"],
                    application1=app1["application"],
                    domain2=app2["domain"],
                    application2=app2["application"],
                    advantages1=", ".join(app1["advantages"])
                )
            )
            
            result = self._parse_json_response(response.content)
            if result.get("score", 0) > 0.7:
                return {
                    "score": result["score"],
                    "description": result.get("description", ""),
                    "impact": result.get("impact", ""),
                    "actions": result.get("actions", []),
                    "novelty": 0.8,
                    "evidence": [
                        f"Success in {app1['domain']}: {app1['application']}",
                        f"Potential in {app2['domain']}: {app2['application']}"
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error evaluating method transfer: {str(e)}")
            
        return None
    
    def _build_citation_network(self, papers: List[Document]) -> nx.DiGraph:
        """Build citation network from papers"""
        G = nx.DiGraph()
        
        for paper in papers:
            G.add_node(paper.doc_id, title=paper.title)
            
            # Extract citations from metadata or content
            citations = paper.metadata.get("citations", [])
            if not citations:
                # Try to extract from content
                citations = self._extract_citations_from_content(paper.content)
            
            for cited_id in citations:
                if any(p.doc_id == cited_id for p in papers):
                    G.add_edge(paper.doc_id, cited_id)
        
        return G
    
    def _papers_cite_each_other(
        self,
        paper1: Document,
        paper2: Document,
        citation_graph: nx.DiGraph
    ) -> bool:
        """Check if papers cite each other"""
        return (
            citation_graph.has_edge(paper1.doc_id, paper2.doc_id) or
            citation_graph.has_edge(paper2.doc_id, paper1.doc_id)
        )
    
    def _calculate_paper_relatedness(
        self,
        paper1: Document,
        paper2: Document,
        entities_by_paper: Dict[str, List[ResearchEntity]],
        knowledge_graph: nx.Graph
    ) -> Dict:
        """Calculate relatedness between papers"""
        entities1 = set(e.name.lower() for e in entities_by_paper.get(paper1.doc_id, []))
        entities2 = set(e.name.lower() for e in entities_by_paper.get(paper2.doc_id, []))
        
        shared_entities = len(entities1 & entities2)
        
        # Get shared methods from knowledge graph
        shared_methods = 0
        if knowledge_graph.has_node(paper1.doc_id) and knowledge_graph.has_node(paper2.doc_id):
            neighbors1 = set(knowledge_graph.neighbors(paper1.doc_id))
            neighbors2 = set(knowledge_graph.neighbors(paper2.doc_id))
            shared_neighbors = neighbors1 & neighbors2
            shared_methods = len([n for n in shared_neighbors if n.startswith("method:")])
        
        # Calculate score
        total_entities = len(entities1 | entities2)
        entity_overlap = shared_entities / total_entities if total_entities > 0 else 0
        
        score = min(1.0, entity_overlap + 0.1 * shared_methods)
        
        return {
            "score": score,
            "shared_entities": shared_entities,
            "shared_methods": shared_methods,
            "evidence": [
                f"Shared entities: {', '.join(list(entities1 & entities2)[:5])}",
                f"Entity overlap: {entity_overlap:.2%}"
            ]
        }
    
    def _analyze_temporal_trends(
        self,
        papers: List[Document],
        entities_by_paper: Dict[str, List[ResearchEntity]],
        methods_by_paper: Dict[str, List[MethodologyPattern]]
    ) -> List[Dict]:
        """Analyze temporal trends in research"""
        trends = []
        
        # Group papers by year
        papers_by_year = defaultdict(list)
        for paper in papers:
            year = int(paper.metadata.get("year", datetime.now().year))
            papers_by_year[year].append(paper)
        
        # Track entity/method frequency over time
        entity_timeline = defaultdict(lambda: defaultdict(int))
        method_timeline = defaultdict(lambda: defaultdict(int))
        
        for year, year_papers in papers_by_year.items():
            for paper in year_papers:
                # Count entities
                for entity in entities_by_paper.get(paper.doc_id, []):
                    entity_timeline[entity.name.lower()][year] += 1
                
                # Count methods
                for method in methods_by_paper.get(paper.doc_id, []):
                    method_timeline[method.technique.lower()][year] += 1
        
        # Identify converging trends
        for item_name, timeline in {**entity_timeline, **method_timeline}.items():
            if len(timeline) >= 3:  # Need at least 3 time points
                years = sorted(timeline.keys())
                frequencies = [timeline[y] for y in years]
                
                # Simple trend detection
                if frequencies[-1] > frequencies[0] and frequencies[-1] >= 3:
                    trend_score = (frequencies[-1] - frequencies[0]) / len(years)
                    
                    if trend_score > 0.5:
                        involved_papers = []
                        for year in years[-2:]:  # Recent papers
                            involved_papers.extend([
                                p.doc_id for p in papers_by_year[year]
                                if item_name in p.content.lower()
                            ])
                        
                        trends.append({
                            "name": item_name,
                            "convergence_score": min(1.0, trend_score),
                            "description": f"Growing research interest in {item_name} - {frequencies[0]} to {frequencies[-1]} papers",
                            "paper_ids": involved_papers[:5],
                            "evidence": [f"Year {y}: {f} papers" for y, f in zip(years[-3:], frequencies[-3:])],
                            "confidence": 0.8,
                            "impact": "This emerging trend could indicate a breakthrough or new research direction",
                            "novelty": 0.7
                        })
        
        return trends
    
    def _extract_citations_from_content(self, content: str) -> List[str]:
        """Extract citation IDs from paper content"""
        # This is a placeholder - real implementation would parse references
        citations = []
        
        # Look for DOI patterns
        doi_pattern = r'10\.\d{4,}/[-._;()/:\w]+'
        dois = re.findall(doi_pattern, content)
        citations.extend(dois)
        
        return citations
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from LLM response"""
        try:
            # Find JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Error parsing JSON response: {str(e)}")
        return {}


class ResearchConnectionGraph:
    """Build and analyze research connection graphs"""
    
    def __init__(self):
        self.insight_generator = CrossPaperInsightGenerator()
        
    def build_connection_graph(
        self,
        query: Optional[str] = None,
        paper_ids: Optional[List[str]] = None,
        connection_types: Optional[List[str]] = None
    ) -> Dict:
        """Build a graph of research connections"""
        try:
            # Get papers
            if paper_ids:
                papers = Document.objects.filter(doc_id__in=paper_ids)
            elif query:
                search_service = SearchService()
                results = search_service.enhanced_search(query, limit=50)
                paper_ids = [r["doc_id"] for r in results["results"]]
                papers = Document.objects.filter(doc_id__in=paper_ids)
            else:
                papers = Document.objects.filter(doc_type="paper")[:50]
            
            # Build graph
            G = nx.Graph()
            
            # Add paper nodes
            for paper in papers:
                G.add_node(
                    paper.doc_id,
                    title=paper.title,
                    year=paper.metadata.get("year", "unknown"),
                    authors=paper.metadata.get("authors", [])
                )
            
            # Generate insights to find connections
            insights = self.insight_generator.generate_insights(
                paper_ids=[p.doc_id for p in papers]
            )
            
            # Add edges based on insights
            for insight in insights:
                if len(insight.papers_involved) >= 2:
                    for i, p1 in enumerate(insight.papers_involved):
                        for p2 in insight.papers_involved[i+1:]:
                            if G.has_edge(p1, p2):
                                # Update edge attributes
                                G[p1][p2]["connections"].append({
                                    "type": insight.insight_type,
                                    "strength": insight.confidence_score,
                                    "description": insight.title
                                })
                            else:
                                G.add_edge(p1, p2, connections=[{
                                    "type": insight.insight_type,
                                    "strength": insight.confidence_score,
                                    "description": insight.title
                                }])
            
            # Convert to serializable format
            nodes = []
            for node_id, attrs in G.nodes(data=True):
                nodes.append({
                    "id": node_id,
                    "title": attrs.get("title", ""),
                    "year": attrs.get("year", ""),
                    "authors": attrs.get("authors", [])
                })
            
            edges = []
            for u, v, attrs in G.edges(data=True):
                connections = attrs.get("connections", [])
                if connections:
                    strongest_connection = max(connections, key=lambda x: x["strength"])
                    edges.append({
                        "source": u,
                        "target": v,
                        "connection_type": strongest_connection["type"],
                        "strength": strongest_connection["strength"],
                        "description": strongest_connection["description"],
                        "all_connections": connections
                    })
            
            # Calculate graph statistics
            stats = {
                "total_papers": len(nodes),
                "total_connections": len(edges),
                "avg_connections_per_paper": len(edges) * 2 / len(nodes) if nodes else 0,
                "connection_types": Counter(e["connection_type"] for e in edges),
                "strongest_connections": sorted(
                    edges, key=lambda x: x["strength"], reverse=True
                )[:10]
            }
            
            return {
                "nodes": nodes,
                "edges": edges,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error building connection graph: {str(e)}")
            return {"nodes": [], "edges": [], "stats": {}}