"""
Utility functions for automated evaluation of the RAG system.
"""

import time
import numpy as np
from django.conf import settings
from django.db import transaction
from django.db.models import Avg, Count
from django.utils import timezone
from openai import OpenAI

from ..models import (
    EvaluationSet,
    ReferenceQuestion,
    EvaluationRun,
    QuestionResult
)
from ..ingestion.embeddings_utils import search_weaviate

# Import moved inside functions to avoid circular import
# from ..views import QueryView


def calculate_source_overlap(sources, expected_sources):
    """
    Calculate the overlap between retrieved sources and expected sources.
    
    Args:
        sources (list): Sources returned by the system
        expected_sources (list): Expected sources for the query
        
    Returns:
        float: Precision score between 0-1
    """
    if not expected_sources:
        return 1.0  # No expected sources to match against
    
    if not sources:
        return 0.0  # No sources retrieved
    
    # Extract source titles for comparison
    source_titles = {source.get('title', '').lower() for source in sources}
    expected_titles = {source.get('title', '').lower() for source in expected_sources}
    
    # Calculate overlap
    matches = source_titles.intersection(expected_titles)
    precision = len(matches) / len(source_titles) if source_titles else 0
    recall = len(matches) / len(expected_titles) if expected_titles else 0
    
    # F1 score (harmonic mean of precision and recall)
    if precision + recall == 0:
        return 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1


def evaluate_answer_relevance(answer, expected_answer):
    """
    Use GPT to evaluate the relevance of the generated answer 
    compared to the expected answer.
    
    Args:
        answer (str): Generated answer
        expected_answer (str): Expected reference answer
        
    Returns:
        float: Relevance score between 0-1
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Prompt for evaluating answer relevance
    prompt = f"""
You are an objective evaluator for question answering systems. 
Compare the following generated answer against the expected reference answer.
Rate the generated answer on a scale from 0.0 to 1.0, where:
- 1.0: Perfect match, covers all key points with accurate information
- 0.8: Very good, covers most key points, minor missing details
- 0.6: Good, covers core information but missing some important details
- 0.4: Partial, covers some information but missing major points
- 0.2: Poor, minimal overlap with expected answer
- 0.0: Completely incorrect or unrelated to expected answer

Return ONLY the numeric score, nothing else.

Generated Answer:
{answer}

Expected Reference Answer:
{expected_answer}
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use smaller, cheaper model for evaluation
            messages=[
                {"role": "system", "content": "You are an objective evaluator that returns only a numeric score."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=5,
        )
        
        # Extract and convert score
        score_text = response.choices[0].message.content.strip()
        score = float(score_text)
        
        # Ensure score is within bounds
        score = max(0.0, min(1.0, score))
        return score
    
    except Exception as e:
        print(f"Error evaluating answer relevance: {e}")
        # Default to middle score in case of error
        return 0.5


def run_evaluation(evaluation_set_id, use_hybrid=True, use_cache=False):
    """
    Run an evaluation against a set of reference questions.
    
    Args:
        evaluation_set_id (int): ID of the evaluation set to run
        use_hybrid (bool): Whether to use hybrid search
        use_cache (bool): Whether to use response caching
        
    Returns:
        EvaluationRun: The completed evaluation run
    """
    # Get the evaluation set
    try:
        evaluation_set = EvaluationSet.objects.get(id=evaluation_set_id)
    except EvaluationSet.DoesNotExist:
        raise ValueError(f"Evaluation set with ID {evaluation_set_id} not found")
    
    # Get all questions in the set
    questions = ReferenceQuestion.objects.filter(evaluation_set=evaluation_set)
    
    if not questions.exists():
        raise ValueError(f"No questions found in evaluation set {evaluation_set.name}")
    
    # Create a new evaluation run
    with transaction.atomic():
        evaluation_run = EvaluationRun.objects.create(
            evaluation_set=evaluation_set,
            status='running',
            total_questions=questions.count()
        )
    
    # Import QueryView here to avoid circular import
    from ..views import QueryView
    
    # Create query view instance for processing
    query_view = QueryView()
    
    # Initialize metrics
    start_time = time.time()
    success_count = 0
    failure_count = 0
    
    # Process each question
    for question in questions:
        try:
            # Time the execution of this question
            question_start_time = time.time()
            
            # Search for relevant documents
            results = search_weaviate(
                question.question_text,
                doc_type=question.doc_type,
                limit=10,
                use_hybrid=use_hybrid
            )
            
            # Rerank results
            reranked_results = query_view.rerank_results(question.question_text, results)
            
            # Build prompt
            prompt = query_view.build_prompt(question.question_text, reranked_results)
            
            # Extract sources
            sources = query_view.extract_sources(reranked_results)
            
            # Select model based on question complexity and type
            selected_model = query_view.select_model(question.question_text, reranked_results)
            
            # Get answer from OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for RNA biology lab. Provide accurate, cited answers based only on the provided sources."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000,
                top_p=1.0
            )
            
            answer = response.choices[0].message.content
            
            # Calculate confidence score
            confidence_score = query_view.calculate_confidence_score(answer, reranked_results)
            
            # Calculate metrics
            retrieval_precision = calculate_source_overlap(sources, question.expected_sources)
            answer_relevance = evaluate_answer_relevance(answer, question.expected_answer)
            
            # Record execution time
            question_exec_time = time.time() - question_start_time
            
            # Create result
            QuestionResult.objects.create(
                evaluation_run=evaluation_run,
                reference_question=question,
                answer=answer,
                sources=sources,
                confidence_score=confidence_score,
                retrieval_precision=retrieval_precision,
                answer_relevance=answer_relevance,
                execution_time=question_exec_time,
                model_used=selected_model
            )
            
            # Update counters
            if confidence_score >= 0.45 and answer_relevance >= 0.6:
                success_count += 1
            else:
                failure_count += 1
            
        except Exception as e:
            print(f"Error processing question '{question.question_text[:50]}...': {e}")
            failure_count += 1
    
    # Calculate total execution time
    total_time = time.time() - start_time
    
    # Update evaluation run with results
    with transaction.atomic():
        # Calculate averages
        results = QuestionResult.objects.filter(evaluation_run=evaluation_run)
        avg_confidence = results.aggregate(Avg('confidence_score'))
        avg_precision = results.aggregate(Avg('retrieval_precision'))
        avg_relevance = results.aggregate(Avg('answer_relevance'))
        
        # Update run status
        evaluation_run.status = 'completed'
        evaluation_run.average_score = avg_confidence.get('confidence_score__avg', 0)
        evaluation_run.average_retrieval_precision = avg_precision.get('retrieval_precision__avg', 0)
        evaluation_run.average_answer_relevance = avg_relevance.get('answer_relevance__avg', 0)
        evaluation_run.success_count = success_count
        evaluation_run.failure_count = failure_count
        evaluation_run.execution_time = total_time
        evaluation_run.save()
    
    return evaluation_run


def compare_runs(current_run_id, previous_run_id=None):
    """
    Compare the current evaluation run with a previous run to detect regressions.
    
    Args:
        current_run_id (int): ID of the current evaluation run
        previous_run_id (int): ID of a previous run to compare against
            If None, automatically finds the most recent completed run.
        
    Returns:
        dict: Comparison results with metrics and change percentages
    """
    try:
        current_run = EvaluationRun.objects.get(id=current_run_id)
    except EvaluationRun.DoesNotExist:
        raise ValueError(f"Evaluation run with ID {current_run_id} not found")
    
    # Find a previous run if not specified
    if previous_run_id is None:
        previous_runs = EvaluationRun.objects.filter(
            evaluation_set=current_run.evaluation_set,
            status='completed',
            run_date__lt=current_run.run_date
        ).order_by('-run_date')
        
        if previous_runs.exists():
            previous_run = previous_runs.first()
        else:
            # No previous run found
            return {
                "current_run": {
                    "id": current_run.id,
                    "date": current_run.run_date,
                    "avg_score": current_run.average_score,
                    "avg_precision": current_run.average_retrieval_precision,
                    "avg_relevance": current_run.average_answer_relevance,
                    "success_rate": current_run.success_count / current_run.total_questions if current_run.total_questions > 0 else 0
                },
                "previous_run": None,
                "changes": None,
                "regression_detected": False
            }
    else:
        try:
            previous_run = EvaluationRun.objects.get(id=previous_run_id)
        except EvaluationRun.DoesNotExist:
            raise ValueError(f"Previous evaluation run with ID {previous_run_id} not found")
    
    # Calculate metrics
    current_success_rate = current_run.success_count / current_run.total_questions if current_run.total_questions > 0 else 0
    previous_success_rate = previous_run.success_count / previous_run.total_questions if previous_run.total_questions > 0 else 0
    
    # Calculate changes
    score_change = (current_run.average_score - previous_run.average_score) / previous_run.average_score if previous_run.average_score else 0
    precision_change = (current_run.average_retrieval_precision - previous_run.average_retrieval_precision) / previous_run.average_retrieval_precision if previous_run.average_retrieval_precision else 0
    relevance_change = (current_run.average_answer_relevance - previous_run.average_answer_relevance) / previous_run.average_answer_relevance if previous_run.average_answer_relevance else 0
    success_rate_change = (current_success_rate - previous_success_rate) / previous_success_rate if previous_success_rate else 0
    
    # Detect regression (defined as 10% drop in any metric)
    regression_threshold = -0.1  # -10%
    regression_detected = any([
        score_change < regression_threshold,
        precision_change < regression_threshold,
        relevance_change < regression_threshold,
        success_rate_change < regression_threshold
    ])
    
    # Format results
    return {
        "current_run": {
            "id": current_run.id,
            "date": current_run.run_date,
            "avg_score": current_run.average_score,
            "avg_precision": current_run.average_retrieval_precision,
            "avg_relevance": current_run.average_answer_relevance,
            "success_rate": current_success_rate
        },
        "previous_run": {
            "id": previous_run.id,
            "date": previous_run.run_date,
            "avg_score": previous_run.average_score,
            "avg_precision": previous_run.average_retrieval_precision,
            "avg_relevance": previous_run.average_answer_relevance,
            "success_rate": previous_success_rate
        },
        "changes": {
            "score_change": score_change * 100,  # Convert to percentage
            "precision_change": precision_change * 100,
            "relevance_change": relevance_change * 100,
            "success_rate_change": success_rate_change * 100
        },
        "regression_detected": regression_detected
    }


def generate_evaluation_report(run_id):
    """
    Generate a detailed report for an evaluation run.
    
    Args:
        run_id (int): ID of the evaluation run
        
    Returns:
        dict: Detailed report data
    """
    try:
        run = EvaluationRun.objects.get(id=run_id)
    except EvaluationRun.DoesNotExist:
        raise ValueError(f"Evaluation run with ID {run_id} not found")
    
    # Get results
    results = QuestionResult.objects.filter(evaluation_run=run)
    
    # Group results by question type
    type_stats = {}
    questions = ReferenceQuestion.objects.filter(evaluation_set=run.evaluation_set)
    for q_type, _ in ReferenceQuestion.QUESTION_TYPES:
        type_results = results.filter(reference_question__question_type=q_type)
        if type_results.exists():
            type_stats[q_type] = {
                "count": type_results.count(),
                "avg_relevance": type_results.aggregate(Avg('answer_relevance')).get('answer_relevance__avg', 0),
                "avg_precision": type_results.aggregate(Avg('retrieval_precision')).get('retrieval_precision__avg', 0)
            }
    
    # Get best and worst performers
    best_results = results.order_by('-answer_relevance')[:3]
    worst_results = results.order_by('answer_relevance')[:3]
    
    # Construct report
    report = {
        "run_id": run.id,
        "set_name": run.evaluation_set.name,
        "run_date": run.run_date,
        "status": run.status,
        "summary": {
            "total_questions": run.total_questions,
            "success_count": run.success_count,
            "failure_count": run.failure_count,
            "success_rate": run.success_count / run.total_questions if run.total_questions > 0 else 0,
            "avg_score": run.average_score,
            "avg_precision": run.average_retrieval_precision,
            "avg_relevance": run.average_answer_relevance,
            "execution_time": run.execution_time
        },
        "by_question_type": type_stats,
        "best_performers": [
            {
                "question": r.reference_question.question_text,
                "relevance": r.answer_relevance,
                "precision": r.retrieval_precision,
                "model": r.model_used
            } for r in best_results
        ],
        "worst_performers": [
            {
                "question": r.reference_question.question_text,
                "relevance": r.answer_relevance,
                "precision": r.retrieval_precision,
                "model": r.model_used
            } for r in worst_results
        ]
    }
    
    return report