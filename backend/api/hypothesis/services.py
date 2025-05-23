"""
Hypothesis Mode Services
Handles advanced reasoning and protocol generation
"""

import json
import logging
from typing import Dict, List, Optional
from django.conf import settings
from openai import OpenAI

from api.models import Document, QueryHistory
from api.search.services import SearchService
from api.search.real_rag import search_documents
from .prompts import (
    HYPOTHESIS_SYSTEM_PROMPT,
    PROTOCOL_GENERATION_PROMPT,
    create_hypothesis_prompt,
    create_protocol_prompt
)

logger = logging.getLogger(__name__)

class HypothesisService:
    """Service for handling hypothesis exploration and advanced reasoning"""
    
    def __init__(self):
        try:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except TypeError as e:
            # Fallback for version compatibility issues
            logger.warning(f"OpenAI client initialization error: {e}")
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            self.client = None  # Will use module-level API
        self.search_service = SearchService()
        
    def explore_hypothesis(
        self,
        question: str,
        user_id: Optional[int] = None,
        use_advanced_model: bool = False
    ) -> Dict:
        """
        Explore a research hypothesis using advanced AI reasoning
        
        Args:
            question: The hypothesis or "what if" question
            user_id: Optional user ID for tracking
            use_advanced_model: Whether to use o3 model (future implementation)
            
        Returns:
            Dict containing analysis, confidence scores, and recommendations
        """
        try:
            # First, search for relevant context
            search_results = search_documents(
                query=question,
                doc_type='all',
                top_k=5
            )
            
            # Extract context from search results
            context_chunks = []
            for result in search_results[:3]:
                context_chunks.append(f"[{result.get('title', 'Unknown')}]: {result.get('snippet', '')}")
            
            context = "\n\n".join(context_chunks)
            
            # Create the hypothesis prompt
            user_prompt = create_hypothesis_prompt(question, context)
            
            # Select model based on subscription tier
            model = "gpt-4o" if not use_advanced_model else "gpt-4o"  # o3 placeholder
            
            # Call OpenAI API
            if self.client:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": HYPOTHESIS_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                answer = response.choices[0].message.content
            else:
                # Fallback to module-level API
                import openai
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": HYPOTHESIS_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                answer = response['choices'][0]['message']['content']
            
            # Parse structured response
            analysis = self._parse_hypothesis_response(answer)
            
            # Calculate confidence scores
            confidence_scores = self._calculate_confidence_scores(analysis, len(context_chunks))
            
            # Save to query history
            if user_id:
                QueryHistory.objects.create(
                    user_id=user_id,
                    query=question,
                    query_type='hypothesis',
                    response=json.dumps(analysis),
                    doc_type='hypothesis',
                    confidence_score=confidence_scores['overall']
                )
            
            return {
                'success': True,
                'question': question,
                'analysis': analysis,
                'confidence_scores': confidence_scores,
                'source_documents': search_results[:3],
                'model_used': model
            }
            
        except Exception as e:
            logger.error(f"Error in hypothesis exploration: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_protocol(
        self,
        requirements: str,
        base_protocol_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Generate a custom protocol based on requirements
        
        Args:
            requirements: Description of protocol requirements
            base_protocol_id: Optional ID of existing protocol to modify
            user_id: Optional user ID for tracking
            
        Returns:
            Dict containing generated protocol
        """
        try:
            context = ""
            
            # If base protocol provided, fetch it
            if base_protocol_id:
                try:
                    base_doc = Document.objects.get(id=base_protocol_id, doc_type='protocol')
                    context = f"Base Protocol: {base_doc.title}\n{base_doc.content[:2000]}"
                except Document.DoesNotExist:
                    logger.warning(f"Base protocol {base_protocol_id} not found")
            
            # Search for similar protocols
            search_results = search_documents(
                query=f"protocol {requirements}",
                doc_type='protocol',
                top_k=3
            )
            
            # Add similar protocols to context
            for result in search_results[:2]:
                context += f"\n\nSimilar Protocol: {result.get('title', '')}\n{result.get('snippet', '')[:1000]}"
            
            # Create protocol generation prompt
            prompt = create_protocol_prompt(requirements, context)
            
            # Generate protocol
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": PROTOCOL_GENERATION_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent protocols
                max_tokens=3000
            )
            
            protocol_content = response.choices[0].message.content
            
            # Parse and structure the protocol
            structured_protocol = self._parse_protocol_response(protocol_content)
            
            # Save to query history
            if user_id:
                QueryHistory.objects.create(
                    user_id=user_id,
                    query=requirements,
                    query_type='protocol_generation',
                    response=json.dumps(structured_protocol),
                    doc_type='protocol'
                )
            
            return {
                'success': True,
                'requirements': requirements,
                'protocol': structured_protocol,
                'reference_protocols': search_results[:2]
            }
            
        except Exception as e:
            logger.error(f"Error in protocol generation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_hypothesis_response(self, response: str) -> Dict:
        """Parse the AI response into structured components"""
        sections = {
            'hypothesis_analysis': '',
            'scientific_basis': '',
            'feasibility_assessment': '',
            'recommended_experiments': '',
            'potential_challenges': '',
            'related_directions': ''
        }
        
        current_section = None
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if 'hypothesis analysis' in line_lower:
                current_section = 'hypothesis_analysis'
            elif 'scientific basis' in line_lower:
                current_section = 'scientific_basis'
            elif 'feasibility' in line_lower:
                current_section = 'feasibility_assessment'
            elif 'experiment' in line_lower:
                current_section = 'recommended_experiments'
            elif 'challenge' in line_lower:
                current_section = 'potential_challenges'
            elif 'related' in line_lower and 'direction' in line_lower:
                current_section = 'related_directions'
            elif current_section and line.strip():
                sections[current_section] += line + '\n'
        
        # Clean up sections
        for key in sections:
            sections[key] = sections[key].strip()
        
        return sections
    
    def _parse_protocol_response(self, response: str) -> Dict:
        """Parse protocol response into structured format"""
        protocol = {
            'title': '',
            'safety_warnings': [],
            'materials': [],
            'equipment': [],
            'steps': [],
            'quality_control': [],
            'troubleshooting': [],
            'notes': ''
        }
        
        # Simple parsing logic - can be enhanced
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line_stripped = line.strip()
            line_lower = line.lower()
            
            if not line_stripped:
                continue
                
            if 'safety' in line_lower or 'warning' in line_lower:
                current_section = 'safety_warnings'
            elif 'material' in line_lower:
                current_section = 'materials'
            elif 'equipment' in line_lower:
                current_section = 'equipment'
            elif 'step' in line_lower or 'procedure' in line_lower:
                current_section = 'steps'
            elif 'quality' in line_lower or 'control' in line_lower:
                current_section = 'quality_control'
            elif 'troubleshoot' in line_lower:
                current_section = 'troubleshooting'
            elif current_section:
                if current_section in ['safety_warnings', 'materials', 'equipment', 'steps', 'quality_control', 'troubleshooting']:
                    if line_stripped.startswith(('-', '•', '*', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                        protocol[current_section].append(line_stripped.lstrip('-•* 1234567890.'))
                else:
                    protocol[current_section] += line + '\n'
        
        # Extract title from first line if not found
        if not protocol['title'] and lines:
            protocol['title'] = lines[0].strip()
        
        return protocol
    
    def _calculate_confidence_scores(self, analysis: Dict, context_count: int) -> Dict:
        """Calculate confidence scores for different aspects of the analysis"""
        scores = {
            'scientific_grounding': 0.0,
            'feasibility': 0.0,
            'experimental_clarity': 0.0,
            'overall': 0.0
        }
        
        # Simple heuristic scoring - can be enhanced with ML
        if analysis.get('scientific_basis'):
            scores['scientific_grounding'] = min(0.6 + (context_count * 0.1), 0.95)
        
        if analysis.get('feasibility_assessment'):
            # Check for positive/negative indicators
            feasibility_text = analysis['feasibility_assessment'].lower()
            if 'feasible' in feasibility_text or 'possible' in feasibility_text:
                scores['feasibility'] = 0.7
            if 'challenging' in feasibility_text or 'difficult' in feasibility_text:
                scores['feasibility'] -= 0.2
        
        if analysis.get('recommended_experiments'):
            # Score based on detail level
            exp_length = len(analysis['recommended_experiments'])
            scores['experimental_clarity'] = min(0.5 + (exp_length / 1000), 0.9)
        
        # Calculate overall score
        scores['overall'] = sum(scores.values()) / (len(scores) - 1)
        
        return scores