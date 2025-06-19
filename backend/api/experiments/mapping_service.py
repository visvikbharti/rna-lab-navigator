"""
Experiment Mapping and Analysis Service
Creates knowledge graphs and analyzes experimental factors
"""

import json
import logging
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import networkx as nx

from django.conf import settings
from django.db import models
from openai import OpenAI

from api.models import Document
from api.rag.enhanced_rag import get_enhanced_rag_pipeline

logger = logging.getLogger(__name__)


@dataclass
class ExperimentData:
    """Data structure for experiment information"""
    experiment_id: str
    experiment_type: str  # e.g., "IVC assay", "RNA-seq", "CRISPR screen"
    target_locus: str
    variables: Dict[str, any]  # e.g., {"cas_variant": "FnCas9", "guide_rna": "sgRNA-1"}
    conditions: Dict[str, any]  # e.g., {"temperature": 37, "time": "48h"}
    protocol_id: Optional[str] = None
    outcomes: Dict[str, any] = field(default_factory=dict)
    success_metrics: Dict[str, float] = field(default_factory=dict)
    researcher: Optional[str] = None
    date_performed: Optional[datetime] = None
    notes: Optional[str] = None


@dataclass
class ExperimentalFactor:
    """Represents a factor that might influence outcomes"""
    name: str
    category: str  # "genetic", "environmental", "technical", "reagent"
    values: List[any]
    is_controlled: bool
    influence_score: float = 0.0


@dataclass
class ExperimentRelationship:
    """Relationship between experiments"""
    source_id: str
    target_id: str
    relationship_type: str  # "variant_of", "control_for", "follows_from", "contradicts"
    strength: float
    metadata: Dict[str, any] = field(default_factory=dict)


class ExperimentMappingService:
    """Service for mapping and analyzing experiment relationships"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.enhanced_rag = get_enhanced_rag_pipeline()
        self.knowledge_graph = nx.DiGraph()
        
    async def map_experiment_series(
        self,
        experiments: List[ExperimentData],
        analysis_focus: Optional[str] = None
    ) -> Dict:
        """
        Map a series of experiments and analyze relationships
        
        Args:
            experiments: List of experiment data
            analysis_focus: Optional focus area (e.g., "variant effects", "protocol optimization")
            
        Returns:
            Comprehensive analysis with knowledge graph and insights
        """
        try:
            # Step 1: Build knowledge graph from experiments
            graph_data = self._build_experiment_graph(experiments)
            
            # Step 2: Identify experimental factors
            factors = self._identify_factors(experiments)
            
            # Step 3: Analyze factor influences
            factor_analysis = await self._analyze_factor_influences(
                experiments, 
                factors,
                analysis_focus
            )
            
            # Step 4: Detect patterns and relationships
            patterns = self._detect_experimental_patterns(experiments, factors)
            
            # Step 5: Identify confounding variables
            confoundings = self._identify_confoundings(experiments, factors)
            
            # Step 6: Generate comparative analysis
            comparative_analysis = await self._generate_comparative_analysis(
                experiments,
                patterns,
                confoundings
            )
            
            # Step 7: Create visualization data
            visualization = self._create_visualization_data(
                graph_data,
                factor_analysis,
                patterns
            )
            
            # Step 8: Generate recommendations
            recommendations = await self._generate_recommendations(
                experiments,
                factor_analysis,
                patterns,
                confoundings
            )
            
            # Compile results
            result = {
                'success': True,
                'experiment_count': len(experiments),
                'graph_data': graph_data,
                'factors': self._serialize_factors(factors),
                'factor_analysis': factor_analysis,
                'patterns': patterns,
                'confoundings': confoundings,
                'comparative_analysis': comparative_analysis,
                'visualization': visualization,
                'recommendations': recommendations,
                'metadata': {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'analysis_focus': analysis_focus
                }
            }
            
            # Update knowledge graph
            await self._update_knowledge_graph(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in experiment mapping: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_experiment_graph(self, experiments: List[ExperimentData]) -> Dict:
        """Build a knowledge graph from experiments"""
        graph_data = {
            'nodes': [],
            'edges': [],
            'clusters': []
        }
        
        # Add experiment nodes
        for exp in experiments:
            node = {
                'id': exp.experiment_id,
                'label': f"{exp.experiment_type} - {exp.target_locus}",
                'type': 'experiment',
                'metadata': {
                    'variables': exp.variables,
                    'conditions': exp.conditions,
                    'success_metrics': exp.success_metrics
                }
            }
            graph_data['nodes'].append(node)
            self.knowledge_graph.add_node(exp.experiment_id, **node)
        
        # Identify relationships
        relationships = self._identify_relationships(experiments)
        
        # Add edges
        for rel in relationships:
            edge = {
                'source': rel.source_id,
                'target': rel.target_id,
                'type': rel.relationship_type,
                'weight': rel.strength,
                'metadata': rel.metadata
            }
            graph_data['edges'].append(edge)
            self.knowledge_graph.add_edge(
                rel.source_id, 
                rel.target_id,
                **edge
            )
        
        # Identify clusters
        clusters = self._identify_clusters(experiments)
        graph_data['clusters'] = clusters
        
        return graph_data
    
    def _identify_relationships(
        self,
        experiments: List[ExperimentData]
    ) -> List[ExperimentRelationship]:
        """Identify relationships between experiments"""
        relationships = []
        
        for i, exp1 in enumerate(experiments):
            for exp2 in experiments[i+1:]:
                # Check for variant relationships
                if self._are_variants(exp1, exp2):
                    relationships.append(ExperimentRelationship(
                        source_id=exp1.experiment_id,
                        target_id=exp2.experiment_id,
                        relationship_type="variant_of",
                        strength=self._calculate_similarity(exp1, exp2),
                        metadata={'varying_factors': self._get_varying_factors(exp1, exp2)}
                    ))
                
                # Check for control relationships
                if self._is_control_for(exp1, exp2):
                    relationships.append(ExperimentRelationship(
                        source_id=exp1.experiment_id,
                        target_id=exp2.experiment_id,
                        relationship_type="control_for",
                        strength=0.9,
                        metadata={'control_type': 'negative'}
                    ))
                
                # Check for temporal relationships
                if exp1.date_performed and exp2.date_performed:
                    if exp1.date_performed < exp2.date_performed:
                        if self._follows_from(exp1, exp2):
                            relationships.append(ExperimentRelationship(
                                source_id=exp1.experiment_id,
                                target_id=exp2.experiment_id,
                                relationship_type="follows_from",
                                strength=0.7,
                                metadata={'time_gap': str(exp2.date_performed - exp1.date_performed)}
                            ))
        
        return relationships
    
    def _identify_factors(self, experiments: List[ExperimentData]) -> List[ExperimentalFactor]:
        """Identify experimental factors across all experiments"""
        factors = []
        
        # Collect all variable keys
        variable_keys = set()
        condition_keys = set()
        
        for exp in experiments:
            variable_keys.update(exp.variables.keys())
            condition_keys.update(exp.conditions.keys())
        
        # Create factors for variables
        for key in variable_keys:
            values = []
            for exp in experiments:
                if key in exp.variables:
                    values.append(exp.variables[key])
            
            unique_values = list(set(values))
            is_controlled = len(unique_values) > 1
            
            factors.append(ExperimentalFactor(
                name=key,
                category=self._categorize_factor(key),
                values=unique_values,
                is_controlled=is_controlled
            ))
        
        # Create factors for conditions
        for key in condition_keys:
            values = []
            for exp in experiments:
                if key in exp.conditions:
                    values.append(exp.conditions[key])
            
            unique_values = list(set(values))
            is_controlled = len(unique_values) > 1
            
            factors.append(ExperimentalFactor(
                name=key,
                category="environmental",
                values=unique_values,
                is_controlled=is_controlled
            ))
        
        return factors
    
    async def _analyze_factor_influences(
        self,
        experiments: List[ExperimentData],
        factors: List[ExperimentalFactor],
        analysis_focus: Optional[str]
    ) -> Dict:
        """Analyze how factors influence outcomes"""
        influences = {}
        
        # Prepare data for analysis
        outcome_metrics = self._extract_outcome_metrics(experiments)
        
        for factor in factors:
            if not factor.is_controlled:
                continue
            
            # Group experiments by factor value
            grouped_experiments = self._group_by_factor(experiments, factor)
            
            # Calculate influence metrics
            influence_data = {
                'factor_name': factor.name,
                'category': factor.category,
                'values_tested': factor.values,
                'effect_size': 0.0,
                'consistency': 0.0,
                'significance': 0.0,
                'interactions': []
            }
            
            # Calculate effect size
            if len(grouped_experiments) > 1:
                effect_size = self._calculate_effect_size(
                    grouped_experiments,
                    outcome_metrics
                )
                influence_data['effect_size'] = effect_size
                
                # Calculate consistency
                consistency = self._calculate_consistency(grouped_experiments)
                influence_data['consistency'] = consistency
                
                # Statistical significance (simplified)
                if effect_size > 0.3 and consistency > 0.7:
                    influence_data['significance'] = 0.95
                elif effect_size > 0.2 and consistency > 0.5:
                    influence_data['significance'] = 0.8
                else:
                    influence_data['significance'] = 0.5
            
            # Check for interactions with other factors
            for other_factor in factors:
                if other_factor.name != factor.name and other_factor.is_controlled:
                    interaction = self._check_interaction(
                        factor,
                        other_factor,
                        experiments
                    )
                    if interaction['strength'] > 0.3:
                        influence_data['interactions'].append(interaction)
            
            influences[factor.name] = influence_data
            
            # Update factor influence score
            factor.influence_score = influence_data['effect_size'] * influence_data['consistency']
        
        # AI-enhanced interpretation
        interpretation = await self._interpret_influences(influences, analysis_focus)
        
        return {
            'factor_influences': influences,
            'interpretation': interpretation,
            'top_factors': self._get_top_factors(factors, 5)
        }
    
    def _detect_experimental_patterns(
        self,
        experiments: List[ExperimentData],
        factors: List[ExperimentalFactor]
    ) -> Dict:
        """Detect patterns in experimental data"""
        patterns = {
            'success_patterns': [],
            'failure_patterns': [],
            'optimization_trends': [],
            'unexpected_results': []
        }
        
        # Group experiments by success
        successful_exps = [e for e in experiments if self._is_successful(e)]
        failed_exps = [e for e in experiments if not self._is_successful(e)]
        
        # Identify success patterns
        if successful_exps:
            success_common_factors = self._find_common_factors(successful_exps)
            patterns['success_patterns'] = [{
                'description': f"Common factors in successful experiments",
                'factors': success_common_factors,
                'experiment_count': len(successful_exps),
                'confidence': len(success_common_factors) / len(factors) if factors else 0
            }]
        
        # Identify failure patterns
        if failed_exps:
            failure_common_factors = self._find_common_factors(failed_exps)
            patterns['failure_patterns'] = [{
                'description': f"Common factors in failed experiments",
                'factors': failure_common_factors,
                'experiment_count': len(failed_exps),
                'warning_level': 'high' if len(failed_exps) > len(successful_exps) else 'medium'
            }]
        
        # Identify optimization trends
        if len(experiments) > 3:
            trends = self._identify_optimization_trends(experiments)
            patterns['optimization_trends'] = trends
        
        # Identify unexpected results
        outliers = self._identify_outliers(experiments)
        patterns['unexpected_results'] = outliers
        
        return patterns
    
    def _identify_confoundings(
        self,
        experiments: List[ExperimentData],
        factors: List[ExperimentalFactor]
    ) -> List[Dict]:
        """Identify potential confounding variables"""
        confoundings = []
        
        # Check for correlated factors
        factor_correlations = self._calculate_factor_correlations(experiments, factors)
        
        for i, factor1 in enumerate(factors):
            for j, factor2 in enumerate(factors[i+1:], i+1):
                correlation = factor_correlations.get((factor1.name, factor2.name), 0)
                
                if abs(correlation) > 0.7:  # High correlation threshold
                    confoundings.append({
                        'factor1': factor1.name,
                        'factor2': factor2.name,
                        'correlation': correlation,
                        'type': 'correlated_factors',
                        'severity': 'high' if abs(correlation) > 0.9 else 'medium',
                        'recommendation': f"Consider controlling for {factor2.name} when varying {factor1.name}"
                    })
        
        # Check for batch effects
        batch_effects = self._detect_batch_effects(experiments)
        confoundings.extend(batch_effects)
        
        # Check for temporal confoundings
        temporal_confoundings = self._detect_temporal_confoundings(experiments)
        confoundings.extend(temporal_confoundings)
        
        return confoundings
    
    async def _generate_comparative_analysis(
        self,
        experiments: List[ExperimentData],
        patterns: Dict,
        confoundings: List[Dict]
    ) -> Dict:
        """Generate comparative analysis using AI"""
        
        # Prepare analysis context
        context = self._prepare_analysis_context(experiments, patterns, confoundings)
        
        prompt = f"""
        Analyze this series of experiments and provide insights:
        
        Experiment Series Context:
        {context}
        
        Provide:
        1. Key differences between successful and unsuccessful experiments
        2. Optimal parameter combinations based on the data
        3. Potential mechanisms explaining the observed patterns
        4. Recommendations for future experiments
        5. Warnings about confounding factors
        
        Focus on actionable insights for researchers.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in experimental design and data analysis, specializing in molecular biology."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        analysis_text = response.choices[0].message.content
        
        # Parse into structured format
        return self._parse_comparative_analysis(analysis_text)
    
    def _create_visualization_data(
        self,
        graph_data: Dict,
        factor_analysis: Dict,
        patterns: Dict
    ) -> Dict:
        """Create data for visualization"""
        
        # Prepare node positions using force-directed layout
        G = self.knowledge_graph
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        # Enhanced node data with positions
        nodes_with_layout = []
        for node in graph_data['nodes']:
            node_id = node['id']
            if node_id in pos:
                node['x'] = float(pos[node_id][0])
                node['y'] = float(pos[node_id][1])
            nodes_with_layout.append(node)
        
        # Factor influence chart data
        factor_chart = {
            'labels': [],
            'effect_sizes': [],
            'consistencies': [],
            'categories': []
        }
        
        for factor_name, influence in factor_analysis['factor_influences'].items():
            factor_chart['labels'].append(factor_name)
            factor_chart['effect_sizes'].append(influence['effect_size'])
            factor_chart['consistencies'].append(influence['consistency'])
            factor_chart['categories'].append(influence['category'])
        
        # Success rate timeline
        timeline_data = self._create_timeline_data(graph_data['nodes'])
        
        # Pattern summary
        pattern_summary = self._create_pattern_summary(patterns)
        
        return {
            'graph': {
                'nodes': nodes_with_layout,
                'edges': graph_data['edges'],
                'layout': 'force-directed'
            },
            'factor_chart': factor_chart,
            'timeline': timeline_data,
            'pattern_summary': pattern_summary,
            'visualization_type': 'multi-panel'
        }
    
    async def _generate_recommendations(
        self,
        experiments: List[ExperimentData],
        factor_analysis: Dict,
        patterns: Dict,
        confoundings: List[Dict]
    ) -> Dict:
        """Generate recommendations for future experiments"""
        
        recommendations = {
            'immediate_actions': [],
            'experiment_design': [],
            'optimization_strategy': [],
            'risk_mitigation': []
        }
        
        # Immediate actions based on patterns
        if patterns['failure_patterns']:
            recommendations['immediate_actions'].append({
                'priority': 'high',
                'action': 'Avoid factor combinations associated with failures',
                'details': patterns['failure_patterns'][0]['factors']
            })
        
        # Design recommendations based on top factors
        top_factors = factor_analysis.get('top_factors', [])
        for factor in top_factors[:3]:
            recommendations['experiment_design'].append({
                'factor': factor['name'],
                'recommendation': f"Focus on optimizing {factor['name']} - shows {factor['influence_score']:.2f} influence score",
                'suggested_values': self._suggest_factor_values(factor, experiments)
            })
        
        # Optimization strategy
        if patterns['optimization_trends']:
            trend = patterns['optimization_trends'][0]
            recommendations['optimization_strategy'].append({
                'approach': trend['description'],
                'expected_improvement': f"{trend.get('improvement_rate', 0)*100:.1f}%",
                'next_steps': self._generate_optimization_steps(trend, experiments)
            })
        
        # Risk mitigation for confoundings
        for confounding in confoundings[:3]:
            recommendations['risk_mitigation'].append({
                'risk': f"Confounding between {confounding.get('factor1', 'unknown')} and {confounding.get('factor2', 'unknown')}",
                'severity': confounding.get('severity', 'medium'),
                'mitigation': confounding.get('recommendation', 'Control for correlated factors')
            })
        
        # AI-enhanced recommendations
        ai_recommendations = await self._generate_ai_recommendations(
            experiments,
            factor_analysis,
            patterns
        )
        recommendations['ai_insights'] = ai_recommendations
        
        return recommendations
    
    async def _update_knowledge_graph(self, analysis_result: Dict):
        """Update the persistent knowledge graph"""
        try:
            kg = self.enhanced_rag.knowledge_graph
            
            # Add experiment series as entity
            series_entity = f"ExperimentSeries_{datetime.now().timestamp()}"
            kg.add_entity(
                entity=series_entity,
                entity_type="experiment_series",
                document_id=f"analysis_{datetime.now().timestamp()}"
            )
            
            # Add relationships for top factors
            for factor in analysis_result['factor_analysis'].get('top_factors', [])[:3]:
                kg.add_relation(
                    source=series_entity,
                    target=factor['name'],
                    relation_type="influenced_by",
                    strength=factor['influence_score']
                )
            
            # Add pattern entities
            for pattern_type, patterns in analysis_result['patterns'].items():
                if patterns:
                    pattern_entity = f"Pattern_{pattern_type}_{datetime.now().timestamp()}"
                    kg.add_entity(
                        entity=pattern_entity,
                        entity_type="experimental_pattern",
                        document_id=f"pattern_{datetime.now().timestamp()}"
                    )
                    
                    kg.add_relation(
                        source=series_entity,
                        target=pattern_entity,
                        relation_type="exhibits",
                        strength=0.8
                    )
                    
        except Exception as e:
            logger.error(f"Error updating knowledge graph: {e}")
    
    # Helper methods
    def _are_variants(self, exp1: ExperimentData, exp2: ExperimentData) -> bool:
        """Check if two experiments are variants of each other"""
        # Same target and type, but different variables
        if exp1.target_locus == exp2.target_locus and exp1.experiment_type == exp2.experiment_type:
            varying_count = sum(1 for k in exp1.variables 
                              if k in exp2.variables and exp1.variables[k] != exp2.variables[k])
            return 1 <= varying_count <= 3  # 1-3 varying factors indicates variant
        return False
    
    def _calculate_similarity(self, exp1: ExperimentData, exp2: ExperimentData) -> float:
        """Calculate similarity between experiments"""
        total_factors = set(exp1.variables.keys()) | set(exp2.variables.keys())
        if not total_factors:
            return 0.0
        
        matching_factors = sum(1 for k in total_factors 
                             if k in exp1.variables and k in exp2.variables 
                             and exp1.variables[k] == exp2.variables[k])
        
        return matching_factors / len(total_factors)
    
    def _get_varying_factors(self, exp1: ExperimentData, exp2: ExperimentData) -> List[str]:
        """Get factors that vary between experiments"""
        varying = []
        all_keys = set(exp1.variables.keys()) | set(exp2.variables.keys())
        
        for key in all_keys:
            val1 = exp1.variables.get(key)
            val2 = exp2.variables.get(key)
            if val1 != val2:
                varying.append(key)
        
        return varying
    
    def _is_control_for(self, exp1: ExperimentData, exp2: ExperimentData) -> bool:
        """Check if exp1 is a control for exp2"""
        # Simple heuristic: same conditions but exp1 has "control" or "wild-type" in variables
        if exp1.target_locus == exp2.target_locus:
            for value in exp1.variables.values():
                if isinstance(value, str) and any(term in value.lower() 
                                                for term in ['control', 'wild-type', 'wt', 'negative']):
                    return True
        return False
    
    def _follows_from(self, exp1: ExperimentData, exp2: ExperimentData) -> bool:
        """Check if exp2 follows from exp1"""
        # Check if exp2 builds on exp1's results
        similarity = self._calculate_similarity(exp1, exp2)
        return 0.5 < similarity < 0.9  # Some similarity but not identical
    
    def _identify_clusters(self, experiments: List[ExperimentData]) -> List[Dict]:
        """Identify clusters of related experiments"""
        # Simple clustering based on experiment type and target
        clusters = {}
        
        for exp in experiments:
            cluster_key = f"{exp.experiment_type}_{exp.target_locus}"
            if cluster_key not in clusters:
                clusters[cluster_key] = {
                    'id': cluster_key,
                    'label': f"{exp.experiment_type} on {exp.target_locus}",
                    'experiments': []
                }
            clusters[cluster_key]['experiments'].append(exp.experiment_id)
        
        return list(clusters.values())
    
    def _categorize_factor(self, factor_name: str) -> str:
        """Categorize a factor based on its name"""
        factor_lower = factor_name.lower()
        
        if any(term in factor_lower for term in ['cas', 'guide', 'grna', 'variant', 'mutant']):
            return 'genetic'
        elif any(term in factor_lower for term in ['temp', 'time', 'ph', 'concentration']):
            return 'environmental'
        elif any(term in factor_lower for term in ['protocol', 'method', 'technique']):
            return 'technical'
        elif any(term in factor_lower for term in ['reagent', 'buffer', 'media', 'enzyme']):
            return 'reagent'
        else:
            return 'other'
    
    def _extract_outcome_metrics(self, experiments: List[ExperimentData]) -> Dict[str, List[float]]:
        """Extract outcome metrics from experiments"""
        metrics = {}
        
        for exp in experiments:
            for metric_name, value in exp.success_metrics.items():
                if metric_name not in metrics:
                    metrics[metric_name] = []
                metrics[metric_name].append(float(value))
        
        return metrics
    
    def _group_by_factor(
        self,
        experiments: List[ExperimentData],
        factor: ExperimentalFactor
    ) -> Dict[str, List[ExperimentData]]:
        """Group experiments by factor value"""
        groups = {}
        
        for exp in experiments:
            value = exp.variables.get(factor.name) or exp.conditions.get(factor.name)
            if value is not None:
                value_str = str(value)
                if value_str not in groups:
                    groups[value_str] = []
                groups[value_str].append(exp)
        
        return groups
    
    def _calculate_effect_size(
        self,
        grouped_experiments: Dict[str, List[ExperimentData]],
        outcome_metrics: Dict[str, List[float]]
    ) -> float:
        """Calculate effect size (Cohen's d) for a factor"""
        if len(grouped_experiments) < 2:
            return 0.0
        
        # Get the two largest groups
        sorted_groups = sorted(grouped_experiments.items(), 
                             key=lambda x: len(x[1]), reverse=True)
        group1_exps = sorted_groups[0][1]
        group2_exps = sorted_groups[1][1]
        
        # Calculate mean outcomes for each group
        group1_outcomes = []
        group2_outcomes = []
        
        for exp in group1_exps:
            if exp.success_metrics:
                group1_outcomes.append(np.mean(list(exp.success_metrics.values())))
        
        for exp in group2_exps:
            if exp.success_metrics:
                group2_outcomes.append(np.mean(list(exp.success_metrics.values())))
        
        if not group1_outcomes or not group2_outcomes:
            return 0.0
        
        # Calculate Cohen's d
        mean1 = np.mean(group1_outcomes)
        mean2 = np.mean(group2_outcomes)
        std1 = np.std(group1_outcomes)
        std2 = np.std(group2_outcomes)
        
        pooled_std = np.sqrt((std1**2 + std2**2) / 2)
        
        if pooled_std == 0:
            return 0.0
        
        cohens_d = abs(mean1 - mean2) / pooled_std
        
        return min(cohens_d, 2.0)  # Cap at 2.0 for very large effects
    
    def _calculate_consistency(
        self,
        grouped_experiments: Dict[str, List[ExperimentData]]
    ) -> float:
        """Calculate consistency of outcomes within factor groups"""
        if not grouped_experiments:
            return 0.0
        
        consistencies = []
        
        for group_name, group_exps in grouped_experiments.items():
            if len(group_exps) > 1:
                # Calculate variance within group
                outcomes = []
                for exp in group_exps:
                    if exp.success_metrics:
                        outcomes.append(np.mean(list(exp.success_metrics.values())))
                
                if len(outcomes) > 1:
                    cv = np.std(outcomes) / (np.mean(outcomes) + 1e-6)  # Coefficient of variation
                    consistency = 1.0 / (1.0 + cv)  # Convert to 0-1 scale
                    consistencies.append(consistency)
        
        return np.mean(consistencies) if consistencies else 0.5
    
    def _check_interaction(
        self,
        factor1: ExperimentalFactor,
        factor2: ExperimentalFactor,
        experiments: List[ExperimentData]
    ) -> Dict:
        """Check for interaction between two factors"""
        # Simple interaction detection
        interaction_strength = 0.0
        
        # Group by both factors
        joint_groups = {}
        for exp in experiments:
            val1 = exp.variables.get(factor1.name) or exp.conditions.get(factor1.name)
            val2 = exp.variables.get(factor2.name) or exp.conditions.get(factor2.name)
            
            if val1 is not None and val2 is not None:
                key = f"{val1}_{val2}"
                if key not in joint_groups:
                    joint_groups[key] = []
                joint_groups[key].append(exp)
        
        # Check if interaction pattern exists (simplified)
        if len(joint_groups) >= 4:  # Need at least 4 combinations
            # Calculate if effect of factor1 depends on factor2
            interaction_strength = 0.5  # Placeholder - would need proper statistical test
        
        return {
            'factor': factor2.name,
            'strength': interaction_strength,
            'type': 'potential' if interaction_strength > 0.3 else 'none'
        }
    
    def _get_top_factors(
        self,
        factors: List[ExperimentalFactor],
        n: int
    ) -> List[Dict]:
        """Get top n influential factors"""
        sorted_factors = sorted(factors, key=lambda f: f.influence_score, reverse=True)
        
        return [
            {
                'name': f.name,
                'category': f.category,
                'influence_score': f.influence_score,
                'values_tested': f.values
            }
            for f in sorted_factors[:n]
        ]
    
    def _is_successful(self, experiment: ExperimentData) -> bool:
        """Determine if an experiment was successful"""
        if not experiment.success_metrics:
            return False
        
        # Simple heuristic: average metric > 0.5
        avg_success = np.mean(list(experiment.success_metrics.values()))
        return avg_success > 0.5
    
    def _find_common_factors(self, experiments: List[ExperimentData]) -> List[Dict]:
        """Find factors common to a set of experiments"""
        if not experiments:
            return []
        
        common_factors = []
        
        # Get all factor keys
        all_keys = set()
        for exp in experiments:
            all_keys.update(exp.variables.keys())
            all_keys.update(exp.conditions.keys())
        
        # Check which factors have consistent values
        for key in all_keys:
            values = []
            for exp in experiments:
                value = exp.variables.get(key) or exp.conditions.get(key)
                if value is not None:
                    values.append(value)
            
            if values and len(set(values)) == 1:  # All same value
                common_factors.append({
                    'factor': key,
                    'value': values[0],
                    'frequency': len(values) / len(experiments)
                })
        
        return common_factors
    
    def _identify_optimization_trends(self, experiments: List[ExperimentData]) -> List[Dict]:
        """Identify optimization trends over time"""
        trends = []
        
        # Sort by date if available
        dated_exps = [e for e in experiments if e.date_performed]
        if len(dated_exps) < 3:
            return trends
        
        dated_exps.sort(key=lambda e: e.date_performed)
        
        # Check for improvement over time
        early_success = np.mean([self._is_successful(e) for e in dated_exps[:len(dated_exps)//2]])
        late_success = np.mean([self._is_successful(e) for e in dated_exps[len(dated_exps)//2:]])
        
        if late_success > early_success:
            improvement_rate = (late_success - early_success) / early_success if early_success > 0 else 1.0
            trends.append({
                'description': 'Success rate improving over time',
                'improvement_rate': improvement_rate,
                'trend_type': 'positive',
                'confidence': min(0.5 + improvement_rate, 0.95)
            })
        
        return trends
    
    def _identify_outliers(self, experiments: List[ExperimentData]) -> List[Dict]:
        """Identify experimental outliers"""
        outliers = []
        
        # Calculate mean and std of success metrics
        all_metrics = []
        for exp in experiments:
            if exp.success_metrics:
                all_metrics.append(np.mean(list(exp.success_metrics.values())))
        
        if len(all_metrics) < 3:
            return outliers
        
        mean_metric = np.mean(all_metrics)
        std_metric = np.std(all_metrics)
        
        # Identify outliers (>2 std from mean)
        for i, exp in enumerate(experiments):
            if exp.success_metrics:
                exp_metric = np.mean(list(exp.success_metrics.values()))
                z_score = abs(exp_metric - mean_metric) / (std_metric + 1e-6)
                
                if z_score > 2:
                    outliers.append({
                        'experiment_id': exp.experiment_id,
                        'metric_value': exp_metric,
                        'z_score': z_score,
                        'type': 'high' if exp_metric > mean_metric else 'low',
                        'factors': exp.variables
                    })
        
        return outliers
    
    def _calculate_factor_correlations(
        self,
        experiments: List[ExperimentData],
        factors: List[ExperimentalFactor]
    ) -> Dict[Tuple[str, str], float]:
        """Calculate correlations between factors"""
        correlations = {}
        
        # Convert factor values to numeric where possible
        factor_data = {}
        for factor in factors:
            if factor.is_controlled:
                values = []
                for exp in experiments:
                    value = exp.variables.get(factor.name) or exp.conditions.get(factor.name)
                    if value is not None:
                        # Try to convert to numeric
                        try:
                            numeric_value = float(value)
                        except:
                            # Use ordinal encoding for categorical
                            unique_values = factor.values
                            numeric_value = unique_values.index(value) if value in unique_values else -1
                        values.append(numeric_value)
                    else:
                        values.append(np.nan)
                
                factor_data[factor.name] = values
        
        # Calculate correlations
        for i, factor1 in enumerate(factors):
            if not factor1.is_controlled:
                continue
            for j, factor2 in enumerate(factors[i+1:], i+1):
                if not factor2.is_controlled:
                    continue
                
                data1 = factor_data.get(factor1.name, [])
                data2 = factor_data.get(factor2.name, [])
                
                if data1 and data2:
                    # Remove NaN pairs
                    valid_pairs = [(d1, d2) for d1, d2 in zip(data1, data2) 
                                 if not np.isnan(d1) and not np.isnan(d2)]
                    
                    if len(valid_pairs) > 2:
                        d1_vals, d2_vals = zip(*valid_pairs)
                        correlation = np.corrcoef(d1_vals, d2_vals)[0, 1]
                        correlations[(factor1.name, factor2.name)] = correlation
        
        return correlations
    
    def _detect_batch_effects(self, experiments: List[ExperimentData]) -> List[Dict]:
        """Detect potential batch effects"""
        batch_effects = []
        
        # Group by researcher
        researcher_groups = {}
        for exp in experiments:
            if exp.researcher:
                if exp.researcher not in researcher_groups:
                    researcher_groups[exp.researcher] = []
                researcher_groups[exp.researcher].append(exp)
        
        if len(researcher_groups) > 1:
            # Check if success rates differ by researcher
            researcher_success = {}
            for researcher, exps in researcher_groups.items():
                success_rates = [self._is_successful(e) for e in exps]
                researcher_success[researcher] = np.mean(success_rates)
            
            # Check for significant differences
            success_values = list(researcher_success.values())
            if max(success_values) - min(success_values) > 0.3:
                batch_effects.append({
                    'type': 'researcher_effect',
                    'severity': 'medium',
                    'details': researcher_success,
                    'recommendation': 'Consider researcher as a blocking factor in analysis'
                })
        
        return batch_effects
    
    def _detect_temporal_confoundings(self, experiments: List[ExperimentData]) -> List[Dict]:
        """Detect temporal confounding factors"""
        temporal_confoundings = []
        
        dated_exps = [e for e in experiments if e.date_performed]
        if len(dated_exps) < 4:
            return temporal_confoundings
        
        # Sort by date
        dated_exps.sort(key=lambda e: e.date_performed)
        
        # Check if certain factors changed over time
        time_periods = {
            'early': dated_exps[:len(dated_exps)//2],
            'late': dated_exps[len(dated_exps)//2:]
        }
        
        # Compare factor distributions
        for period_name, period_exps in time_periods.items():
            common_factors = self._find_common_factors(period_exps)
            if common_factors:
                temporal_confoundings.append({
                    'type': 'temporal_bias',
                    'period': period_name,
                    'common_factors': common_factors[:3],
                    'severity': 'low',
                    'recommendation': f"Factors clustered in {period_name} period may confound temporal analysis"
                })
        
        return temporal_confoundings
    
    def _prepare_analysis_context(
        self,
        experiments: List[ExperimentData],
        patterns: Dict,
        confoundings: List[Dict]
    ) -> str:
        """Prepare context for AI analysis"""
        context = f"""
        Number of experiments: {len(experiments)}
        Experiment types: {', '.join(set(e.experiment_type for e in experiments))}
        Target loci: {', '.join(set(e.target_locus for e in experiments))}
        
        Success patterns found: {len(patterns.get('success_patterns', []))}
        Failure patterns found: {len(patterns.get('failure_patterns', []))}
        Optimization trends: {patterns.get('optimization_trends', [])}
        
        Confounding factors identified: {len(confoundings)}
        Main confoundings: {', '.join(c.get('type', 'unknown') for c in confoundings[:3])}
        """
        
        return context
    
    def _parse_comparative_analysis(self, analysis_text: str) -> Dict:
        """Parse AI analysis into structured format"""
        sections = {
            'key_differences': '',
            'optimal_parameters': '',
            'mechanisms': '',
            'future_recommendations': '',
            'warnings': ''
        }
        
        lines = analysis_text.split('\n')
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if 'key difference' in line_lower or 'difference' in line_lower:
                current_section = 'key_differences'
            elif 'optimal' in line_lower or 'parameter' in line_lower:
                current_section = 'optimal_parameters'
            elif 'mechanism' in line_lower:
                current_section = 'mechanisms'
            elif 'recommend' in line_lower or 'future' in line_lower:
                current_section = 'future_recommendations'
            elif 'warning' in line_lower or 'confound' in line_lower:
                current_section = 'warnings'
            elif current_section and line.strip():
                sections[current_section] += line + '\n'
        
        return sections
    
    def _create_timeline_data(self, nodes: List[Dict]) -> List[Dict]:
        """Create timeline visualization data"""
        timeline = []
        
        for node in nodes:
            if 'date_performed' in node.get('metadata', {}):
                timeline.append({
                    'date': node['metadata']['date_performed'],
                    'experiment': node['label'],
                    'success': node['metadata'].get('success_metrics', {})
                })
        
        # Sort by date
        timeline.sort(key=lambda x: x['date'])
        
        return timeline
    
    def _create_pattern_summary(self, patterns: Dict) -> Dict:
        """Create summary of patterns for visualization"""
        summary = {
            'pattern_counts': {},
            'key_insights': []
        }
        
        for pattern_type, pattern_list in patterns.items():
            summary['pattern_counts'][pattern_type] = len(pattern_list)
            
            if pattern_list:
                # Extract key insight
                if pattern_type == 'success_patterns':
                    summary['key_insights'].append({
                        'type': 'success',
                        'message': f"Found {len(pattern_list)} success patterns",
                        'importance': 'high'
                    })
                elif pattern_type == 'failure_patterns':
                    summary['key_insights'].append({
                        'type': 'warning',
                        'message': f"Identified {len(pattern_list)} failure patterns",
                        'importance': 'high'
                    })
        
        return summary
    
    def _suggest_factor_values(
        self,
        factor: Dict,
        experiments: List[ExperimentData]
    ) -> List[str]:
        """Suggest optimal values for a factor"""
        # Group experiments by factor value and calculate success
        value_success = {}
        
        for exp in experiments:
            value = exp.variables.get(factor['name']) or exp.conditions.get(factor['name'])
            if value is not None:
                if value not in value_success:
                    value_success[value] = []
                value_success[value].append(self._is_successful(exp))
        
        # Calculate average success for each value
        value_scores = {}
        for value, successes in value_success.items():
            value_scores[value] = np.mean(successes)
        
        # Sort by success rate
        sorted_values = sorted(value_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top 3 values
        return [str(val) for val, score in sorted_values[:3]]
    
    def _generate_optimization_steps(
        self,
        trend: Dict,
        experiments: List[ExperimentData]
    ) -> List[str]:
        """Generate specific optimization steps"""
        steps = []
        
        if trend['trend_type'] == 'positive':
            steps.append("Continue current optimization trajectory")
            steps.append("Increase sample size to confirm improvements")
            steps.append("Document successful modifications for reproducibility")
        else:
            steps.append("Review recent protocol changes")
            steps.append("Revert to previously successful conditions")
            steps.append("Identify and address new variables")
        
        return steps
    
    async def _interpret_influences(
        self,
        influences: Dict,
        analysis_focus: Optional[str]
    ) -> str:
        """Generate AI interpretation of factor influences"""
        
        # Prepare influence summary
        influence_summary = []
        for factor_name, data in influences.items():
            influence_summary.append(
                f"{factor_name}: effect={data['effect_size']:.2f}, "
                f"consistency={data['consistency']:.2f}, "
                f"interactions={len(data['interactions'])}"
            )
        
        prompt = f"""
        Interpret these experimental factor influences:
        
        {chr(10).join(influence_summary)}
        
        Analysis focus: {analysis_focus or 'general optimization'}
        
        Provide:
        1. Which factors are most important and why
        2. How factors interact with each other
        3. Practical recommendations for optimization
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in experimental design and statistical analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    async def _generate_ai_recommendations(
        self,
        experiments: List[ExperimentData],
        factor_analysis: Dict,
        patterns: Dict
    ) -> List[Dict]:
        """Generate AI-powered recommendations"""
        
        # Prepare context
        exp_summary = f"{len(experiments)} experiments analyzed"
        top_factors = factor_analysis.get('top_factors', [])[:3]
        success_rate = sum(1 for e in experiments if self._is_successful(e)) / len(experiments)
        
        prompt = f"""
        Based on this experimental analysis:
        - {exp_summary}
        - Overall success rate: {success_rate:.1%}
        - Top influential factors: {', '.join(f['name'] for f in top_factors)}
        - Patterns identified: {len(patterns.get('success_patterns', []))} success, {len(patterns.get('failure_patterns', []))} failure
        
        Generate 3 specific, actionable recommendations for the next experiments.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a senior research scientist providing experimental guidance."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=500
        )
        
        # Parse recommendations
        recommendations = []
        lines = response.choices[0].message.content.split('\n')
        
        for line in lines:
            if line.strip() and (line[0].isdigit() or line.startswith('-')):
                recommendations.append({
                    'recommendation': line.strip().lstrip('0123456789.- '),
                    'source': 'AI analysis',
                    'confidence': 'high'
                })
        
        return recommendations[:3]
    
    def _serialize_factors(self, factors: List[ExperimentalFactor]) -> List[Dict]:
        """Serialize factors for output"""
        return [
            {
                'name': f.name,
                'category': f.category,
                'values': f.values,
                'is_controlled': f.is_controlled,
                'influence_score': f.influence_score
            }
            for f in factors
        ]


# Singleton instance
_experiment_mapping_service = None

def get_experiment_mapping_service() -> ExperimentMappingService:
    """Get singleton instance of experiment mapping service"""
    global _experiment_mapping_service
    if _experiment_mapping_service is None:
        _experiment_mapping_service = ExperimentMappingService()
    return _experiment_mapping_service