"""
Intelligent Research Partner Views
This demonstrates how to transform simple Q&A into active research assistance
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from openai import OpenAI
from .views import search_papers

RESEARCH_PARTNER_PROMPT = """
You are a senior RNA biologist helping a junior researcher. You have deep knowledge of:
- RNA biology and modifications
- CRISPR/Cas systems
- Molecular biology techniques
- Experimental design and statistics

When answering questions:
1. First provide the direct answer
2. Then think critically and suggest:
   - What experiment would test this?
   - What related questions should they explore?
   - Any contradictions in the literature?
   - Novel combinations of techniques from different papers?
   - Potential pitfalls and controls needed?

Be specific, actionable, and reference papers when possible.
Format your response with clear sections using markdown headers.
"""

@api_view(['POST'])
def intelligent_query(request):
    """
    Enhanced query endpoint that provides research intelligence
    """
    query = request.data.get('query', '')
    mode = request.data.get('mode', 'standard')  # standard or research_partner
    
    # First get standard search results
    search_response = search_papers(request)
    search_data = search_response.data
    
    if mode == 'standard' or not search_data.get('answer'):
        return search_response
    
    # Enhance with research intelligence
    try:
        # Prepare context from search results
        context = f"Query: {query}\n\nRelevant findings from lab database:\n"
        context += search_data['answer'] + "\n\nSources:\n"
        
        for source in search_data.get('sources', [])[:3]:
            context += f"- {source['title']} by {source['author']}\n"
        
        # Generate intelligent response
        messages = [
            {"role": "system", "content": RESEARCH_PARTNER_PROMPT},
            {"role": "user", "content": context + "\n\nNow provide research intelligence on this topic."}
        ]
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )
        
        intelligent_answer = response.choices[0].message.content
        
        # Combine standard and intelligent responses
        enhanced_response = {
            **search_data,
            'intelligent_analysis': intelligent_answer,
            'mode': 'research_partner',
            'suggestions': extract_suggestions(intelligent_answer)
        }
        
        return Response(enhanced_response)
        
    except Exception as e:
        # Fallback to standard response if enhancement fails
        search_data['error'] = f"Intelligence enhancement unavailable: {str(e)}"
        return Response(search_data)


@api_view(['POST'])
def design_experiment(request):
    """
    Takes a research question and designs a complete experiment
    """
    question = request.data.get('question', '')
    background = request.data.get('background', '')
    constraints = request.data.get('constraints', {})
    
    # Search relevant papers
    search_request = request
    search_request.data = {'query': question}
    search_response = search_papers(search_request)
    papers = search_response.data.get('sources', [])
    
    # Create experimental design prompt
    design_prompt = f"""
    Research Question: {question}
    
    Background: {background}
    
    Lab Constraints:
    - Time: {constraints.get('time', 'Not specified')}
    - Budget: {constraints.get('budget', 'Not specified')}
    - Equipment: {constraints.get('equipment', 'Standard molecular biology lab')}
    
    Relevant Literature:
    """
    
    for paper in papers[:5]:
        design_prompt += f"\n- {paper['title']} - Key finding: {paper.get('snippet', '')[:200]}"
    
    design_prompt += """
    
    Design a complete experiment including:
    
    ## Hypothesis
    State a clear, testable hypothesis
    
    ## Experimental Design
    1. Overall approach
    2. Specific methods (step by step)
    3. Sample size and replicates
    4. Timeline
    
    ## Controls
    List all necessary controls and why they're needed
    
    ## Expected Results
    - Primary outcome
    - Alternative outcomes
    - How to interpret each
    
    ## Statistical Analysis
    - Tests to use
    - Power analysis
    - Multiple testing corrections if needed
    
    ## Potential Issues
    - Technical challenges
    - Alternative approaches
    - Troubleshooting guide
    
    ## Resources Needed
    - Reagents (with catalog numbers if possible)
    - Equipment
    - Estimated cost
    - Time requirement
    
    Be specific and practical. Reference the provided papers where relevant.
    """
    
    try:
        messages = [
            {"role": "system", "content": "You are an expert experimental biologist with 20 years of experience in RNA biology and CRISPR. Design practical, rigorous experiments."},
            {"role": "user", "content": design_prompt}
        ]
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.6,
            max_tokens=2000
        )
        
        experimental_design = response.choices[0].message.content
        
        return Response({
            'question': question,
            'design': experimental_design,
            'references': papers,
            'estimated_feasibility': assess_feasibility(experimental_design, constraints)
        })
        
    except Exception as e:
        return Response({
            'error': f"Could not generate experimental design: {str(e)}"
        }, status=500)


@api_view(['POST'])
def optimize_protocol(request):
    """
    Takes an existing protocol and optimizes it based on literature
    """
    current_protocol = request.data.get('protocol', '')
    issues = request.data.get('issues', [])
    target_improvement = request.data.get('target', '')
    
    # Search for relevant optimizations
    optimization_query = f"protocol optimization {' '.join(issues)} {target_improvement}"
    search_request = request
    search_request.data = {'query': optimization_query}
    search_response = search_papers(search_request)
    relevant_papers = search_response.data.get('sources', [])
    
    optimization_prompt = f"""
    Current Protocol:
    {current_protocol}
    
    Reported Issues:
    {', '.join(issues)}
    
    Target Improvement:
    {target_improvement}
    
    Relevant Literature on Optimizations:
    """
    
    for paper in relevant_papers[:5]:
        optimization_prompt += f"\n- {paper['title']}: {paper.get('snippet', '')[:200]}"
    
    optimization_prompt += """
    
    Provide an optimized protocol with:
    
    ## Key Changes
    List each modification and why it should help
    
    ## Optimized Protocol
    Step-by-step improved protocol
    
    ## Expected Improvements
    - Quantify expected benefits
    - Timeline to see results
    
    ## Validation
    How to verify the optimization worked
    
    ## Risk Assessment
    - What could go wrong
    - Fallback options
    
    Be specific about concentrations, times, and temperatures.
    """
    
    try:
        messages = [
            {"role": "system", "content": "You are a protocol optimization expert. Provide practical, tested improvements based on literature evidence."},
            {"role": "user", "content": optimization_prompt}
        ]
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.6,
            max_tokens=1500
        )
        
        optimized_protocol = response.choices[0].message.content
        
        return Response({
            'original_protocol': current_protocol,
            'optimized_protocol': optimized_protocol,
            'changes_summary': extract_key_changes(optimized_protocol),
            'supporting_literature': relevant_papers
        })
        
    except Exception as e:
        return Response({
            'error': f"Could not optimize protocol: {str(e)}"
        }, status=500)


@api_view(['POST'])
def generate_hypotheses(request):
    """
    Analyzes a research area and generates novel hypotheses
    """
    research_area = request.data.get('area', '')
    current_knowledge = request.data.get('current_knowledge', '')
    
    # Search broad literature
    search_request = request
    search_request.data = {'query': research_area}
    search_response = search_papers(search_request)
    papers = search_response.data.get('sources', [])
    
    hypothesis_prompt = f"""
    Research Area: {research_area}
    
    Current Lab Knowledge:
    {current_knowledge}
    
    Literature Review:
    """
    
    for paper in papers[:10]:
        hypothesis_prompt += f"\n- {paper['title']}: {paper.get('snippet', '')[:150]}"
    
    hypothesis_prompt += """
    
    Generate 5 novel, testable hypotheses by:
    
    1. Identifying gaps in current knowledge
    2. Finding contradictions between papers
    3. Combining insights from different papers
    4. Extending findings to new contexts
    5. Proposing new mechanisms
    
    For each hypothesis provide:
    - The hypothesis statement
    - Why it's novel
    - How to test it (brief)
    - Potential impact if true
    - Risk level (low/medium/high)
    
    Rank by potential impact and feasibility.
    """
    
    try:
        messages = [
            {"role": "system", "content": "You are a visionary scientist who excels at identifying research opportunities. Generate creative but testable hypotheses grounded in existing knowledge."},
            {"role": "user", "content": hypothesis_prompt}
        ]
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.8,
            max_tokens=1500
        )
        
        hypotheses = response.choices[0].message.content
        
        return Response({
            'research_area': research_area,
            'hypotheses': hypotheses,
            'supporting_literature': papers,
            'next_steps': suggest_pilot_experiments(hypotheses)
        })
        
    except Exception as e:
        return Response({
            'error': f"Could not generate hypotheses: {str(e)}"
        }, status=500)


# Helper functions
def extract_suggestions(text):
    """Extract actionable suggestions from intelligent analysis"""
    suggestions = []
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        if any(marker in line.lower() for marker in ['suggest', 'try', 'consider', 'experiment']):
            suggestions.append(line.strip())
    
    return suggestions[:5]  # Top 5 suggestions


def assess_feasibility(design, constraints):
    """Assess if experimental design fits within constraints"""
    # Simple heuristic - in production, this would be more sophisticated
    feasibility_score = 100
    
    if 'week' in design.lower() and constraints.get('time') == 'urgent':
        feasibility_score -= 30
    
    if '$' in design:
        # Extract rough cost estimate
        import re
        costs = re.findall(r'\$(\d+)', design)
        if costs:
            total_cost = sum(int(c) for c in costs)
            budget = constraints.get('budget', '1000').replace('$', '')
            if total_cost > int(budget):
                feasibility_score -= 40
    
    return min(max(feasibility_score, 0), 100)


def extract_key_changes(protocol):
    """Extract key changes from optimized protocol"""
    changes = []
    lines = protocol.split('\n')
    
    in_changes_section = False
    for line in lines:
        if 'key changes' in line.lower():
            in_changes_section = True
            continue
        elif line.startswith('#') and in_changes_section:
            break
        elif in_changes_section and line.strip():
            changes.append(line.strip())
    
    return changes[:5]


def suggest_pilot_experiments(hypotheses):
    """Suggest quick pilot experiments to test hypotheses"""
    # In production, this would analyze the hypotheses and suggest specific pilots
    return [
        "Run preliminary Western blot to check protein expression (1 day, $50)",
        "Quick qPCR screen of top 5 targets (2 days, $200)",
        "Cell viability assay under test conditions (1 day, $100)"
    ]