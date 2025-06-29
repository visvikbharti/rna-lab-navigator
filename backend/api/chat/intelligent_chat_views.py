"""
Intelligent Chat Views - Immediate Enhancement
This can be deployed TODAY to make the chat more intelligent
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .views import ChatSessionViewSet
from openai import OpenAI
from django.conf import settings

# This prompt transforms the AI into a research partner
INTELLIGENT_RESEARCH_PROMPT = """You are a senior RNA biologist acting as a research partner. You have extensive knowledge of RNA biology, CRISPR systems, and experimental design.

For EVERY response, follow this structure:

1. **Direct Answer**: Answer the user's question using the provided context
2. **Research Intelligence**: Then add:
   - 🧪 **Experiment Suggestion**: What experiment would test/extend this?
   - 🤔 **Critical Questions**: What should they consider that they might not have thought of?
   - ⚡ **Quick Win**: A simple pilot experiment they could do today/this week
   - ⚠️ **Watch Out**: Common pitfalls or contradictions in the literature
   - 💡 **Novel Idea**: Can you combine insights from different papers for a new approach?

Always be specific with concentrations, times, temperatures. Reference the source papers. Think like you're mentoring a graduate student.

Example format:
---
**Direct Answer**: [Answer using the context provided]

**Research Intelligence**:

🧪 **Experiment Suggestion**: Based on the findings in [Paper], you could test...

🤔 **Critical Questions**: 
- Have you considered...?
- What if the effect is cell-type specific?

⚡ **Quick Win**: Tomorrow, try a quick experiment: [specific pilot]

⚠️ **Watch Out**: Papers disagree on [X]. Paper A says... but Paper B found...

💡 **Novel Idea**: Combining the approach from [Paper 1] with the insight from [Paper 2], you could...
---

Remember: You're not just answering questions, you're actively helping design the next experiment."""

class IntelligentChatViewSet(ChatSessionViewSet):
    """
    Enhanced chat that provides research intelligence
    """
    
    def create_message(self, request, session_id):
        """Override the parent method to add intelligence"""
        
        # Get the standard response first
        response = super().create_message(request, session_id)
        
        # If intelligent mode is enabled, enhance the response
        if request.data.get('intelligent_mode', True):
            try:
                # Get the original response data
                original_answer = response.data.get('response', {}).get('content', '')
                sources = response.data.get('response', {}).get('metadata', {}).get('sources', [])
                
                # Enhance with intelligence
                enhanced_answer = self._add_research_intelligence(
                    query=request.data.get('content', ''),
                    original_answer=original_answer,
                    sources=sources
                )
                
                # Update the response
                response.data['response']['content'] = enhanced_answer
                response.data['response']['metadata']['intelligent_mode'] = True
                
            except Exception as e:
                # If enhancement fails, return original response
                print(f"Intelligence enhancement failed: {e}")
        
        return response
    
    def _add_research_intelligence(self, query, original_answer, sources):
        """Add research intelligence to the answer"""
        
        # Prepare context
        context = f"User Question: {query}\n\nContext from lab database:\n{original_answer}\n\n"
        if sources:
            context += "Sources:\n"
            for source in sources[:3]:
                context += f"- {source.get('title', 'Unknown')} by {source.get('author', 'Unknown')}\n"
        
        # Get intelligent enhancement
        try:
            messages = [
                {"role": "system", "content": INTELLIGENT_RESEARCH_PROMPT},
                {"role": "user", "content": context}
            ]
            
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            # Fallback: Add simple suggestions if API fails
            return original_answer + self._add_simple_suggestions(query, original_answer)
    
    def _add_simple_suggestions(self, query, answer):
        """Add basic suggestions without API call"""
        
        suggestions = "\n\n**Research Intelligence**:\n\n"
        
        # Simple keyword-based suggestions
        if any(word in query.lower() for word in ['nhej', 'hdr', 'repair']):
            suggestions += "🧪 **Experiment Suggestion**: Compare repair efficiency with and without SCR7 inhibitor\n"
            suggestions += "⚡ **Quick Win**: Run a T7E1 assay to quickly assess indel frequency\n"
        
        if 'protocol' in query.lower():
            suggestions += "🧪 **Experiment Suggestion**: Run controls with your current vs optimized protocol\n"
            suggestions += "⚠️ **Watch Out**: Always verify pH and osmolarity when changing buffers\n"
        
        if 'crispr' in query.lower():
            suggestions += "💡 **Novel Idea**: Consider using your lab's FnCas9 variant for higher specificity\n"
            suggestions += "🤔 **Critical Question**: Have you verified your gRNA doesn't have off-targets?\n"
        
        return suggestions


# Quick endpoint to test intelligence
@api_view(['POST'])
def test_intelligence(request):
    """Test the intelligent response system"""
    
    test_query = request.data.get('query', 'How can I improve CRISPR efficiency?')
    
    # Simulate a basic answer
    basic_answer = """
    CRISPR efficiency can be improved through several methods:
    1. Optimize sgRNA design for high on-target activity
    2. Use modified Cas9 variants with enhanced specificity
    3. Optimize delivery methods and timing
    4. Consider using HDR enhancers like SCR7
    """
    
    # Add intelligence
    intelligent = IntelligentChatViewSet()._add_research_intelligence(
        query=test_query,
        original_answer=basic_answer,
        sources=[
            {"title": "Optimizing CRISPR-Cas9 for high efficiency", "author": "Smith et al"},
            {"title": "Rhythm Phutela PhD Thesis", "author": "Rhythm Phutela"}
        ]
    )
    
    return Response({
        'query': test_query,
        'basic_answer': basic_answer,
        'intelligent_answer': intelligent,
        'mode': 'research_partner'
    })


# Hypothesis generator for chat
@api_view(['POST']) 
def chat_hypothesis_generator(request):
    """Generate hypotheses based on chat context"""
    
    session_id = request.data.get('session_id')
    research_area = request.data.get('area', '')
    
    # Get chat history for context
    # [Implementation would fetch actual chat history]
    
    prompt = f"""Based on our discussion about {research_area}, generate 3 novel hypotheses:

    For each hypothesis:
    1. State the hypothesis clearly
    2. Explain why it's novel
    3. Suggest a key experiment
    4. Predict the impact
    
    Be creative but grounded in the science we've discussed."""
    
    # Generate hypotheses
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a creative scientist who generates novel but testable hypotheses."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=800
        )
        
        return Response({
            'hypotheses': response.choices[0].message.content,
            'session_id': session_id,
            'area': research_area
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)