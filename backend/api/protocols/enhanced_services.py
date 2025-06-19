"""
Enhanced Protocol Builder Services
AI-powered protocol generation with lab context awareness
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from django.conf import settings
from django.db import models
from openai import OpenAI

from api.models import Document, QueryHistory
from api.search.real_rag import search_documents
from api.rag.enhanced_rag import get_enhanced_rag_pipeline

logger = logging.getLogger(__name__)


@dataclass
class ProtocolRequirements:
    """Detailed requirements for protocol generation"""
    experiment_type: str
    sample_type: str
    sample_size: int
    objectives: List[str]
    constraints: Dict[str, any] = field(default_factory=dict)
    safety_level: str = "BSL-1"
    timeline: str = "flexible"
    budget: str = "standard"


@dataclass
class LabCapabilities:
    """Lab capabilities and resources"""
    equipment: List[str]
    reagents: List[str]
    expertise: List[str]
    typical_protocols: List[str]


@dataclass
class ProtocolOptimization:
    """Protocol optimization parameters"""
    optimize_for: str  # "time", "cost", "yield", "quality"
    critical_steps: List[str]
    flexibility_areas: List[str]


class ExperimentHistory(models.Model):
    """Track experiment history for learning"""
    protocol_id = models.ForeignKey(Document, on_delete=models.CASCADE)
    success_rate = models.FloatField()
    modifications = models.JSONField()
    lessons_learned = models.TextField()
    researcher = models.CharField(max_length=255)
    date_performed = models.DateTimeField()
    conditions = models.JSONField()
    
    class Meta:
        app_label = 'api'


class EnhancedProtocolService:
    """Enhanced protocol generation with scientist-like reasoning"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.enhanced_rag = get_enhanced_rag_pipeline()
        
    async def generate_intelligent_protocol(
        self,
        requirements: ProtocolRequirements,
        lab_capabilities: Optional[LabCapabilities] = None,
        optimization: Optional[ProtocolOptimization] = None,
        session_id: Optional[str] = None,
        base_protocol_id: Optional[int] = None
    ) -> Dict:
        """
        Generate an intelligent protocol with scientist-level reasoning
        
        Args:
            requirements: Detailed experiment requirements
            lab_capabilities: Available lab resources
            optimization: Optimization parameters
            session_id: Session ID for context
            base_protocol_id: Optional base protocol to modify
            
        Returns:
            Dict containing comprehensive protocol with reasoning
        """
        try:
            # Step 1: Analyze requirements and find relevant protocols
            relevant_protocols = await self._find_relevant_protocols(requirements)
            
            # Step 2: Analyze past experiment outcomes
            historical_insights = await self._analyze_experiment_history(
                requirements.experiment_type,
                relevant_protocols
            )
            
            # Step 3: Check equipment and reagent compatibility
            compatibility_check = self._check_lab_compatibility(
                requirements,
                lab_capabilities
            )
            
            # Step 4: Generate protocol with multi-stage reasoning
            protocol_draft = await self._generate_protocol_draft(
                requirements,
                relevant_protocols,
                historical_insights,
                lab_capabilities,
                optimization
            )
            
            # Step 5: Optimize based on constraints
            optimized_protocol = await self._optimize_protocol(
                protocol_draft,
                requirements.constraints,
                optimization
            )
            
            # Step 6: Add safety and quality control
            final_protocol = await self._add_safety_and_qc(
                optimized_protocol,
                requirements.safety_level
            )
            
            # Step 7: Generate troubleshooting guide
            troubleshooting = await self._generate_troubleshooting(
                final_protocol,
                historical_insights
            )
            
            # Step 8: Create validation criteria
            validation = self._create_validation_criteria(
                requirements.objectives,
                final_protocol
            )
            
            # Compile comprehensive result
            result = {
                'success': True,
                'protocol': final_protocol,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'session_id': session_id,
                    'optimization_applied': optimization.optimize_for if optimization else 'none',
                    'confidence_score': self._calculate_protocol_confidence(
                        final_protocol,
                        historical_insights,
                        compatibility_check
                    )
                },
                'reasoning': {
                    'requirements_analysis': self._format_requirements_analysis(requirements),
                    'historical_insights': historical_insights,
                    'compatibility_check': compatibility_check,
                    'optimization_rationale': self._explain_optimization(optimization)
                },
                'troubleshooting_guide': troubleshooting,
                'validation_criteria': validation,
                'reference_protocols': relevant_protocols[:3],
                'alternatives': await self._suggest_alternatives(
                    requirements,
                    final_protocol
                ),
                'cost_estimate': self._estimate_costs(final_protocol, lab_capabilities),
                'timeline_estimate': self._estimate_timeline(final_protocol)
            }
            
            # Store in knowledge graph
            await self._update_protocol_knowledge(requirements, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced protocol generation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _find_relevant_protocols(self, requirements: ProtocolRequirements) -> List[Dict]:
        """Find protocols relevant to the requirements"""
        
        # Build search query from requirements
        search_terms = [
            requirements.experiment_type,
            requirements.sample_type,
            *requirements.objectives[:2]
        ]
        
        query = " ".join(search_terms)
        
        # Search for similar protocols
        results = search_documents(
            query=query,
            doc_type='protocol',
            top_k=10
        )
        
        # Score protocols based on relevance
        scored_protocols = []
        for protocol in results:
            score = self._score_protocol_relevance(protocol, requirements)
            protocol['relevance_score'] = score
            scored_protocols.append(protocol)
        
        # Sort by relevance
        scored_protocols.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return scored_protocols
    
    async def _analyze_experiment_history(
        self,
        experiment_type: str,
        relevant_protocols: List[Dict]
    ) -> Dict:
        """Analyze historical experiment data for insights"""
        
        insights = {
            'common_pitfalls': [],
            'success_factors': [],
            'typical_modifications': [],
            'average_success_rate': 0.0,
            'lessons_learned': []
        }
        
        try:
            # Query experiment history
            protocol_ids = [p['id'] for p in relevant_protocols[:5] if 'id' in p]
            
            if not protocol_ids:
                return insights
            
            # For now, generate synthetic insights based on experiment type
            # In production, this would query the ExperimentHistory model
            
            if 'pcr' in experiment_type.lower():
                insights['common_pitfalls'] = [
                    "Primer dimers due to suboptimal annealing temperature",
                    "Non-specific amplification from contamination",
                    "Poor yield from degraded template"
                ]
                insights['success_factors'] = [
                    "Gradient PCR to optimize annealing temperature",
                    "Fresh preparation of reagents",
                    "Template quality verification"
                ]
                insights['average_success_rate'] = 0.85
                
            elif 'transfection' in experiment_type.lower():
                insights['common_pitfalls'] = [
                    "Low transfection efficiency due to cell confluence",
                    "Toxicity from excessive reagent concentration",
                    "Mycoplasma contamination affecting results"
                ]
                insights['success_factors'] = [
                    "Optimal cell confluence (70-80%)",
                    "Reagent optimization for cell type",
                    "Regular mycoplasma testing"
                ]
                insights['average_success_rate'] = 0.70
                
            elif 'crispr' in experiment_type.lower():
                insights['common_pitfalls'] = [
                    "Off-target effects from suboptimal guide design",
                    "Low editing efficiency in certain cell types",
                    "Mosaic editing in primary cells"
                ]
                insights['success_factors'] = [
                    "Multiple guide RNA screening",
                    "Optimized delivery method for cell type",
                    "Validation with multiple methods"
                ]
                insights['average_success_rate'] = 0.65
                
            insights['typical_modifications'] = [
                "Adjusted incubation times based on cell type",
                "Modified reagent concentrations",
                "Added validation steps"
            ]
            
            insights['lessons_learned'] = [
                "Always include proper controls",
                "Pilot experiments save time in the long run",
                "Documentation of deviations is crucial"
            ]
            
        except Exception as e:
            logger.error(f"Error analyzing experiment history: {e}")
        
        return insights
    
    def _check_lab_compatibility(
        self,
        requirements: ProtocolRequirements,
        lab_capabilities: Optional[LabCapabilities]
    ) -> Dict:
        """Check compatibility between requirements and lab capabilities"""
        
        compatibility = {
            'overall_compatible': True,
            'equipment_gaps': [],
            'reagent_gaps': [],
            'expertise_gaps': [],
            'recommendations': []
        }
        
        if not lab_capabilities:
            compatibility['recommendations'].append(
                "Lab capabilities not specified - protocol assumes standard molecular biology lab"
            )
            return compatibility
        
        # Check equipment requirements
        required_equipment = self._infer_required_equipment(requirements)
        for equipment in required_equipment:
            if equipment not in lab_capabilities.equipment:
                compatibility['equipment_gaps'].append(equipment)
                compatibility['overall_compatible'] = False
        
        # Check expertise requirements
        required_expertise = self._infer_required_expertise(requirements)
        for expertise in required_expertise:
            if expertise not in lab_capabilities.expertise:
                compatibility['expertise_gaps'].append(expertise)
        
        # Generate recommendations
        if compatibility['equipment_gaps']:
            compatibility['recommendations'].append(
                f"Consider outsourcing or acquiring: {', '.join(compatibility['equipment_gaps'])}"
            )
        
        if compatibility['expertise_gaps']:
            compatibility['recommendations'].append(
                f"Training recommended for: {', '.join(compatibility['expertise_gaps'])}"
            )
        
        return compatibility
    
    async def _generate_protocol_draft(
        self,
        requirements: ProtocolRequirements,
        relevant_protocols: List[Dict],
        historical_insights: Dict,
        lab_capabilities: Optional[LabCapabilities],
        optimization: Optional[ProtocolOptimization]
    ) -> Dict:
        """Generate initial protocol draft with reasoning"""
        
        # Prepare context from relevant protocols
        protocol_context = self._format_protocol_context(relevant_protocols[:3])
        
        # Create comprehensive prompt
        prompt = f"""
        You are an experienced molecular biologist designing a protocol.
        
        Requirements:
        - Experiment Type: {requirements.experiment_type}
        - Sample Type: {requirements.sample_type}
        - Sample Size: {requirements.sample_size}
        - Objectives: {json.dumps(requirements.objectives)}
        - Constraints: {json.dumps(requirements.constraints)}
        - Safety Level: {requirements.safety_level}
        - Timeline: {requirements.timeline}
        - Budget: {requirements.budget}
        
        Lab Capabilities:
        {self._format_lab_capabilities(lab_capabilities)}
        
        Historical Insights:
        - Common Pitfalls: {json.dumps(historical_insights['common_pitfalls'])}
        - Success Factors: {json.dumps(historical_insights['success_factors'])}
        - Average Success Rate: {historical_insights['average_success_rate']}
        
        Reference Protocols:
        {protocol_context}
        
        Optimization Focus: {optimization.optimize_for if optimization else 'balanced approach'}
        
        Generate a detailed protocol that:
        1. Addresses all objectives
        2. Incorporates lessons from historical data
        3. Optimizes for the specified parameter
        4. Includes critical quality control steps
        5. Provides clear, actionable steps
        
        Format the protocol with:
        - Title
        - Summary
        - Materials and Reagents (with catalog numbers where relevant)
        - Equipment Required
        - Safety Considerations
        - Detailed Procedure (numbered steps with timing)
        - Quality Control Checkpoints
        - Expected Results
        - Data Analysis Guidelines
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert molecular biologist with 20 years of experience in protocol development and optimization."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for consistency
            max_tokens=4000
        )
        
        protocol_text = response.choices[0].message.content
        
        # Parse into structured format
        return self._parse_protocol_draft(protocol_text)
    
    async def _optimize_protocol(
        self,
        protocol_draft: Dict,
        constraints: Dict,
        optimization: Optional[ProtocolOptimization]
    ) -> Dict:
        """Optimize protocol based on constraints and parameters"""
        
        if not optimization:
            return protocol_draft
        
        optimized = protocol_draft.copy()
        
        if optimization.optimize_for == "time":
            optimized = self._optimize_for_time(optimized, optimization)
        elif optimization.optimize_for == "cost":
            optimized = self._optimize_for_cost(optimized, constraints)
        elif optimization.optimize_for == "yield":
            optimized = self._optimize_for_yield(optimized)
        elif optimization.optimize_for == "quality":
            optimized = self._optimize_for_quality(optimized)
        
        # Apply critical step protection
        optimized = self._protect_critical_steps(optimized, optimization.critical_steps)
        
        return optimized
    
    async def _add_safety_and_qc(self, protocol: Dict, safety_level: str) -> Dict:
        """Add comprehensive safety measures and quality control"""
        
        enhanced_protocol = protocol.copy()
        
        # Add safety measures based on BSL level
        safety_measures = self._generate_safety_measures(safety_level, protocol)
        enhanced_protocol['safety_measures'] = safety_measures
        
        # Add quality control checkpoints
        qc_checkpoints = self._generate_qc_checkpoints(protocol)
        enhanced_protocol['quality_control'] = qc_checkpoints
        
        # Add validation steps
        validation_steps = self._generate_validation_steps(protocol)
        enhanced_protocol['validation'] = validation_steps
        
        return enhanced_protocol
    
    async def _generate_troubleshooting(
        self,
        protocol: Dict,
        historical_insights: Dict
    ) -> Dict:
        """Generate comprehensive troubleshooting guide"""
        
        troubleshooting = {
            'common_issues': [],
            'preventive_measures': [],
            'diagnostic_flowchart': [],
            'emergency_procedures': []
        }
        
        # Extract potential issues from protocol steps
        for step in protocol.get('procedure', []):
            potential_issues = self._identify_potential_issues(step)
            for issue in potential_issues:
                troubleshooting['common_issues'].append({
                    'step': step.get('number', ''),
                    'issue': issue['description'],
                    'symptoms': issue['symptoms'],
                    'solutions': issue['solutions']
                })
        
        # Add historical issues
        for pitfall in historical_insights.get('common_pitfalls', []):
            troubleshooting['preventive_measures'].append({
                'issue': pitfall,
                'prevention': self._generate_prevention_strategy(pitfall)
            })
        
        # Create diagnostic flowchart for major issues
        troubleshooting['diagnostic_flowchart'] = self._create_diagnostic_flowchart(
            protocol,
            troubleshooting['common_issues']
        )
        
        return troubleshooting
    
    def _create_validation_criteria(
        self,
        objectives: List[str],
        protocol: Dict
    ) -> Dict:
        """Create validation criteria for protocol success"""
        
        validation = {
            'success_criteria': [],
            'quantitative_metrics': [],
            'qualitative_assessments': [],
            'decision_tree': {}
        }
        
        # Generate success criteria from objectives
        for objective in objectives:
            criteria = self._objective_to_criteria(objective)
            validation['success_criteria'].extend(criteria)
        
        # Extract quantitative metrics from protocol
        validation['quantitative_metrics'] = self._extract_metrics(protocol)
        
        # Add qualitative assessments
        validation['qualitative_assessments'] = [
            "Visual inspection of results",
            "Consistency across replicates",
            "Absence of contamination indicators"
        ]
        
        # Create decision tree
        validation['decision_tree'] = self._create_validation_decision_tree(
            validation['success_criteria']
        )
        
        return validation
    
    async def _suggest_alternatives(
        self,
        requirements: ProtocolRequirements,
        primary_protocol: Dict
    ) -> List[Dict]:
        """Suggest alternative approaches"""
        
        alternatives = []
        
        # Generate alternatives based on different optimization strategies
        optimization_strategies = ["time", "cost", "yield", "simplicity"]
        
        for strategy in optimization_strategies:
            if strategy != primary_protocol.get('optimization_focus'):
                alternative = {
                    'name': f"Alternative optimized for {strategy}",
                    'key_differences': self._identify_key_differences(
                        primary_protocol,
                        strategy
                    ),
                    'trade_offs': self._identify_trade_offs(strategy),
                    'when_to_use': self._when_to_use_alternative(strategy)
                }
                alternatives.append(alternative)
        
        return alternatives[:3]  # Return top 3 alternatives
    
    def _calculate_protocol_confidence(
        self,
        protocol: Dict,
        historical_insights: Dict,
        compatibility: Dict
    ) -> float:
        """Calculate confidence score for the protocol"""
        
        confidence = 0.5  # Base confidence
        
        # Adjust based on historical success rate
        if historical_insights.get('average_success_rate'):
            confidence += historical_insights['average_success_rate'] * 0.2
        
        # Adjust based on compatibility
        if compatibility.get('overall_compatible'):
            confidence += 0.2
        else:
            confidence -= 0.1 * len(compatibility.get('equipment_gaps', []))
        
        # Adjust based on protocol completeness
        if protocol.get('procedure') and len(protocol['procedure']) > 5:
            confidence += 0.1
        
        if protocol.get('quality_control'):
            confidence += 0.1
        
        if protocol.get('validation'):
            confidence += 0.1
        
        return min(confidence, 0.95)
    
    def _estimate_costs(self, protocol: Dict, lab_capabilities: Optional[LabCapabilities]) -> Dict:
        """Estimate protocol costs"""
        
        costs = {
            'reagents': 0,
            'consumables': 0,
            'equipment_rental': 0,
            'labor': 0,
            'total': 0,
            'breakdown': []
        }
        
        # Estimate reagent costs
        for material in protocol.get('materials', []):
            estimated_cost = self._estimate_material_cost(material)
            costs['reagents'] += estimated_cost
            costs['breakdown'].append({
                'item': material.get('name', 'Unknown'),
                'cost': estimated_cost,
                'category': 'reagent'
            })
        
        # Estimate consumables
        consumables_cost = len(protocol.get('procedure', [])) * 10  # $10 per step estimate
        costs['consumables'] = consumables_cost
        
        # Estimate labor (hours * rate)
        total_time = self._calculate_total_time(protocol)
        costs['labor'] = total_time * 50  # $50/hour estimate
        
        costs['total'] = sum([costs['reagents'], costs['consumables'], 
                             costs['equipment_rental'], costs['labor']])
        
        return costs
    
    def _estimate_timeline(self, protocol: Dict) -> Dict:
        """Estimate protocol timeline"""
        
        timeline = {
            'preparation': 0,
            'execution': 0,
            'analysis': 0,
            'total_active': 0,
            'total_elapsed': 0,
            'critical_path': []
        }
        
        # Calculate preparation time
        timeline['preparation'] = 2  # 2 hours default
        
        # Calculate execution time
        for step in protocol.get('procedure', []):
            step_time = self._parse_step_time(step.get('description', ''))
            timeline['execution'] += step_time
        
        # Calculate analysis time
        timeline['analysis'] = 4  # 4 hours default
        
        timeline['total_active'] = sum([timeline['preparation'], 
                                       timeline['execution'], 
                                       timeline['analysis']])
        
        # Account for incubation/waiting times
        timeline['total_elapsed'] = timeline['total_active'] * 1.5  # 50% waiting time estimate
        
        return timeline
    
    async def _update_protocol_knowledge(self, requirements: ProtocolRequirements, result: Dict):
        """Update knowledge graph with protocol information"""
        try:
            kg = self.enhanced_rag.knowledge_graph
            
            # Add protocol as entity
            protocol_entity = f"Protocol: {result['protocol'].get('title', 'Generated Protocol')}"
            kg.add_entity(
                entity=protocol_entity,
                entity_type="protocol",
                document_id=f"protocol_{datetime.now().timestamp()}"
            )
            
            # Add relationships to experiment type
            kg.add_relation(
                source=protocol_entity,
                target=requirements.experiment_type,
                relation_type="designed_for",
                strength=0.9
            )
            
            # Add relationships to objectives
            for objective in requirements.objectives[:3]:
                kg.add_relation(
                    source=protocol_entity,
                    target=objective,
                    relation_type="achieves",
                    strength=0.8
                )
                
        except Exception as e:
            logger.error(f"Error updating protocol knowledge: {e}")
    
    # Helper methods
    def _score_protocol_relevance(self, protocol: Dict, requirements: ProtocolRequirements) -> float:
        """Score protocol relevance to requirements"""
        score = 0.0
        
        # Check experiment type match
        if requirements.experiment_type.lower() in protocol.get('title', '').lower():
            score += 0.3
        
        # Check sample type match
        if requirements.sample_type.lower() in protocol.get('snippet', '').lower():
            score += 0.2
        
        # Check objectives overlap
        protocol_text = f"{protocol.get('title', '')} {protocol.get('snippet', '')}"
        for objective in requirements.objectives:
            if any(word in protocol_text.lower() for word in objective.lower().split()):
                score += 0.1
        
        return min(score, 1.0)
    
    def _infer_required_equipment(self, requirements: ProtocolRequirements) -> List[str]:
        """Infer required equipment from experiment type"""
        equipment_map = {
            'pcr': ['Thermal cycler', 'Gel electrophoresis', 'UV transilluminator'],
            'cell culture': ['Biosafety cabinet', 'CO2 incubator', 'Microscope'],
            'transfection': ['Biosafety cabinet', 'CO2 incubator', 'Fluorescence microscope'],
            'western blot': ['Gel apparatus', 'Transfer system', 'Imaging system'],
            'flow cytometry': ['Flow cytometer', 'Cell sorter'],
            'crispr': ['Thermal cycler', 'Electroporator', 'Fluorescence microscope'],
            'rna extraction': ['Centrifuge', 'Vortex', 'Spectrophotometer']
        }
        
        equipment = []
        exp_type_lower = requirements.experiment_type.lower()
        
        for key, items in equipment_map.items():
            if key in exp_type_lower:
                equipment.extend(items)
        
        return list(set(equipment))
    
    def _infer_required_expertise(self, requirements: ProtocolRequirements) -> List[str]:
        """Infer required expertise from experiment type"""
        expertise_map = {
            'pcr': ['Molecular biology', 'Primer design'],
            'cell culture': ['Aseptic technique', 'Cell biology'],
            'transfection': ['Cell culture', 'Transfection optimization'],
            'western blot': ['Protein analysis', 'Antibody validation'],
            'flow cytometry': ['Flow cytometry analysis', 'Cell sorting'],
            'crispr': ['Gene editing', 'Guide RNA design', 'Genomic analysis'],
            'rna extraction': ['RNA handling', 'Quality assessment']
        }
        
        expertise = []
        exp_type_lower = requirements.experiment_type.lower()
        
        for key, items in expertise_map.items():
            if key in exp_type_lower:
                expertise.extend(items)
        
        return list(set(expertise))
    
    def _format_protocol_context(self, protocols: List[Dict]) -> str:
        """Format protocol context for LLM"""
        context = []
        for i, protocol in enumerate(protocols):
            context.append(f"Protocol {i+1}: {protocol.get('title', 'Unknown')}")
            context.append(f"Relevance: {protocol.get('relevance_score', 0):.2f}")
            context.append(f"Summary: {protocol.get('snippet', '')[:300]}...")
            context.append("")
        
        return "\n".join(context)
    
    def _format_lab_capabilities(self, lab_capabilities: Optional[LabCapabilities]) -> str:
        """Format lab capabilities for LLM"""
        if not lab_capabilities:
            return "Standard molecular biology lab assumed"
        
        return f"""
        Equipment: {', '.join(lab_capabilities.equipment[:10])}
        Reagents: {', '.join(lab_capabilities.reagents[:10])}
        Expertise: {', '.join(lab_capabilities.expertise)}
        Typical protocols: {', '.join(lab_capabilities.typical_protocols[:5])}
        """
    
    def _format_requirements_analysis(self, requirements: ProtocolRequirements) -> str:
        """Format requirements analysis"""
        return f"""
        Experiment Type: {requirements.experiment_type}
        Sample: {requirements.sample_type} (n={requirements.sample_size})
        Key Objectives: {', '.join(requirements.objectives[:3])}
        Timeline: {requirements.timeline}
        Budget: {requirements.budget}
        Safety: {requirements.safety_level}
        """
    
    def _explain_optimization(self, optimization: Optional[ProtocolOptimization]) -> str:
        """Explain optimization strategy"""
        if not optimization:
            return "No specific optimization applied - balanced approach used"
        
        explanations = {
            "time": "Protocol optimized for speed - parallel steps and minimal incubations where possible",
            "cost": "Protocol optimized for cost - generic reagents and minimal waste",
            "yield": "Protocol optimized for maximum yield - extended incubations and optimal conditions",
            "quality": "Protocol optimized for quality - additional purification and validation steps"
        }
        
        return explanations.get(optimization.optimize_for, "Custom optimization applied")
    
    def _parse_protocol_draft(self, protocol_text: str) -> Dict:
        """Parse protocol text into structured format"""
        protocol = {
            'title': '',
            'summary': '',
            'materials': [],
            'equipment': [],
            'safety': [],
            'procedure': [],
            'quality_control': [],
            'expected_results': '',
            'data_analysis': ''
        }
        
        # Simple parsing logic - can be enhanced with NLP
        lines = protocol_text.split('\n')
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if 'title:' in line_lower:
                protocol['title'] = line.split(':', 1)[1].strip()
            elif any(keyword in line_lower for keyword in ['summary:', 'overview:', 'abstract:']):
                current_section = 'summary'
            elif 'materials' in line_lower or 'reagents' in line_lower:
                current_section = 'materials'
            elif 'equipment' in line_lower:
                current_section = 'equipment'
            elif 'safety' in line_lower:
                current_section = 'safety'
            elif 'procedure' in line_lower or 'method' in line_lower:
                current_section = 'procedure'
            elif 'quality control' in line_lower or 'qc' in line_lower:
                current_section = 'quality_control'
            elif 'expected results' in line_lower:
                current_section = 'expected_results'
            elif 'data analysis' in line_lower:
                current_section = 'data_analysis'
            elif current_section and line.strip():
                if current_section in ['materials', 'equipment', 'safety', 'procedure', 'quality_control']:
                    if line.strip().startswith(('-', '•', '*', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                        if current_section == 'procedure':
                            protocol[current_section].append({
                                'number': len(protocol[current_section]) + 1,
                                'description': line.strip().lstrip('-•* 1234567890.')
                            })
                        else:
                            protocol[current_section].append({
                                'name': line.strip().lstrip('-•* 1234567890.')
                            })
                else:
                    protocol[current_section] += line + '\n'
        
        # Clean up text sections
        for key in ['summary', 'expected_results', 'data_analysis']:
            if key in protocol:
                protocol[key] = protocol[key].strip()
        
        return protocol
    
    def _optimize_for_time(self, protocol: Dict, optimization: ProtocolOptimization) -> Dict:
        """Optimize protocol for time efficiency"""
        optimized = protocol.copy()
        
        # Identify steps that can be parallelized
        procedure = optimized.get('procedure', [])
        
        # Add parallel processing notes
        for i, step in enumerate(procedure):
            if 'incubat' in step.get('description', '').lower():
                # Suggest parallel activities during incubation
                step['optimization_note'] = "During incubation, prepare next reagents"
            
            if 'overnight' in step.get('description', '').lower():
                # Suggest shorter alternatives
                step['alternative'] = "Consider 4-hour rapid protocol variant if available"
        
        return optimized
    
    def _optimize_for_cost(self, protocol: Dict, constraints: Dict) -> Dict:
        """Optimize protocol for cost efficiency"""
        optimized = protocol.copy()
        
        # Suggest generic alternatives for materials
        for material in optimized.get('materials', []):
            if 'kit' in material.get('name', '').lower():
                material['cost_saving_alternative'] = "Consider in-house buffer preparation"
        
        return optimized
    
    def _optimize_for_yield(self, protocol: Dict) -> Dict:
        """Optimize protocol for maximum yield"""
        optimized = protocol.copy()
        
        # Enhance critical yield-affecting steps
        for step in optimized.get('procedure', []):
            if any(keyword in step.get('description', '').lower() 
                   for keyword in ['elut', 'extract', 'harvest']):
                step['yield_optimization'] = "Use pre-warmed elution buffer and extended incubation"
        
        return optimized
    
    def _optimize_for_quality(self, protocol: Dict) -> Dict:
        """Optimize protocol for quality"""
        optimized = protocol.copy()
        
        # Add additional quality control steps
        qc_steps = optimized.get('quality_control', [])
        qc_steps.append({
            'name': 'Additional purity check using spectrophotometry'
        })
        qc_steps.append({
            'name': 'Replicate validation for consistency'
        })
        
        optimized['quality_control'] = qc_steps
        
        return optimized
    
    def _protect_critical_steps(self, protocol: Dict, critical_steps: List[str]) -> Dict:
        """Ensure critical steps are not compromised during optimization"""
        protected = protocol.copy()
        
        for step in protected.get('procedure', []):
            step_desc = step.get('description', '').lower()
            for critical in critical_steps:
                if critical.lower() in step_desc:
                    step['critical'] = True
                    step['note'] = "Critical step - do not modify without validation"
        
        return protected
    
    def _generate_safety_measures(self, safety_level: str, protocol: Dict) -> List[Dict]:
        """Generate safety measures based on BSL level"""
        measures = []
        
        base_measures = [
            {'measure': 'Wear appropriate PPE (lab coat, gloves, safety glasses)', 'level': 'all'},
            {'measure': 'Work in designated area', 'level': 'all'},
            {'measure': 'Proper waste disposal according to institutional guidelines', 'level': 'all'}
        ]
        
        measures.extend(base_measures)
        
        if safety_level == "BSL-2":
            measures.extend([
                {'measure': 'Work in biosafety cabinet for aerosol-generating procedures', 'level': 'BSL-2'},
                {'measure': 'Decontaminate work surfaces with appropriate disinfectant', 'level': 'BSL-2'}
            ])
        
        # Check for specific hazards in materials
        for material in protocol.get('materials', []):
            if 'trizol' in material.get('name', '').lower():
                measures.append({
                    'measure': 'Handle TRIzol in fume hood - contains phenol and guanidinium',
                    'specific_to': 'TRIzol'
                })
        
        return measures
    
    def _generate_qc_checkpoints(self, protocol: Dict) -> List[Dict]:
        """Generate quality control checkpoints"""
        checkpoints = []
        
        # Add QC for each major phase
        checkpoints.append({
            'phase': 'Pre-protocol',
            'checks': [
                'Verify all reagents are within expiration date',
                'Confirm equipment calibration is current',
                'Check sample quality/quantity'
            ]
        })
        
        # Add step-specific QC
        for i, step in enumerate(protocol.get('procedure', [])):
            if any(keyword in step.get('description', '').lower() 
                   for keyword in ['extract', 'purif', 'amplif']):
                checkpoints.append({
                    'phase': f'After step {i+1}',
                    'checks': [
                        'Verify expected yield/concentration',
                        'Check purity ratios if applicable',
                        'Visual inspection for anomalies'
                    ]
                })
        
        checkpoints.append({
            'phase': 'Post-protocol',
            'checks': [
                'Validate results against expected outcomes',
                'Document any deviations',
                'Store samples appropriately'
            ]
        })
        
        return checkpoints
    
    def _generate_validation_steps(self, protocol: Dict) -> List[str]:
        """Generate validation steps"""
        validation = [
            "Run positive and negative controls in parallel",
            "Perform technical replicates (minimum n=3)",
            "Validate key results with orthogonal method",
            "Document all observations and deviations"
        ]
        
        # Add protocol-specific validation
        if 'pcr' in protocol.get('title', '').lower():
            validation.append("Verify amplicon size by gel electrophoresis")
            validation.append("Sequence PCR products to confirm specificity")
        
        return validation
    
    def _identify_potential_issues(self, step: Dict) -> List[Dict]:
        """Identify potential issues for a protocol step"""
        issues = []
        step_desc = step.get('description', '').lower()
        
        # Temperature-sensitive steps
        if any(word in step_desc for word in ['ice', 'cold', 'frozen']):
            issues.append({
                'description': 'Temperature deviation',
                'symptoms': ['Degradation', 'Reduced activity'],
                'solutions': ['Maintain cold chain', 'Work quickly', 'Pre-chill equipment']
            })
        
        # Time-sensitive steps
        if any(word in step_desc for word in ['immediately', 'quickly', 'min', 'hour']):
            issues.append({
                'description': 'Timing deviation',
                'symptoms': ['Suboptimal results', 'Failed reaction'],
                'solutions': ['Set timers', 'Prepare in advance', 'Work in batches']
            })
        
        return issues
    
    def _generate_prevention_strategy(self, pitfall: str) -> str:
        """Generate prevention strategy for common pitfall"""
        strategies = {
            'contamination': 'Use filter tips, separate pre/post-PCR areas, regular decontamination',
            'degradation': 'Work on ice, minimize freeze-thaw cycles, aliquot samples',
            'low yield': 'Optimize input amount, verify reagent quality, extend incubation times',
            'high background': 'Optimize washing steps, titrate reagents, include proper controls'
        }
        
        for key, strategy in strategies.items():
            if key in pitfall.lower():
                return strategy
        
        return "Follow best practices and manufacturer recommendations"
    
    def _create_diagnostic_flowchart(self, protocol: Dict, issues: List[Dict]) -> List[Dict]:
        """Create diagnostic flowchart for troubleshooting"""
        flowchart = []
        
        # Group issues by symptoms
        symptom_map = {}
        for issue in issues:
            for symptom in issue.get('symptoms', []):
                if symptom not in symptom_map:
                    symptom_map[symptom] = []
                symptom_map[symptom].append(issue)
        
        # Create flowchart nodes
        for symptom, related_issues in symptom_map.items():
            node = {
                'symptom': symptom,
                'diagnostic_steps': [
                    f"Check step {issue['step']}" for issue in related_issues
                ],
                'likely_causes': [issue['issue'] for issue in related_issues],
                'solutions': []
            }
            
            # Aggregate solutions
            for issue in related_issues:
                node['solutions'].extend(issue.get('solutions', []))
            
            flowchart.append(node)
        
        return flowchart
    
    def _objective_to_criteria(self, objective: str) -> List[str]:
        """Convert objective to measurable criteria"""
        criteria = []
        objective_lower = objective.lower()
        
        if 'quantif' in objective_lower:
            criteria.append("Quantification within 10% CV across replicates")
            criteria.append("Linear dynamic range covers expected values")
        
        if 'detect' in objective_lower:
            criteria.append("Signal-to-noise ratio > 3")
            criteria.append("Specificity confirmed by controls")
        
        if 'purif' in objective_lower:
            criteria.append("Purity > 90% by appropriate method")
            criteria.append("Yield within expected range")
        
        return criteria
    
    def _extract_metrics(self, protocol: Dict) -> List[Dict]:
        """Extract quantitative metrics from protocol"""
        metrics = []
        
        # Look for numeric values in expected results
        expected_results = protocol.get('expected_results', '')
        
        # Simple pattern matching for metrics
        import re
        
        # Find percentages
        percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', expected_results)
        for pct in percentages:
            metrics.append({
                'metric': 'Percentage',
                'value': float(pct),
                'unit': '%'
            })
        
        # Find concentrations
        concentrations = re.findall(r'(\d+(?:\.\d+)?)\s*(ng|μg|mg|μM|mM|M)', expected_results)
        for conc, unit in concentrations:
            metrics.append({
                'metric': 'Concentration',
                'value': float(conc),
                'unit': unit
            })
        
        return metrics
    
    def _create_validation_decision_tree(self, criteria: List[str]) -> Dict:
        """Create decision tree for validation"""
        tree = {
            'root': 'All criteria met?',
            'yes': 'Protocol successful - proceed to data analysis',
            'no': {
                'question': 'Which criteria failed?',
                'branches': {}
            }
        }
        
        for criterion in criteria[:3]:  # Limit to avoid too complex tree
            tree['no']['branches'][criterion] = {
                'action': f"Troubleshoot: {criterion}",
                'next': 'Repeat affected steps'
            }
        
        return tree
    
    def _identify_key_differences(self, primary_protocol: Dict, strategy: str) -> List[str]:
        """Identify key differences for alternative protocol"""
        differences = []
        
        if strategy == "time":
            differences = [
                "Shorter incubation times",
                "Parallel processing steps",
                "Rapid kit alternatives"
            ]
        elif strategy == "cost":
            differences = [
                "In-house buffer preparation",
                "Bulk reagent purchasing",
                "Reduced reaction volumes"
            ]
        elif strategy == "yield":
            differences = [
                "Extended incubation times",
                "Optimized elution conditions",
                "Multiple extraction rounds"
            ]
        elif strategy == "simplicity":
            differences = [
                "Fewer steps overall",
                "All-in-one kit usage",
                "Minimal equipment requirements"
            ]
        
        return differences
    
    def _identify_trade_offs(self, strategy: str) -> List[str]:
        """Identify trade-offs for optimization strategy"""
        trade_offs = {
            "time": ["May sacrifice yield", "Higher reagent costs", "Less optimization flexibility"],
            "cost": ["Longer preparation time", "Potentially lower consistency", "More hands-on work"],
            "yield": ["Increased time requirement", "Higher reagent usage", "More complex procedure"],
            "simplicity": ["Less optimization possible", "Potentially higher cost", "May not suit all samples"]
        }
        
        return trade_offs.get(strategy, [])
    
    def _when_to_use_alternative(self, strategy: str) -> str:
        """Describe when to use alternative protocol"""
        recommendations = {
            "time": "Use when results are needed urgently or for high-throughput applications",
            "cost": "Use for routine applications with large sample numbers or limited budget",
            "yield": "Use when sample is precious or downstream applications require high input",
            "simplicity": "Use for new users, teaching labs, or when consistency is more important than optimization"
        }
        
        return recommendations.get(strategy, "Evaluate based on specific project needs")
    
    def _estimate_material_cost(self, material: Dict) -> float:
        """Estimate cost for a material"""
        # Simple estimation based on common reagents
        material_name = material.get('name', '').lower()
        
        cost_map = {
            'trizol': 150,
            'kit': 300,
            'enzyme': 200,
            'antibod': 400,
            'primer': 50,
            'buffer': 30,
            'tip': 20,
            'tube': 15,
            'plate': 25
        }
        
        for key, cost in cost_map.items():
            if key in material_name:
                return cost
        
        return 50  # Default cost
    
    def _calculate_total_time(self, protocol: Dict) -> float:
        """Calculate total time in hours"""
        total_hours = 0
        
        for step in protocol.get('procedure', []):
            time_hours = self._parse_step_time(step.get('description', ''))
            total_hours += time_hours
        
        return total_hours
    
    def _parse_step_time(self, description: str) -> float:
        """Parse time from step description"""
        import re
        
        description_lower = description.lower()
        
        # Look for time patterns
        hours = re.findall(r'(\d+(?:\.\d+)?)\s*h(?:ou)?r', description_lower)
        minutes = re.findall(r'(\d+)\s*min', description_lower)
        overnight = 'overnight' in description_lower
        
        total_hours = 0
        
        if hours:
            total_hours += sum(float(h) for h in hours)
        if minutes:
            total_hours += sum(float(m) / 60 for m in minutes)
        if overnight:
            total_hours += 16  # Assume overnight = 16 hours
        
        # Default to 0.5 hours if no time specified
        return total_hours if total_hours > 0 else 0.5


# Singleton instance
_enhanced_protocol_service = None

def get_enhanced_protocol_service() -> EnhancedProtocolService:
    """Get singleton instance of enhanced protocol service"""
    global _enhanced_protocol_service
    if _enhanced_protocol_service is None:
        _enhanced_protocol_service = EnhancedProtocolService()
    return _enhanced_protocol_service