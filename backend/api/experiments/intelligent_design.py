"""
Intelligent Experiment Designer
Helps researchers design rigorous experiments based on their questions
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
import openai
from api.search.real_rag import search_documents

# Configure OpenAI
openai.api_key = settings.OPENAI_API_KEY

EXPERIMENT_DESIGN_PROMPT = """You are a senior experimental biologist with 20+ years of experience in RNA biology, CRISPR, and molecular techniques. Design practical, rigorous experiments that junior researchers can follow.

When designing experiments:
1. Be extremely specific with concentrations, times, temperatures
2. Include all necessary controls (positive, negative, vehicle)
3. Consider the lab's actual capabilities and resources
4. Provide troubleshooting guidance
5. Suggest pilot experiments before full-scale
6. Include statistical considerations

Structure your response with these sections:
## Hypothesis
- Clear, testable hypothesis based on the question

## Experimental Design
### Overview
- Brief summary of the approach

### Materials Needed
- Specific reagents with catalog numbers when possible
- Equipment required
- Estimated cost

### Detailed Protocol
1. Step-by-step instructions
2. Include exact conditions (37°C, 5% CO2, etc.)
3. Timing for each step

### Controls
- Positive control: [specific]
- Negative control: [specific]  
- Vehicle/mock control: [specific]

### Expected Results
- Primary outcome and how to measure
- Alternative outcomes and interpretations
- Quantification methods

### Statistical Analysis
- Sample size calculation (with justification)
- Statistical tests to use
- Multiple comparison corrections if needed

### Troubleshooting Guide
- Common problems and solutions
- When to abort and restart
- Quality control checkpoints

### Timeline and Milestones
- Day-by-day breakdown
- Go/no-go decision points
- Total time estimate

Be practical and consider real-world constraints!"""


@api_view(['POST'])
def design_experiment(request):
    """
    Takes a research question and designs a complete experiment
    """
    question = request.data.get('question', '')
    background = request.data.get('background', '')
    constraints = request.data.get('constraints', {})
    
    if not question:
        return Response({'error': 'Research question is required'}, status=400)
    
    # Search for relevant papers and protocols
    search_results = search_documents(question, top_k=5)
    
    # Build context from search results
    context = "Relevant information from lab documents:\n\n"
    for i, result in enumerate(search_results[:3]):
        context += f"Source {i+1}: {result['title']} by {result['author']}\n"
        context += f"Key info: {result['snippet'][:300]}...\n\n"
    
    # Create the design prompt
    design_request = f"""
Research Question: {question}

Background/Context: {background or "No additional background provided"}

Lab Constraints:
- Time available: {constraints.get('time', 'Flexible')}
- Budget limit: {constraints.get('budget', 'Standard lab budget')}
- Equipment: {constraints.get('equipment', 'Standard molecular biology lab')}
- Personnel: {constraints.get('personnel', '1 graduate student')}

{context}

Based on the research question, background, constraints, and available lab documents, design a complete experiment. Include specific protocols from the lab's documents when relevant.
"""
    
    try:
        response = openai.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": EXPERIMENT_DESIGN_PROMPT},
                {"role": "user", "content": design_request}
            ],
            temperature=0.6,
            max_tokens=2000
        )
        
        experimental_design = response.choices[0].message.content
        
        # Extract key information for quick reference
        summary = extract_experiment_summary(experimental_design)
        
        return Response({
            'question': question,
            'design': experimental_design,
            'summary': summary,
            'references': [
                {
                    'title': r['title'],
                    'author': r['author'],
                    'relevance': r['score']
                } for r in search_results[:3]
            ],
            'estimated_timeline': extract_timeline(experimental_design),
            'estimated_cost': extract_cost(experimental_design),
            'complexity_score': assess_complexity(experimental_design, constraints)
        })
        
    except Exception as e:
        return Response({
            'error': f"Could not generate experimental design: {str(e)}"
        }, status=500)


@api_view(['POST'])
def validate_protocol(request):
    """
    Validates an experimental protocol for completeness and rigor
    """
    protocol = request.data.get('protocol', '')
    experiment_type = request.data.get('type', 'general')
    
    if not protocol:
        return Response({'error': 'Protocol text is required'}, status=400)
    
    validation_prompt = f"""
Review this experimental protocol for completeness and rigor:

{protocol}

Evaluate the following aspects:
1. Are all necessary controls included?
2. Is the sample size adequate for statistical power?
3. Are all steps clearly defined with specific conditions?
4. Are there any missing reagents or equipment?
5. Is the timeline realistic?
6. Are there potential confounding variables not addressed?
7. Is the data analysis plan appropriate?

Provide:
- Overall score (1-10)
- List of missing elements
- Specific suggestions for improvement
- Risk assessment
"""
    
    try:
        response = openai.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a rigorous experimental reviewer. Identify any weaknesses or missing elements in protocols."},
                {"role": "user", "content": validation_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        validation_result = response.choices[0].message.content
        
        return Response({
            'protocol_summary': protocol[:200] + '...',
            'validation': validation_result,
            'checklist': generate_protocol_checklist(experiment_type)
        })
        
    except Exception as e:
        return Response({
            'error': f"Could not validate protocol: {str(e)}"
        }, status=500)


@api_view(['POST']) 
def suggest_pilot_experiment(request):
    """
    Suggests a quick pilot experiment to test feasibility
    """
    main_hypothesis = request.data.get('hypothesis', '')
    available_time = request.data.get('time', '1 week')
    
    if not main_hypothesis:
        return Response({'error': 'Hypothesis is required'}, status=400)
    
    pilot_prompt = f"""
Main hypothesis: {main_hypothesis}
Available time: {available_time}

Design a pilot experiment that:
1. Tests the key assumption of the hypothesis
2. Can be completed in {available_time}
3. Uses minimal resources
4. Provides go/no-go decision for full experiment
5. Identifies potential technical issues

Include:
- Simplified protocol (1-2 days)
- Minimum sample size (n=3)
- Key measurement
- Decision criteria
- Cost estimate (<$500)
"""
    
    try:
        response = openai.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert at designing quick pilot experiments that provide maximum information with minimum resources."},
                {"role": "user", "content": pilot_prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        pilot_design = response.choices[0].message.content
        
        return Response({
            'hypothesis': main_hypothesis,
            'pilot_experiment': pilot_design,
            'decision_tree': generate_decision_tree(pilot_design)
        })
        
    except Exception as e:
        return Response({
            'error': f"Could not generate pilot experiment: {str(e)}"
        }, status=500)


# Helper functions
def extract_experiment_summary(design_text):
    """Extract key points from experimental design"""
    summary = {
        'hypothesis': '',
        'approach': '',
        'key_techniques': [],
        'primary_outcome': ''
    }
    
    lines = design_text.split('\n')
    current_section = ''
    
    for line in lines:
        if 'hypothesis' in line.lower():
            current_section = 'hypothesis'
        elif 'approach' in line.lower() or 'overview' in line.lower():
            current_section = 'approach'
        elif 'primary outcome' in line.lower():
            current_section = 'outcome'
        elif current_section:
            if current_section == 'hypothesis' and line.strip() and not line.startswith('#'):
                summary['hypothesis'] = line.strip()
                current_section = ''
            elif current_section == 'approach' and line.strip() and not line.startswith('#'):
                summary['approach'] = line.strip()
                current_section = ''
    
    return summary


def extract_timeline(design_text):
    """Extract timeline information from design"""
    import re
    
    # Look for day/week/month mentions
    days = re.findall(r'(\d+)\s*days?', design_text.lower())
    weeks = re.findall(r'(\d+)\s*weeks?', design_text.lower())
    
    if weeks:
        total_days = sum(int(w) * 7 for w in weeks)
    elif days:
        total_days = sum(int(d) for d in days)
    else:
        total_days = 7  # Default estimate
    
    return f"Approximately {total_days} days"


def extract_cost(design_text):
    """Extract cost estimate from design"""
    import re
    
    # Look for dollar amounts
    costs = re.findall(r'\$(\d+)', design_text)
    
    if costs:
        total = sum(int(c) for c in costs)
        return f"${total} (estimated)"
    
    return "Cost estimate not provided"


def assess_complexity(design_text, constraints):
    """Assess experiment complexity based on techniques and constraints"""
    complexity_score = 5  # Base score
    
    # Increase for complex techniques
    complex_techniques = ['CRISPR', 'primary cells', 'in vivo', 'proteomics', 'RNA-seq']
    for technique in complex_techniques:
        if technique.lower() in design_text.lower():
            complexity_score += 1
    
    # Decrease if time is limited
    if constraints.get('time') == 'urgent':
        complexity_score += 2
    
    # Decrease if budget is limited
    if '$' in str(constraints.get('budget', '')):
        try:
            budget = int(constraints['budget'].replace('$', '').replace(',', ''))
            if budget < 1000:
                complexity_score += 2
        except:
            pass
    
    return min(complexity_score, 10)


def generate_protocol_checklist(experiment_type):
    """Generate a checklist for the experiment type"""
    base_checklist = [
        "Hypothesis clearly stated",
        "All reagents listed with catalog numbers",
        "Step-by-step protocol with times/temperatures",
        "Positive and negative controls included",
        "Sample size calculation provided",
        "Statistical analysis plan defined",
        "Data collection sheets prepared",
        "Safety considerations addressed"
    ]
    
    if experiment_type == 'CRISPR':
        base_checklist.extend([
            "gRNA sequences validated",
            "Off-target analysis completed",
            "Transfection efficiency controls",
            "Editing efficiency assay planned"
        ])
    elif experiment_type == 'cell_culture':
        base_checklist.extend([
            "Cell line authentication",
            "Mycoplasma testing",
            "Passage number recorded",
            "Media batch noted"
        ])
    
    return base_checklist


def generate_decision_tree(pilot_design):
    """Generate a simple decision tree for pilot outcomes"""
    return {
        'success_criteria': 'Effect size > 20% with p < 0.05',
        'if_success': 'Proceed with full experiment as designed',
        'if_partial': 'Optimize protocol and repeat pilot',
        'if_failure': 'Re-evaluate hypothesis or try alternative approach',
        'key_metrics': ['Primary outcome measurement', 'Technical success rate', 'Cost per sample']
    }