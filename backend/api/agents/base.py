"""
Base classes for the multi-agent system
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import openai
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all research agents."""
    
    def __init__(self, name: str, role: str, temperature: float = 0.7):
        self.name = name
        self.role = role
        self.temperature = temperature
        self.context = {}
        openai.api_key = settings.OPENAI_API_KEY
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return results."""
        pass
    
    def think(self, prompt: str, context: str = "") -> str:
        """Use LLM to think about a problem."""
        messages = [
            {"role": "system", "content": f"You are {self.name}, {self.role}"},
            {"role": "user", "content": f"{context}\n\n{prompt}"}
        ]
        
        try:
            response = openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=self.temperature,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Agent {self.name} thinking error: {e}")
            return f"Error in {self.name}: {str(e)}"
    
    def collaborate(self, other_agent: 'BaseAgent', topic: str) -> Dict[str, Any]:
        """Collaborate with another agent on a topic."""
        # Share context and get insights
        my_thoughts = self.think(f"Share your insights on: {topic}")
        their_thoughts = other_agent.think(
            f"Based on this insight: {my_thoughts}\nWhat are your thoughts on: {topic}"
        )
        
        return {
            f"{self.name}_insights": my_thoughts,
            f"{other_agent.name}_insights": their_thoughts,
            "synthesis": self.think(
                f"Synthesize these insights:\n1. {my_thoughts}\n2. {their_thoughts}"
            )
        }


class AgentOrchestrator:
    """Orchestrates multiple agents to solve complex research problems."""
    
    def __init__(self):
        self.agents = {}
        self.workflow_history = []
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator."""
        self.agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")
    
    def execute_workflow(self, workflow: List[Dict[str, Any]], initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow across multiple agents."""
        results = {"input": initial_input, "steps": []}
        current_data = initial_input
        
        for step in workflow:
            agent_name = step.get("agent")
            action = step.get("action", "process")
            
            if agent_name not in self.agents:
                logger.error(f"Agent {agent_name} not found")
                continue
            
            agent = self.agents[agent_name]
            
            # Execute the action
            if action == "process":
                step_result = agent.process(current_data)
            elif action == "collaborate":
                other_agent = self.agents.get(step.get("with"))
                if other_agent:
                    step_result = agent.collaborate(other_agent, step.get("topic", ""))
                else:
                    step_result = {"error": "Collaboration partner not found"}
            else:
                step_result = {"error": f"Unknown action: {action}"}
            
            # Store results
            results["steps"].append({
                "agent": agent_name,
                "action": action,
                "result": step_result
            })
            
            # Update current data for next step
            if isinstance(step_result, dict):
                current_data.update(step_result)
        
        self.workflow_history.append(results)
        return results
    
    def parallel_process(self, agents: List[str], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input through multiple agents in parallel."""
        import concurrent.futures
        
        results = {}
        
        def process_agent(agent_name):
            if agent_name in self.agents:
                return agent_name, self.agents[agent_name].process(input_data)
            return agent_name, {"error": "Agent not found"}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = [executor.submit(process_agent, agent) for agent in agents]
            
            for future in concurrent.futures.as_completed(futures):
                agent_name, result = future.result()
                results[agent_name] = result
        
        return results
    
    def synthesize_insights(self, insights: Dict[str, Any]) -> str:
        """Synthesize insights from multiple agents."""
        synthesis_prompt = "Synthesize these research insights into actionable recommendations:\n\n"
        
        for agent, insight in insights.items():
            synthesis_prompt += f"{agent}:\n{json.dumps(insight, indent=2)}\n\n"
        
        synthesis_prompt += "Provide a coherent synthesis with specific next steps."
        
        # Use a synthesis agent or the orchestrator itself
        try:
            response = openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a research synthesis expert who combines insights from multiple sources into actionable recommendations."},
                    {"role": "user", "content": synthesis_prompt}
                ],
                temperature=0.6,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return "Error synthesizing insights"