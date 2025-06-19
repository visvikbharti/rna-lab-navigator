"""
Protocol Design Agent - Creates detailed experimental protocols
"""

from typing import Dict, Any, List, Optional
from .base import BaseAgent
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ProtocolDesignAgent(BaseAgent):
    """Agent specialized in designing experimental protocols."""
    
    def __init__(self):
        super().__init__(
            name="ProtocolDesigner",
            role="an experienced lab scientist who designs detailed, practical experimental protocols with careful attention to controls, reproducibility, and safety",
            temperature=0.4  # Lower temperature for precision
        )
        
        # Common experimental considerations
        self.safety_checks = [
            "biosafety level requirements",
            "chemical hazards",
            "PPE requirements",
            "waste disposal"
        ]
        
        self.control_types = [
            "negative control",
            "positive control", 
            "vehicle control",
            "technical replicate",
            "biological replicate"
        ]
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Design a complete experimental protocol."""
        hypothesis = input_data.get('hypothesis', '')
        constraints = input_data.get('constraints', {})
        existing_methods = input_data.get('existing_methods', [])
        lab_capabilities = input_data.get('lab_capabilities', {})
        
        # Design protocol components
        protocol_overview = self._design_overview(hypothesis, constraints)
        materials = self._list_materials(protocol_overview, lab_capabilities)
        methods = self._design_methods(hypothesis, existing_methods, constraints)
        controls = self._design_controls(methods)
        timeline = self._create_timeline(methods, constraints)
        analysis_plan = self._design_analysis(hypothesis, methods)
        troubleshooting = self._create_troubleshooting_guide(methods)
        
        # Validate protocol
        validation = self._validate_protocol(methods, materials, constraints)
        
        return {
            "protocol_name": self._generate_protocol_name(hypothesis),
            "overview": protocol_overview,
            "materials": materials,
            "methods": methods,
            "controls": controls,
            "timeline": timeline,
            "analysis_plan": analysis_plan,
            "troubleshooting": troubleshooting,
            "validation": validation,
            "estimated_cost": self._estimate_cost(materials),
            "safety_considerations": self._assess_safety(materials, methods)
        }
    
    def _generate_protocol_name(self, hypothesis: str) -> str:
        """Generate a descriptive protocol name."""
        prompt = f"""
Create a concise, descriptive protocol name (5-10 words) for testing this hypothesis:
{hypothesis}

The name should indicate the key technique and target.
"""
        name = self.think(prompt).strip()
        return name.replace('"', '').replace("'", '')[:100]  # Clean and limit length
    
    def _design_overview(self, hypothesis: str, constraints: Dict) -> Dict[str, Any]:
        """Design protocol overview."""
        prompt = f"""
Design an experimental protocol to test this hypothesis:
{hypothesis}

Constraints:
- Time: {constraints.get('time', 'Not specified')}
- Budget: {constraints.get('budget', 'Not specified')}
- Equipment: {constraints.get('equipment', 'Standard lab equipment')}

Provide:
1. Objective (1-2 sentences)
2. Approach (brief methodology overview)
3. Expected outcomes
4. Key milestones
"""
        
        overview_text = self.think(prompt)
        
        return {
            "objective": self._extract_section(overview_text, "Objective"),
            "approach": self._extract_section(overview_text, "Approach"),
            "expected_outcomes": self._extract_section(overview_text, "Expected outcomes"),
            "milestones": self._extract_section(overview_text, "milestones"),
            "hypothesis": hypothesis
        }
    
    def _list_materials(self, overview: Dict, lab_capabilities: Dict) -> Dict[str, List]:
        """Generate comprehensive materials list."""
        prompt = f"""
Based on this protocol overview:
{json.dumps(overview, indent=2)}

List all required materials in these categories:
1. Reagents (with catalog numbers if common)
2. Equipment
3. Consumables
4. Cell lines/organisms (if applicable)
5. Software/analysis tools

Be specific with concentrations, volumes, and specifications.
"""
        
        materials_text = self.think(prompt)
        
        # Parse into categories
        materials = {
            "reagents": self._extract_list(materials_text, "Reagents"),
            "equipment": self._extract_list(materials_text, "Equipment"),
            "consumables": self._extract_list(materials_text, "Consumables"),
            "biological_materials": self._extract_list(materials_text, "Cell lines|organisms"),
            "software": self._extract_list(materials_text, "Software|analysis tools")
        }
        
        return materials
    
    def _design_methods(self, hypothesis: str, existing_methods: List[str], 
                       constraints: Dict) -> List[Dict]:
        """Design detailed step-by-step methods."""
        existing_context = "\n".join(existing_methods) if existing_methods else "No existing methods provided"
        
        prompt = f"""
Design detailed step-by-step methods to test:
{hypothesis}

Consider these existing methods in the lab:
{existing_context}

Time constraint: {constraints.get('time', 'Not specified')}

Provide numbered steps with:
- Clear instructions
- Specific temperatures, times, concentrations
- Critical steps marked
- Pause points identified
- Safety warnings where needed

Format each step as:
Step X: [Action]
- Details: [specifics]
- Duration: [time]
- Critical: [yes/no]
- Safety: [any warnings]
"""
        
        methods_text = self.think(prompt)
        
        # Parse into structured steps
        steps = []
        current_step = {}
        
        for line in methods_text.split('\n'):
            if line.strip().startswith('Step'):
                if current_step:
                    steps.append(current_step)
                current_step = {
                    'step_number': len(steps) + 1,
                    'action': line.split(':', 1)[1].strip() if ':' in line else line,
                    'details': '',
                    'duration': '',
                    'critical': False,
                    'safety': ''
                }
            elif '- Details:' in line:
                current_step['details'] = line.split(':', 1)[1].strip()
            elif '- Duration:' in line:
                current_step['duration'] = line.split(':', 1)[1].strip()
            elif '- Critical:' in line:
                current_step['critical'] = 'yes' in line.lower()
            elif '- Safety:' in line:
                current_step['safety'] = line.split(':', 1)[1].strip()
        
        if current_step:
            steps.append(current_step)
        
        return steps if steps else [{"step_number": 1, "action": methods_text, "details": "", 
                                    "duration": "Variable", "critical": False, "safety": ""}]
    
    def _design_controls(self, methods: List[Dict]) -> List[Dict]:
        """Design appropriate controls."""
        method_summary = "\n".join([f"Step {m['step_number']}: {m['action']}" for m in methods])
        
        prompt = f"""
Design controls for this experimental protocol:
{method_summary}

Include:
1. Negative controls (what should show no effect)
2. Positive controls (what should show known effect)
3. Technical controls (for method validation)
4. Statistical requirements (replicates, power)

For each control, specify:
- Type
- Purpose
- Setup details
- Expected result
"""
        
        controls_text = self.think(prompt)
        
        # Parse controls
        controls = []
        for control_type in self.control_types:
            if control_type in controls_text.lower():
                controls.append({
                    "type": control_type,
                    "purpose": self._extract_section(controls_text, control_type),
                    "setup": f"Run parallel to experimental samples",
                    "expected_result": "As per standard for " + control_type
                })
        
        return controls
    
    def _create_timeline(self, methods: List[Dict], constraints: Dict) -> Dict[str, Any]:
        """Create realistic timeline."""
        total_time = constraints.get('time', '2 weeks')
        
        # Calculate total duration from methods
        total_hours = 0
        for method in methods:
            duration = method.get('duration', '1 hour')
            # Simple parsing - could be more sophisticated
            if 'hour' in duration:
                hours = float(duration.split()[0]) if duration[0].isdigit() else 1
                total_hours += hours
            elif 'day' in duration:
                days = float(duration.split()[0]) if duration[0].isdigit() else 1
                total_hours += days * 8  # Assume 8-hour workday
        
        # Create daily schedule
        days_needed = max(1, int(total_hours / 6))  # 6 productive hours per day
        
        timeline = {
            "total_duration": f"{days_needed} days",
            "daily_schedule": [],
            "milestones": [],
            "critical_path": []
        }
        
        # Distribute methods across days
        current_day = 1
        current_hours = 0
        day_tasks = []
        
        for method in methods:
            method_hours = 1  # Default
            if 'hour' in method.get('duration', ''):
                try:
                    method_hours = float(method['duration'].split()[0])
                except:
                    method_hours = 1
            
            if current_hours + method_hours > 6:
                timeline['daily_schedule'].append({
                    "day": current_day,
                    "tasks": day_tasks,
                    "total_hours": current_hours
                })
                current_day += 1
                current_hours = method_hours
                day_tasks = [f"Step {method['step_number']}: {method['action']}"]
            else:
                current_hours += method_hours
                day_tasks.append(f"Step {method['step_number']}: {method['action']}")
        
        if day_tasks:
            timeline['daily_schedule'].append({
                "day": current_day,
                "tasks": day_tasks,
                "total_hours": current_hours
            })
        
        # Add milestones
        timeline['milestones'] = [
            {"day": 1, "milestone": "Protocol initiation"},
            {"day": days_needed // 2, "milestone": "Mid-point check"},
            {"day": days_needed, "milestone": "Data collection complete"}
        ]
        
        return timeline
    
    def _design_analysis(self, hypothesis: str, methods: List[Dict]) -> Dict[str, Any]:
        """Design data analysis plan."""
        prompt = f"""
Design a data analysis plan for testing:
{hypothesis}

The protocol has {len(methods)} steps.

Include:
1. Primary outcome measures
2. Secondary outcomes
3. Statistical tests to use
4. Power calculation
5. Data visualization plan
6. Criteria for success/failure
"""
        
        analysis_text = self.think(prompt)
        
        return {
            "primary_outcomes": self._extract_section(analysis_text, "Primary outcome"),
            "secondary_outcomes": self._extract_section(analysis_text, "Secondary outcome"),
            "statistical_tests": self._extract_section(analysis_text, "Statistical test"),
            "power_calculation": self._extract_section(analysis_text, "Power calculation"),
            "visualization": self._extract_section(analysis_text, "visualization"),
            "success_criteria": self._extract_section(analysis_text, "success|criteria")
        }
    
    def _create_troubleshooting_guide(self, methods: List[Dict]) -> List[Dict]:
        """Create troubleshooting guide."""
        method_summary = "\n".join([f"{m['action']}" for m in methods[:5]])  # First 5 steps
        
        prompt = f"""
Create a troubleshooting guide for this protocol:
{method_summary}

For each potential problem:
1. Describe the issue
2. Likely causes
3. Solutions to try
4. Prevention tips

Focus on the most common problems researchers face.
"""
        
        troubleshooting_text = self.think(prompt)
        
        # Parse into problems and solutions
        problems = []
        lines = troubleshooting_text.split('\n')
        
        current_problem = {}
        for line in lines:
            if any(word in line.lower() for word in ['problem', 'issue', 'error', 'failure']):
                if current_problem:
                    problems.append(current_problem)
                current_problem = {
                    'problem': line.strip(),
                    'causes': [],
                    'solutions': [],
                    'prevention': ''
                }
            elif 'cause' in line.lower():
                current_problem['causes'].append(line.strip())
            elif 'solution' in line.lower() or 'try' in line.lower():
                current_problem['solutions'].append(line.strip())
            elif 'prevent' in line.lower():
                current_problem['prevention'] = line.strip()
        
        if current_problem:
            problems.append(current_problem)
        
        return problems[:5]  # Top 5 issues
    
    def _validate_protocol(self, methods: List[Dict], materials: Dict, 
                          constraints: Dict) -> Dict[str, Any]:
        """Validate protocol feasibility."""
        validation = {
            "is_valid": True,
            "warnings": [],
            "suggestions": [],
            "feasibility_score": 85  # Default
        }
        
        # Check time constraints
        if constraints.get('time'):
            # Simple check - could be more sophisticated
            if len(methods) > 20 and 'day' in constraints['time'] and '1' in constraints['time']:
                validation['warnings'].append("Protocol may be too complex for 1-day timeline")
                validation['feasibility_score'] -= 20
        
        # Check materials availability
        total_materials = sum(len(items) for items in materials.values())
        if total_materials > 50:
            validation['suggestions'].append("Consider simplifying protocol - requires many materials")
            validation['feasibility_score'] -= 10
        
        # Check for critical steps
        critical_count = sum(1 for m in methods if m.get('critical', False))
        if critical_count > len(methods) / 2:
            validation['warnings'].append("Many critical steps - higher risk of failure")
            validation['feasibility_score'] -= 15
        
        validation['is_valid'] = validation['feasibility_score'] > 50
        
        return validation
    
    def _estimate_cost(self, materials: Dict) -> Dict[str, Any]:
        """Estimate protocol costs."""
        # Simple estimation - in practice would use catalog prices
        costs = {
            "reagents": len(materials.get('reagents', [])) * 50,
            "consumables": len(materials.get('consumables', [])) * 20,
            "other": 100  # Overhead
        }
        
        total = sum(costs.values())
        
        return {
            "breakdown": costs,
            "total_estimated": f"${total}",
            "confidence": "low",  # Since we're estimating
            "note": "Rough estimate - verify with actual catalog prices"
        }
    
    def _assess_safety(self, materials: Dict, methods: List[Dict]) -> List[Dict]:
        """Assess safety considerations."""
        safety_concerns = []
        
        # Check materials for common hazards
        all_materials = " ".join([
            " ".join(items) for items in materials.values()
        ])
        
        hazard_keywords = {
            "biosafety": ["cell", "virus", "bacteria", "organism"],
            "chemical": ["acid", "base", "organic solvent", "formaldehyde"],
            "radiation": ["radioactive", "UV", "X-ray"],
            "sharps": ["needle", "blade", "glass"]
        }
        
        for hazard_type, keywords in hazard_keywords.items():
            if any(keyword in all_materials.lower() for keyword in keywords):
                safety_concerns.append({
                    "type": hazard_type,
                    "concern": f"Protocol involves {hazard_type} hazards",
                    "precautions": f"Follow standard {hazard_type} safety protocols",
                    "ppe": "Lab coat, gloves, safety glasses" + 
                          (" + face shield" if hazard_type == "chemical" else "")
                })
        
        # Check methods for safety notes
        for method in methods:
            if method.get('safety'):
                safety_concerns.append({
                    "type": "procedural",
                    "concern": method['safety'],
                    "step": method['step_number'],
                    "precautions": "Follow step-specific safety guidelines"
                })
        
        return safety_concerns
    
    def _extract_section(self, text: str, section_pattern: str) -> str:
        """Extract a section from text based on pattern."""
        import re
        pattern = rf'{section_pattern}[:\s]*([^\n]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""
    
    def _extract_list(self, text: str, section_pattern: str) -> List[str]:
        """Extract a list from text section."""
        import re
        # Find the section
        pattern = rf'{section_pattern}[:\s]*\n((?:[-•*]\s*[^\n]+\n?)*)'
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        
        if match:
            items_text = match.group(1)
            # Extract individual items
            items = re.findall(r'[-•*]\s*([^\n]+)', items_text)
            return [item.strip() for item in items]
        
        return []