# Weekend Implementation Guide - RNA Lab Intelligence Platform

## 🚀 Friday Evening: Spectacular UI Foundation (4-6 hours)

### 1. Install Animation Dependencies
```bash
cd frontend
npm install three @react-three/fiber @react-three/drei framer-motion lottie-react react-particles @tsparticles/react
```

### 2. Create Animated Background Component
```jsx
// frontend/src/components/AnimatedBackground.jsx
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Sphere, MeshDistortMaterial } from '@react-three/drei'
import { Suspense } from 'react'

function AnimatedSphere() {
  return (
    <Sphere visible args={[1, 100, 200]} scale={2}>
      <MeshDistortMaterial
        color="#6B46C1"
        attach="material"
        distort={0.3}
        speed={1.5}
        roughness={0.4}
      />
    </Sphere>
  )
}

export default function AnimatedBackground() {
  return (
    <div className="fixed inset-0 -z-10">
      <Canvas camera={{ fov: 25 }}>
        <Suspense fallback={null}>
          <ambientLight intensity={0.5} />
          <directionalLight position={[10, 10, 5]} />
          <AnimatedSphere />
          <OrbitControls enableZoom={false} autoRotate />
        </Suspense>
      </Canvas>
      
      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-transparent to-blue-900/20" />
    </div>
  )
}
```

### 3. Glass Morphism Chat Component
```jsx
// frontend/src/components/GlassChatBox.jsx
import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'

export default function GlassChatBox() {
  const [messages, setMessages] = useState([])
  const [selectedModel, setSelectedModel] = useState('gpt-4o')
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 shadow-2xl"
    >
      {/* Model Selector */}
      <div className="flex items-center justify-between mb-6">
        <motion.div 
          className="flex gap-2"
          whileHover={{ scale: 1.02 }}
        >
          <button
            onClick={() => setSelectedModel('gpt-4o')}
            className={`px-4 py-2 rounded-lg transition-all ${
              selectedModel === 'gpt-4o' 
                ? 'bg-purple-600 text-white' 
                : 'bg-white/10 text-white/70 hover:bg-white/20'
            }`}
          >
            GPT-4o ⚡
          </button>
          <button
            onClick={() => setSelectedModel('o3')}
            className={`px-4 py-2 rounded-lg transition-all ${
              selectedModel === 'o3' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white/10 text-white/70 hover:bg-white/20'
            }`}
          >
            o3 🧠
          </button>
        </motion.div>
        
        <div className="text-white/70 text-sm">
          Tier: <span className="text-yellow-400">Advanced 🥈</span>
        </div>
      </div>
      
      {/* Messages */}
      <div className="h-96 overflow-y-auto space-y-4 mb-4">
        <AnimatePresence>
          {messages.map((msg, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: msg.role === 'user' ? 20 : -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-md px-4 py-2 rounded-2xl ${
                msg.role === 'user' 
                  ? 'bg-purple-600/80 text-white' 
                  : 'bg-white/10 text-white'
              }`}>
                {msg.content}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
      
      {/* Input */}
      <motion.input
        whileFocus={{ scale: 1.02 }}
        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-500"
        placeholder={`Ask ${selectedModel === 'o3' ? 'a breakthrough question' : 'about your research'}...`}
      />
    </motion.div>
  )
}
```

### 4. Particle Effects System
```jsx
// frontend/src/components/ParticleField.jsx
import Particles from '@tsparticles/react'
import { loadSlim } from '@tsparticles/slim'

export default function ParticleField() {
  const particlesInit = async (engine) => {
    await loadSlim(engine)
  }
  
  return (
    <Particles
      init={particlesInit}
      options={{
        particles: {
          color: { value: "#6B46C1" },
          move: {
            enable: true,
            speed: 1,
            direction: "none",
            random: true,
            straight: false,
            outModes: "bounce",
          },
          number: {
            density: { enable: true, area: 800 },
            value: 80,
          },
          opacity: {
            value: 0.3,
            random: true,
            animation: {
              enable: true,
              speed: 1,
              minimumValue: 0.1,
            },
          },
          size: {
            value: { min: 1, max: 3 },
          },
          links: {
            enable: true,
            distance: 150,
            color: "#6B46C1",
            opacity: 0.2,
          },
        },
      }}
    />
  )
}
```

## 🧬 Saturday: "What If" Research Simulator (8-10 hours)

### 1. Backend: Hypothesis Mode Handler
```python
# backend/api/llm/hypothesis_engine.py
from typing import Dict, List
import openai
from django.conf import settings

class HypothesisEngine:
    """Advanced reasoning engine for research hypotheses"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
    def generate_hypothesis(self, query: str, context: List[Dict], model: str = "gpt-4o") -> Dict:
        """Generate research hypothesis with confidence scoring"""
        
        # Construct hypothesis prompt
        system_prompt = """You are an advanced research hypothesis generator. 
        When given a "what if" scenario, you must:
        1. Analyze feasibility based on current scientific knowledge
        2. Identify potential challenges and opportunities
        3. Suggest experimental approaches
        4. Provide confidence scores for each aspect
        5. Reference relevant papers from the context
        
        Format your response with clear sections and confidence percentages."""
        
        # Enhanced prompt for o3 model
        if model == "o3":
            system_prompt += """
            Additionally, for o3 advanced reasoning:
            - Consider breakthrough implications
            - Identify paradigm-shifting potential
            - Suggest unconventional approaches
            - Connect disparate research areas"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context}\n\nHypothesis Query: {query}"}
        ]
        
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse and structure response
        return self._parse_hypothesis_response(response.choices[0].message.content)
    
    def _parse_hypothesis_response(self, response: str) -> Dict:
        """Parse hypothesis response into structured format"""
        return {
            "hypothesis": response,
            "confidence_scores": self._extract_confidence_scores(response),
            "experimental_approaches": self._extract_approaches(response),
            "references": self._extract_references(response),
            "breakthrough_potential": self._assess_breakthrough_potential(response)
        }
```

### 2. Frontend: Hypothesis Mode UI
```jsx
// frontend/src/components/HypothesisMode.jsx
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Brain, Beaker, TrendingUp } from 'lucide-react'

export default function HypothesisMode({ onSubmit }) {
  const [hypothesis, setHypothesis] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  
  const generateHypothesis = async () => {
    setLoading(true)
    const response = await fetch('/api/hypothesis/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        query: hypothesis,
        model: 'o3' // Use advanced model for hypotheses
      })
    })
    const data = await response.json()
    setResults(data)
    setLoading(false)
  }
  
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Hypothesis Input */}
      <div className="relative">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="absolute -top-12 right-0 text-purple-400"
        >
          <Brain size={32} />
        </motion.div>
        
        <textarea
          value={hypothesis}
          onChange={(e) => setHypothesis(e.target.value)}
          placeholder="What if we applied FnCas9 variants to brain organoid systems..."
          className="w-full h-32 p-4 bg-white/10 backdrop-blur-xl border border-purple-500/30 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-500"
        />
        
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={generateHypothesis}
          disabled={loading}
          className="mt-4 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold flex items-center gap-2"
        >
          {loading ? (
            <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity }}>
              <Sparkles />
            </motion.div>
          ) : (
            <Sparkles />
          )}
          Generate Research Hypothesis
        </motion.button>
      </div>
      
      {/* Results Display */}
      <AnimatePresence>
        {results && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            {/* Confidence Meters */}
            <div className="grid grid-cols-2 gap-4">
              <ConfidenceMeter
                label="Feasibility"
                value={results.confidence_scores.feasibility}
                icon={<Beaker />}
              />
              <ConfidenceMeter
                label="Innovation"
                value={results.confidence_scores.innovation}
                icon={<TrendingUp />}
              />
            </div>
            
            {/* Hypothesis Content */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="p-6 bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl"
            >
              <h3 className="text-xl font-bold text-white mb-4">Research Hypothesis</h3>
              <div className="text-white/90 space-y-4 whitespace-pre-wrap">
                {results.hypothesis}
              </div>
            </motion.div>
            
            {/* Experimental Approaches */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="p-6 bg-gradient-to-br from-purple-900/20 to-blue-900/20 backdrop-blur-xl border border-white/10 rounded-xl"
            >
              <h3 className="text-xl font-bold text-white mb-4">Suggested Experiments</h3>
              <ul className="space-y-2">
                {results.experimental_approaches.map((approach, idx) => (
                  <motion.li
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + idx * 0.1 }}
                    className="flex items-start gap-2 text-white/80"
                  >
                    <span className="text-purple-400">▸</span>
                    {approach}
                  </motion.li>
                ))}
              </ul>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function ConfidenceMeter({ label, value, icon }) {
  return (
    <motion.div
      initial={{ scale: 0.9 }}
      animate={{ scale: 1 }}
      className="p-4 bg-white/5 backdrop-blur-xl border border-white/10 rounded-lg"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-white/70 text-sm">{label}</span>
        <div className="text-purple-400">{icon}</div>
      </div>
      <div className="relative h-2 bg-white/10 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
          className="absolute h-full bg-gradient-to-r from-purple-500 to-blue-500"
        />
      </div>
      <div className="text-right mt-1 text-white font-bold">{value}%</div>
    </motion.div>
  )
}
```

## 🧪 Sunday: Intelligent Protocol Generator (8-10 hours)

### 1. Backend: Protocol Generation Engine
```python
# backend/api/protocols/generator.py
from typing import List, Dict, Optional
import json
from django.db.models import Q
from api.models import Document
from api.llm.local_llm import get_llm

class ProtocolGenerator:
    """Intelligent protocol generation from existing templates"""
    
    def __init__(self):
        self.llm = get_llm()
        
    def generate_custom_protocol(
        self, 
        requirements: str, 
        sample_type: str,
        techniques: List[str],
        user_constraints: Optional[Dict] = None
    ) -> Dict:
        """Generate custom protocol by combining existing protocols"""
        
        # Find relevant protocols
        relevant_protocols = self._find_relevant_protocols(techniques, sample_type)
        
        # Extract protocol chunks
        protocol_chunks = self._extract_protocol_chunks(relevant_protocols)
        
        # Generate combined protocol
        system_prompt = """You are a protocol generation expert. 
        Create a detailed, step-by-step protocol by intelligently combining 
        elements from existing protocols. Ensure:
        1. Logical flow and proper sequencing
        2. Safety warnings and precautions
        3. Material and reagent lists
        4. Time estimates for each step
        5. Troubleshooting tips
        
        Format with clear sections and numbered steps."""
        
        user_prompt = f"""
        Requirements: {requirements}
        Sample Type: {sample_type}
        Techniques: {', '.join(techniques)}
        Constraints: {json.dumps(user_constraints or {})}
        
        Available Protocol Elements:
        {protocol_chunks}
        
        Generate a comprehensive protocol that meets these requirements.
        """
        
        response = self.llm.invoke(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        return self._structure_protocol(response, requirements)
    
    def _find_relevant_protocols(self, techniques: List[str], sample_type: str) -> List[Document]:
        """Find protocols matching techniques and sample type"""
        query = Q(doc_type='protocol')
        
        # Search for technique matches
        technique_q = Q()
        for technique in techniques:
            technique_q |= Q(content__icontains=technique)
        
        # Search for sample type matches
        if sample_type:
            query &= Q(content__icontains=sample_type)
            
        return Document.objects.filter(query & technique_q)
    
    def _structure_protocol(self, raw_protocol: str, title: str) -> Dict:
        """Structure the generated protocol"""
        return {
            "title": f"Custom Protocol: {title}",
            "version": "1.0",
            "generated_date": datetime.now().isoformat(),
            "sections": self._parse_protocol_sections(raw_protocol),
            "estimated_time": self._estimate_time(raw_protocol),
            "difficulty": self._assess_difficulty(raw_protocol),
            "validation_status": "pending_review"
        }
```

### 2. Frontend: Protocol Builder UI
```jsx
// frontend/src/components/ProtocolBuilder.jsx
import { useState } from 'react'
import { DndContext, closestCenter, DragOverlay } from '@dnd-kit/core'
import { arrayMove, SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Flask, Clock, AlertTriangle } from 'lucide-react'

export default function ProtocolBuilder() {
  const [requirements, setRequirements] = useState('')
  const [sampleType, setSampleType] = useState('')
  const [techniques, setTechniques] = useState([])
  const [generatedProtocol, setGeneratedProtocol] = useState(null)
  const [activeId, setActiveId] = useState(null)
  
  const availableTechniques = [
    'RNA Extraction', 'qPCR', 'Western Blot', 'Cell Culture',
    'Transfection', 'CRISPR', 'Flow Cytometry', 'Immunostaining'
  ]
  
  const generateProtocol = async () => {
    const response = await fetch('/api/protocols/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        requirements,
        sample_type: sampleType,
        techniques
      })
    })
    const data = await response.json()
    setGeneratedProtocol(data)
  }
  
  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* Input Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6"
      >
        <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
          <Flask className="text-purple-400" />
          Protocol Generator
        </h2>
        
        {/* Requirements Input */}
        <div className="space-y-4">
          <div>
            <label className="block text-white/70 mb-2">What do you need to do?</label>
            <textarea
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              placeholder="Extract RNA from frozen tissue samples for single-cell analysis..."
              className="w-full h-24 p-3 bg-white/5 border border-white/20 rounded-lg text-white placeholder-white/40"
            />
          </div>
          
          {/* Sample Type */}
          <div>
            <label className="block text-white/70 mb-2">Sample Type</label>
            <input
              value={sampleType}
              onChange={(e) => setSampleType(e.target.value)}
              placeholder="Frozen tissue, cell culture, blood..."
              className="w-full p-3 bg-white/5 border border-white/20 rounded-lg text-white placeholder-white/40"
            />
          </div>
          
          {/* Technique Selection */}
          <div>
            <label className="block text-white/70 mb-2">Select Techniques</label>
            <div className="grid grid-cols-4 gap-2">
              {availableTechniques.map((tech) => (
                <motion.button
                  key={tech}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {
                    setTechniques(prev => 
                      prev.includes(tech) 
                        ? prev.filter(t => t !== tech)
                        : [...prev, tech]
                    )
                  }}
                  className={`p-2 rounded-lg text-sm transition-all ${
                    techniques.includes(tech)
                      ? 'bg-purple-600 text-white'
                      : 'bg-white/10 text-white/70 hover:bg-white/20'
                  }`}
                >
                  {tech}
                </motion.button>
              ))}
            </div>
          </div>
          
          {/* Generate Button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={generateProtocol}
            className="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold"
          >
            Generate Custom Protocol
          </motion.button>
        </div>
      </motion.div>
      
      {/* Generated Protocol Display */}
      <AnimatePresence>
        {generatedProtocol && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6"
          >
            {/* Protocol Header */}
            <div className="flex items-start justify-between mb-6">
              <div>
                <h3 className="text-2xl font-bold text-white">
                  {generatedProtocol.title}
                </h3>
                <div className="flex items-center gap-4 mt-2 text-white/70">
                  <span className="flex items-center gap-1">
                    <Clock size={16} />
                    {generatedProtocol.estimated_time}
                  </span>
                  <span className="px-2 py-1 bg-purple-600/30 rounded text-xs">
                    {generatedProtocol.difficulty}
                  </span>
                </div>
              </div>
              
              {/* Action Buttons */}
              <div className="flex gap-2">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  className="px-4 py-2 bg-white/10 text-white rounded-lg"
                >
                  Save
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg"
                >
                  Export PDF
                </motion.button>
              </div>
            </div>
            
            {/* Protocol Sections */}
            <div className="space-y-6">
              {generatedProtocol.sections.map((section, idx) => (
                <ProtocolSection key={idx} section={section} index={idx} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function ProtocolSection({ section, index }) {
  const [expanded, setExpanded] = useState(true)
  
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className="border border-white/10 rounded-lg overflow-hidden"
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 bg-white/5 text-left flex items-center justify-between hover:bg-white/10 transition-colors"
      >
        <h4 className="text-lg font-semibold text-white">{section.title}</h4>
        <motion.div
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-white/50"
        >
          ▼
        </motion.div>
      </button>
      
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 space-y-3 text-white/80">
              {section.steps.map((step, stepIdx) => (
                <div key={stepIdx} className="flex gap-3">
                  <span className="text-purple-400 font-mono">{stepIdx + 1}.</span>
                  <div className="flex-1">
                    <p>{step.description}</p>
                    {step.warning && (
                      <div className="mt-2 flex items-start gap-2 text-yellow-400 text-sm">
                        <AlertTriangle size={16} className="mt-0.5" />
                        <span>{step.warning}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
```

## 🔐 User Authentication System (Parallel Implementation)

### Backend Authentication
```python
# backend/api/auth/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class ResearchUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription_tier = models.CharField(
        max_length=20,
        choices=[
            ('basic', 'Basic'),
            ('advanced', 'Advanced'),
            ('unlimited', 'Unlimited'),
        ],
        default='basic'
    )
    lab_affiliation = models.CharField(max_length=200)
    monthly_query_limit = models.IntegerField(default=100)
    queries_used_this_month = models.IntegerField(default=0)
    preferred_model = models.CharField(max_length=20, default='gpt-4o')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def can_use_model(self, model: str) -> bool:
        if model == 'gpt-4o':
            return True
        elif model == 'o3':
            return self.subscription_tier in ['advanced', 'unlimited']
        return False
    
    def has_queries_remaining(self) -> bool:
        if self.subscription_tier == 'unlimited':
            return True
        return self.queries_used_this_month < self.monthly_query_limit

# backend/api/auth/serializers.py
from rest_framework import serializers
from .models import ResearchUser

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = ResearchUser
        fields = ['email', 'username', 'password', 'lab_affiliation']
    
    def create(self, validated_data):
        user = ResearchUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            lab_affiliation=validated_data.get('lab_affiliation', '')
        )
        return user
```

### Frontend Login/Register
```jsx
// frontend/src/components/Auth/LoginModal.jsx
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { User, Lock, Mail, Building } from 'lucide-react'

export default function LoginModal({ isOpen, onClose, onSuccess }) {
  const [mode, setMode] = useState('login') // 'login' or 'register'
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    lab_affiliation: ''
  })
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    const endpoint = mode === 'login' ? '/api/auth/login/' : '/api/auth/register/'
    
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    })
    
    if (response.ok) {
      const data = await response.json()
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      onSuccess(data.user)
    }
  }
  
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-gray-900/90 backdrop-blur-xl border border-white/20 rounded-2xl p-8 max-w-md w-full"
          >
            {/* Header */}
            <h2 className="text-2xl font-bold text-white mb-6 text-center">
              {mode === 'login' ? 'Welcome Back' : 'Join RNA Lab Navigator'}
            </h2>
            
            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="relative">
                <User className="absolute left-3 top-3 text-white/50" size={20} />
                <input
                  type="text"
                  placeholder="Username"
                  value={formData.username}
                  onChange={(e) => setFormData({...formData, username: e.target.value})}
                  className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50"
                  required
                />
              </div>
              
              {mode === 'register' && (
                <>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 text-white/50" size={20} />
                    <input
                      type="email"
                      placeholder="Email"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50"
                      required
                    />
                  </div>
                  
                  <div className="relative">
                    <Building className="absolute left-3 top-3 text-white/50" size={20} />
                    <input
                      type="text"
                      placeholder="Lab Affiliation"
                      value={formData.lab_affiliation}
                      onChange={(e) => setFormData({...formData, lab_affiliation: e.target.value})}
                      className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50"
                    />
                  </div>
                </>
              )}
              
              <div className="relative">
                <Lock className="absolute left-3 top-3 text-white/50" size={20} />
                <input
                  type="password"
                  placeholder="Password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50"
                  required
                />
              </div>
              
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                className="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold"
              >
                {mode === 'login' ? 'Sign In' : 'Create Account'}
              </motion.button>
            </form>
            
            {/* Toggle Mode */}
            <p className="text-center text-white/70 mt-6">
              {mode === 'login' ? "Don't have an account?" : "Already have an account?"}
              <button
                onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
                className="text-purple-400 ml-2 hover:underline"
              >
                {mode === 'login' ? 'Sign Up' : 'Sign In'}
              </button>
            </p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
```

## 🎬 Quick Start Commands

```bash
# Friday Evening - Start Here
cd frontend
npm install three @react-three/fiber @react-three/drei framer-motion lottie-react @tsparticles/react
npm run dev

# Backend Setup (parallel terminal)
cd backend
python manage.py makemigrations auth
python manage.py migrate
python manage.py createsuperuser

# Test Everything
# 1. Visit http://localhost:5173
# 2. See spectacular animations
# 3. Register new account
# 4. Test hypothesis mode
# 5. Generate a protocol
```

## 🚨 Important Notes

1. **API Keys**: Update settings.py with o3 model access when available
2. **Database**: Run migrations for new user model
3. **Performance**: Use React.memo for heavy 3D components
4. **Security**: Implement rate limiting for expensive o3 calls
5. **Testing**: Create test users with different subscription tiers

This guide gives you everything needed for an incredible weekend of building! The result will be a platform that's not just functional but truly inspiring for researchers. 🚀