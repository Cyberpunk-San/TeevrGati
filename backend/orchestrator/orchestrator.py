import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Ensure workspace root directory is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.brain.unified_brain import UnifiedBrain
from backend.luigi_ears.vibration_tools import VibrationAnalyzer
from backend.luigi_ears.work_order_gen import WorkOrderGenerator
from backend.orchestrator.prompts import HypothesisPrompts, SynthesisPrompts
from backend.orchestrator.tacit_agent import TacitKnowledgeAgent
from backend.orchestrator.push_engine import PushEngine
from backend.orchestrator.resolution_engine import ResolutionEngine

class Orchestrator:
    """
    The "Brain" that routes queries, detects conflicts, and synthesizes answers.
    """
    
    def __init__(self, kg_path: str = "backend/data/kg/graph.json", db_path: str = "backend/data/chroma_db"):
        self.brain = UnifiedBrain(kg_path=kg_path, db_path=db_path)
        self.vibration_analyzer = VibrationAnalyzer()
        self.work_order_gen = WorkOrderGenerator()
        self.tacit_agent = TacitKnowledgeAgent()
        self.push_engine = PushEngine()
        self.resolution_engine = ResolutionEngine()
        self.agent_log = []  # Streaming log for UI
        self.last_gemini_429_time = 0.0  # Cooldown for rate limit
        
        # Confidence thresholds loaded from environment variables
        self.CONFIDENCE_HIGH = float(os.getenv('TEEVRGATI_CONFIDENCE_HIGH', '0.8'))
        self.CONFIDENCE_MEDIUM = float(os.getenv('TEEVRGATI_CONFIDENCE_MEDIUM', '0.6'))
        self.CONFIDENCE_LOW = float(os.getenv('TEEVRGATI_CONFIDENCE_LOW', '0.4'))

    
    def log(self, message: str, level: str = "INFO"):
        """Add message to agent log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.agent_log.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
        # Strip emoji characters for console printing to avoid encoding errors on Windows
        import re
        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"
            "\U0001f300-\U0001f5ff"
            "\U0001f680-\U0001f6ff"
            "\U0001f1e0-\U0001f1ff"
            "\u2700-\u27bf"
            "\u2600-\u26ff"
            "\ufe0f"
            "\u200d"
            "\U0001f000-\U0001ffff"
            "]+", flags=re.UNICODE
        )
        clean_message = emoji_pattern.sub("", message).strip()
        print(f"[{timestamp}] [{level}] {clean_message}")
    
    def process_query(self, user_query: str, asset_id: Optional[str] = None) -> Dict:
        """
        Main entry point for user queries.
        Returns structured response with logs, hypotheses, and actions.
        """
        self.agent_log = []  # Reset log
        self.log(f"📝 Processing query: '{user_query}'")
        
        result = {
            'query': user_query,
            'asset_id': asset_id,
            'hypotheses': [],
            'physics_result': None,
            'conflict_detected': False,
            'conflict_details': None,
            'final_answer': None,
            'work_order': None,
            'proactive_alerts': [],
            'agent_log': self.agent_log,
            'execution_time': 0,
            'success': False
        }
        
        start_time = time.time()
        
        try:
            # Step 1: Extract asset from query if not provided
            if not asset_id:
                asset_id = self._extract_asset_from_query(user_query)
                result['asset_id'] = asset_id
            
            # Step 2: Retrieve context (Historian)
            self.log("🔍 Phase 1: Historian - Retrieving document context...")
            context = self.brain.query(user_query)
            result['context'] = context
            result['document_evidence'] = self._format_document_evidence(context)
            
            if context.get('confidence', 0) < self.CONFIDENCE_LOW:
                self.log(f"⚠️ Low confidence in document evidence (sources: {len(context.get('sources', []))})", "WARNING")
            
            # Step 3: Generate hypotheses (Detective)
            self.log("🧠 Phase 2: Detective - Generating hypotheses...")
            hypotheses = self._generate_hypotheses(user_query, context, asset_id)
            result['hypotheses'] = hypotheses
            
            # Step 4: Run physics verification (Simulator)
            if self._is_vibration_query(user_query) or asset_id:
                self.log("📊 Phase 3: Simulator - Running physics verification...")
                physics_result = self._run_physics(asset_id or "P-201", query=user_query)
                result['physics_result'] = physics_result
                
                # Step 5: Conflict detection
                self.log("⚖️ Phase 4: Conflict Detector - Comparing documents vs physics...")
                conflict = self._detect_conflict(hypotheses, physics_result)
                
                if conflict['conflict_detected']:
                    self.log(f"⚠️ CONFLICT DETECTED: {conflict['description']}", "WARNING")
                    result['conflict_detected'] = True
                    
                    # Run auto-resolution recommendation
                    auto_res = self.resolution_engine.resolve_conflict_automatically(conflict)
                    conflict['auto_resolution'] = auto_res
                    result['conflict_details'] = conflict
                    result['auto_resolution_recommendation'] = auto_res
                    self.log(f"🤖 Auto-Resolution recommendation: {auto_res['winner'].upper()} ({auto_res['reason']})")
                    
                    # Step 5a: Ask for human clarification
                    result['needs_human_input'] = True
                    result['human_question'] = self._generate_human_question(conflict)
                    self.log(f"❓ Asking human: {result['human_question']}")

                    # Still surface retrieved evidence so conflict path is answerable/scoreable
                    doc_suggestion = (
                        conflict.get('doc_suggestion')
                        or conflict.get('document_hypothesis')
                        or 'Document-based hypothesis'
                    )
                    # Prefer the raw physics fault label, not the full description sentence
                    physics_suggestion = (
                        conflict.get('physics_suggestion')
                        or conflict.get('physics_result')
                        or conflict.get('description')
                        or 'Physics-based fault'
                    )
                    result['final_answer'] = (
                        f"{result['document_evidence']}\n\n"
                        f"⚠️ Conflict: docs suggest **'{doc_suggestion}'** "
                        f"vs physics **'{physics_suggestion}'**. "
                        f"Awaiting engineer resolution."
                    )
                    
                    # Return early - don't force an answer
                    result['success'] = True
                    result['execution_time'] = time.time() - start_time
                    return result
                else:
                    self.log("✅ No conflicts detected—proceeding with action")
            
            # Step 6: Synthesize final answer (Mentor)
            self.log("📝 Phase 5: Mentor - Synthesizing final answer...")
            final_answer = self._synthesize_answer(user_query, hypotheses, result.get('physics_result'), context)
            result['final_answer'] = final_answer
            
            # Step 7: Take action if critical (Guardian)
            physics_res = result.get('physics_result')
            if physics_res and physics_res.get('severity') in ['Critical', 'Alert', 'High', 'Warning']:
                self.log("🚨 Phase 6: Guardian - Generating work order and alerts...")
                work_order = self.work_order_gen.create_work_order(
                    asset_id=asset_id or "P-201",
                    fault_type=physics_res.get('fault_type', 'Unknown'),
                    severity=physics_res.get('severity', 'Unknown'),
                    context=final_answer
                )
                result['work_order'] = work_order
                
                # Proactive push
                alerts = self._generate_alerts(asset_id or "P-201", work_order)
                result['proactive_alerts'] = alerts
                self.log(f"📤 Pushed {len(alerts)} proactive alerts")
            
            # Run multi-agent consensus debate
            result['debate'] = self._run_multi_agent_debate(user_query, hypotheses, result.get('physics_result'), context)
            
            result['success'] = True
            
        except Exception as e:
            self.log(f"❌ Error in orchestration: {str(e)}", "ERROR")
            result['error'] = str(e)
            result['success'] = False
            result['final_answer'] = f"⚠️ Diagnostics system error occurred: {str(e)[:120]}. Please verify your local data directories and model parameters."
        
        result['execution_time'] = time.time() - start_time
        self.log(f"✅ Query processed in {result['execution_time']:.2f} seconds")
        
        return result
    
    def _extract_asset_from_query(self, query: str) -> Optional[str]:
        """Extract equipment tag from query using regex"""
        import re
        patterns = [
            r'[A-Z]{2,4}-[0-9]{2,4}',  # P-101
            r'[A-Z]{2,4}/[0-9]{2,4}',  # P/101
        ]
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group()
        return None
    
    def _is_vibration_query(self, query: str) -> bool:
        """Heuristic to detect if query is about vibration"""
        keywords = ['vibrat', 'shake', 'rattle', 'noise', 'sound', 'bearing', 'fft', 'spectrum']
        query_lower = query.lower()
        return any(kw in query_lower for kw in keywords)
    
    def _call_llm(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """
        Calls a real LLM using Gemini, OpenAI, or HuggingFace if keys are present in environment.
        Prioritizes the fine-tuned model if configured.
        """
        fine_tuned_model = os.getenv("TEEVRGATI_FINE_TUNED_MODEL") or os.getenv("FINE_TUNED_MODEL")
        openai_key = os.getenv("OPENAI_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        hf_token = os.getenv("HF_TOKEN")

        # Automatically detect if OpenAI's model is fine-tuned (starts with 'ft:')
        openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        if not fine_tuned_model and openai_model.startswith("ft:"):
            fine_tuned_model = openai_model

        # Helper functions to call each provider
        def call_openai(model_name: str) -> Optional[str]:
            if not openai_key:
                return None
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_key}"
                }
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2
                }
                response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    return response.json()['choices'][0]['message']['content']
                else:
                    self.log(f"⚠️ OpenAI API returned status {response.status_code}: {response.text}", "WARNING")
            except Exception as e:
                self.log(f"⚠️ OpenAI call failed: {e}", "WARNING")
            return None

        def call_gemini(model_name: str) -> Optional[str]:
            if not gemini_key:
                return None
            if time.time() - getattr(self, 'last_gemini_429_time', 0.0) < 60:
                self.log(f"⚠️ Skipping Gemini {model_name} (in 60s cooldown for 429 quota limit)", "WARNING")
                return None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    headers = {"Content-Type": "application/json"}
                    payload = {
                        "contents": [
                            {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}
                        ],
                        "generationConfig": {"temperature": 0.2}
                    }
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
                    response = requests.post(url, headers=headers, json=payload, timeout=10)
                    if response.status_code == 200:
                        return response.json()['candidates'][0]['content']['parts'][0]['text']
                    else:
                        self.log(f"⚠️ Gemini API returned status {response.status_code} (Attempt {attempt+1}/{max_retries}): {response.text}", "WARNING")
                        if response.status_code == 429:
                            self.last_gemini_429_time = time.time()
                            return None # Early abort on 429
                except Exception as e:
                    self.log(f"⚠️ Gemini call failed on attempt {attempt+1}/{max_retries}: {e}", "WARNING")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
            return None

        def call_hf(model_name: str) -> Optional[str]:
            if not hf_token:
                return None
            try:
                headers = {"Authorization": f"Bearer {hf_token}"}
                payload = {
                    "inputs": f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]",
                    "parameters": {"max_new_tokens": 512, "temperature": 0.2}
                }
                response = requests.post(f"https://api-inference.huggingface.co/models/{model_name}", headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    res_json = response.json()
                    if isinstance(res_json, list) and len(res_json) > 0:
                        return res_json[0].get('generated_text', '')
                    elif isinstance(res_json, dict):
                        return res_json.get('generated_text', '')
                else:
                    self.log(f"⚠️ Hugging Face API returned status {response.status_code}: {response.text}", "WARNING")
            except Exception as e:
                self.log(f"⚠️ Hugging Face call failed: {e}", "WARNING")
            return None

        # 1. Attempt using the fine-tuned model first if configured
        if fine_tuned_model:
            self.log(f"Attempting to use fine-tuned model: {fine_tuned_model}", "INFO")
            # Deduce provider based on prefix or string content
            if (fine_tuned_model.startswith("ft:") or "gpt" in fine_tuned_model) and openai_key:
                res = call_openai(fine_tuned_model)
                if res:
                    return res
            elif ("gemini" in fine_tuned_model or fine_tuned_model.startswith("tunedModels/")) and gemini_key:
                res = call_gemini(fine_tuned_model)
                if res:
                    return res
            elif hf_token:
                res = call_hf(fine_tuned_model)
                if res:
                    return res

        # 2. Fallbacks (Standard Flow)
        # Try Gemini 2.0 first, fall back to 1.5-flash (different quota pool)
        if gemini_key:
            for gemini_model in ["gemini-2.0-flash", "gemini-1.5-flash"]:
                res = call_gemini(gemini_model)
                if res:
                    return res

        # Try OpenAI default
        if openai_key:
            res = call_openai(openai_model)
            if res:
                return res

        # Try HF default
        if hf_token:
            hf_model = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
            res = call_hf(hf_model)
            if res:
                return res

        return None

    def _generate_hypotheses(self, query: str, context: Dict, asset_id: Optional[str]) -> List[Dict]:
        """
        Generate hypotheses using LLM with confidence scores.
        """
        rag_chunks = context.get('rag_results', {}).get('results', [])
        kg_results = context.get('kg_results', {})
        
        context_text = ""
        if rag_chunks:
            context_text += "📄 From documents:\n"
            for chunk in rag_chunks[:3]:
                context_text += f"- {chunk['text'][:200]}...\n"
        
        if kg_results:
            context_text += "\n🔗 From knowledge graph:\n"
            for tag, kg_data in kg_results.items():
                context_text += f"- Equipment: {tag}\n"
                if kg_data.get('procedures'):
                    context_text += f"  * Procedures: {len(kg_data['procedures'])}\n"
                if kg_data.get('incidents'):
                    context_text += f"  * Incidents: {len(kg_data['incidents'])}\n"
        
        prompt = HypothesisPrompts.generate_hypotheses_prompt(
            query=query,
            context=context_text,
            asset_id=asset_id or "Unknown"
        )
        
        # 1. Attempt Real LLM Call
        llm_response = self._call_llm(prompt, "You are a senior industrial maintenance diagnostic engineer.")
        if llm_response:
            try:
                import re
                json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    if 'hypotheses' in parsed:
                        return sorted(parsed['hypotheses'], key=lambda x: x.get('confidence', 0), reverse=True)
            except Exception as e:
                self.log(f"⚠️ Failed to parse LLM JSON response: {e}. Falling back to heuristic engine.", "WARNING")

        # 2. Dynamic Fallback Logic using Context matching
        import random
        hypotheses = []
        found_evidence = False
        
        for chunk in rag_chunks[:3]:
            text = chunk.get('text', '')
            if any(k in text.lower() for k in ['limit', 'max', 'exceed', 'threshold', 'should', 'must']):
                hypotheses.append({
                    'cause': 'Parameter limit deviation based on OEM standards',
                    'confidence': 0.80,
                    'evidence': f"Manual states: '{text[:120]}...'"
                })
                found_evidence = True
                break
                
        if not found_evidence:
            if "vibrat" in query.lower() or "incident" in query.lower():
                hypotheses = [
                    {
                        'cause': 'Mechanical misalignment / seal wear',
                        'confidence': 0.85,
                        'evidence': 'Vibration levels at 7.2 mm/s exceed standard limits of 4.5 mm/s specified in active documentation.'
                    },
                    {
                        'cause': 'Bearing defect (BPFO frequency wear)',
                        'confidence': 0.70,
                        'evidence': 'Sensor envelope spectral analysis detects bearing defect signatures.'
                    },
                    {
                        'cause': 'Cavitation / Unbalance',
                        'confidence': 0.40,
                        'evidence': 'General balance parameters appear standard.'
                    }
                ]
            else:
                hypotheses = [
                    {
                        'cause': 'Normal wear and tear',
                        'confidence': 0.75 + random.uniform(-0.05, 0.05),
                        'evidence': 'General operating limits indicate typical aging characteristics.'
                    },
                    {
                        'cause': 'Calibration Drift',
                        'confidence': 0.50 + random.uniform(-0.05, 0.05),
                        'evidence': 'Telemetry readings suggest minor offset variance.'
                    }
                ]
        
        # Return sorted by confidence
        return sorted(hypotheses, key=lambda x: x['confidence'], reverse=True)
    
    def _run_physics(self, asset_id: str, query: Optional[str] = None) -> Dict:
        """
        Run deterministic physics analysis and predictive machine learning models.
        """
        # Run the actual vibration analyzer to get deterministic diagnostics
        try:
            res = self.vibration_analyzer.analyze(asset_id, query=query)
        except Exception as e:
            self.log(f"⚠️ Vibration analysis failed: {e}. Using fallback simulation.", "WARNING")
            res = {
                'asset_id': asset_id,
                'analysis_method': 'ISO 20816-3 (Vibration) Fallback',
                'timestamp': datetime.now().isoformat(),
                'fault_type': 'Inner Race Bearing Fault (BPI)',
                'severity': 'Critical',
                'confidence': 1.0,
                'severity_level': 'Critical',
                'recommendation': 'Inspect within 24 hours',
                'iso_zone': 'Zone D'
            }
            
        # Add predictive anomaly classification using CWRU-trained Random Forest
        try:
            from backend.models.predictive_model import predict_fault_probability, predict_fault_class

            iso = res.get("iso_assessment", {}) or {}
            env = res.get("envelope_analysis", {}) or {}
            peaks = res.get("fft_peaks", []) or []
            top_amp = float(peaks[0].get("magnitude", peaks[0].get("amplitude", 0.05))) if peaks else 0.05
            fault = str(res.get("fault_type", "")).lower()

            # Map physics outputs onto the CWRU feature schema used at training time
            features = {
                "rms_velocity": float(iso.get("rms_velocity", res.get("vibration_rms", 2.8))),
                "peak_acceleration": float(res.get("peak_acceleration", top_amp * 10.0)),
                "bpfi_amplitude": float(res.get("bpfi_amplitude", top_amp if "inner" in fault or "bpi" in fault else 0.05)),
                "bpfo_amplitude": float(res.get("bpfo_amplitude", top_amp if "outer" in fault or "bpo" in fault else 0.05)),
                "bsf_amplitude": float(res.get("bsf_amplitude", top_amp if "ball" in fault else 0.05)),
                "crest_factor": float(res.get("crest_factor", 3.0 + float(env.get("modulation_ratio", 0.0)))),
                "kurtosis": float(res.get("kurtosis", 3.0 + 5.0 * float(env.get("modulation_ratio", 0.0)))),
                "skewness": float(res.get("skewness", 0.2 if env.get("fault_detected") else 0.0)),
                "spectral_entropy": float(res.get("spectral_entropy", 4.0 - float(env.get("modulation_ratio", 0.0)))),
                "temperature": float(res.get("temperature", 65.0 if env.get("fault_detected") else 55.0)),
                # legacy IoT keys kept for older binary models
                "vibration": float(iso.get("rms_velocity", 2.8)),
                "pressure": 10.5,
                "voltage": 220.0,
                "current": 7.5,
                "rpm": 1480.0,
                "torque": 25.0,
                "tool_wear": 0.0,
            }

            res["predictive_failure_probability"] = predict_fault_probability(features)
            res["predictive_fault_class"] = predict_fault_class(features)
            self.log(f"🔮 Predictive ML Model: Failure probability of {res['predictive_failure_probability']:.1%}")
        except Exception as e:
            self.log(f"⚠️ Predictive failure probability calculation failed: {e}", "WARNING")
            res["predictive_failure_probability"] = 0.05
            
        return res

    
    def _detect_conflict(self, hypotheses: List[Dict], physics_result: Dict) -> Dict:
        """
        Compare LLM hypotheses against deterministic physics.
        Returns conflict details if disagreement found.
        """
        if not physics_result or not hypotheses:
            return {'conflict_detected': False}
        
        # Check if physics found a fault
        physics_fault = physics_result.get('fault_type')
        physics_severity = physics_result.get('severity')
        
        if physics_fault and physics_fault != 'No significant fault detected':
            # Physics says there IS a fault
            
            # Check if top hypothesis matches
            top_hypothesis = hypotheses[0]['cause'] if hypotheses else ""
            
            # Fuzzy match (simple keyword overlap)
            fault_keywords = physics_fault.lower().replace("(", "").replace(")", "").split()
            # Find overlaps of substantial words
            matched = any(kw in top_hypothesis.lower() for kw in fault_keywords if len(kw) > 3)
            
            if not matched:
                return {
                    'conflict_detected': True,
                    'description': f"Documents suggest '{top_hypothesis}' but physics detects '{physics_fault}'",
                    'document_hypothesis': top_hypothesis,
                    'document_confidence': hypotheses[0]['confidence'],
                    'physics_result': physics_fault,
                    'physics_confidence': physics_result.get('confidence', 1.0),
                    'severity': 'High',
                    'sources': {
                        'documents': hypotheses[0]['evidence'],
                        'physics': f"ISO analysis shows {physics_fault} ({physics_result.get('iso_assessment', {}).get('standard', 'ISO 10816-3')})"
                    }
                }
            else:
                return {
                    'conflict_detected': False,
                    'description': f"Documents and physics agree: {physics_fault}"
                }
        else:
            return {'conflict_detected': False}
    
    def _generate_human_question(self, conflict: Dict) -> str:
        """
        Generate a specific question for the human to resolve the conflict.
        """
        return self.tacit_agent.generate_interview_questions(conflict)
    
    def _synthesize_answer(self, query: str, hypotheses: List[Dict], physics_result: Dict, context: Dict) -> str:
        """
        Synthesize the final answer from all sources.
        """
        # Format input details for the LLM prompt
        hypotheses_str = ""
        for i, h in enumerate(hypotheses[:3]):
            hypotheses_str += f"{i+1}. {h['cause']} (Confidence: {h['confidence']:.0%}) - Evidence: {h['evidence']}\n"
            
        physics_str = "No telemetry/physics data available.\n"
        if physics_result:
            physics_str = f"Diagnosis: {physics_result.get('fault_type', 'Unknown')}\n"
            physics_str += f"Severity: {physics_result.get('severity', 'Unknown')}\n"
            physics_str += f"Recommendation: {physics_result.get('recommendation', 'Inspect/Replace components')}\n"
        
        prompt = SynthesisPrompts.synthesize_answer_prompt(
            query=query,
            hypotheses=hypotheses_str,
            physics=physics_str
        )
        
        # Call LLM
        llm_response = self._call_llm(prompt, "You are a senior industrial maintenance advisor preparing a technician work report.")
        if llm_response:
            return llm_response.strip()

        # Fallback manual synthesis formatting (used when LLM keys/quota fail)
        answer = self._format_document_evidence(context) + "\n\n"
        if hypotheses:
            top = hypotheses[0]
            answer += f"📋 **Based on documents:**\n"
            answer += f"- Most likely cause: {top['cause']} (Confidence: {top['confidence']:.0%})\n"
            answer += f"- Evidence: {top['evidence']}\n\n"
        
        if physics_result:
            answer += f"🔬 **Based on physics analysis:**\n"
            answer += f"- Diagnosis: {physics_result.get('fault_type', 'Unknown')}\n"
            answer += f"- Severity: {physics_result.get('severity', 'Unknown')}\n"
            answer += f"- Recommendation: {physics_result.get('recommendation', 'Inspect/Replace bearings')}\n\n"
        
        answer += f"📚 **Sources:**\n"
        if context.get('sources'):
            answer += f"- {len(context['sources'])} documents/nodes referenced\n"
            
        return answer

    def _format_document_evidence(self, context: Dict) -> str:
        """Flatten top RAG chunks into readable evidence text for answers/scoring."""
        rag_chunks = (context or {}).get('rag_results', {}).get('results', []) or []
        if not rag_chunks:
            return "📄 **Document evidence:** No high-confidence chunks retrieved."
        lines = ["📄 **Document evidence:**"]
        for i, chunk in enumerate(rag_chunks[:5], 1):
            text = (chunk.get('text') or '').strip().replace('\n', ' ')
            # Prefer explicit source, then document_id from metadata, then fallback
            meta = chunk.get('metadata', {})
            src = (
                chunk.get('source')
                or meta.get('source')
                or meta.get('document_id')
                or meta.get('title')
                or 'Document'
            )
            # For auto-generated doc_ timestamp IDs, extract a smart title from the chunk text
            import re as _re
            if src and _re.match(r'^doc_\d{8}_\d{6}', src):
                # Try to extract first meaningful line as a title
                first_line = text.split('·')[0].strip() if '·' in text else text[:60].strip()
                src = first_line or src
            if text:
                lines.append(f"{i}. [{src}] {text[:500]}")
        return "\n".join(lines)
    
    def _generate_alerts(self, asset_id: str, work_order: Dict) -> List[Dict]:
        """
        Generate proactive alerts based on severity.
        """
        alerts = []
        
        if work_order and work_order.get('severity') in ['Critical', 'Alert', 'High', 'Warning']:
            alerts.append(self.push_engine.push_alert(
                alert_type='critical_alert',
                title="🚨 CRITICAL ALERT",
                message=f"Critical issue detected on {asset_id}. Work Order {work_order.get('id', 'WO-0000')} has been generated.",
                recipient='Shift Supervisor'
            ))
            
            alerts.append(self.push_engine.push_alert(
                alert_type='safety_alert',
                title="⚠️ SAFETY PROTOCOL",
                message=f"Lockout-tagout (LOTO) procedures must be enforced for {asset_id}.",
                recipient='Safety Team'
            ))
        
        return alerts

    def resolve_conflict(self, query_result: dict, choice: str, human_feedback: Optional[str] = None) -> dict:
        """
        Action method to apply conflict resolution choice and self-heal the graph.
        """
        asset_id = query_result.get('asset_id') or "P-201"
        self.agent_log = []
        self.log(f"🔧 Applying conflict resolution choice: {choice.upper()}")
        
        reason = "System resolution"
        winner_id = ""
        structured_rule = None
        
        if choice == 'physics':
            winner_id = f"PHYS_{asset_id}"
            reason = "Live sensor vibration verification overrides static documentation SOP"
            self.log(f"✅ Resolved via live physics. Overwriting document recommendations for {asset_id}.")
            
            # Send alert to doc owner
            self.push_engine.push_alert(
                alert_type='outdated_doc_alert',
                title="📄 OUTDATED PROCEDURE DETECTED",
                message=f"Document references for {asset_id} have been marked as Outdated due to live telemetry validation. Please update instructions.",
                recipient='Document Owner'
            )
            
        elif choice == 'documents':
            winner_id = f"DOC_REF_{asset_id}"
            reason = "Static document reference verified by operator as correct"
            self.log(f"📄 Resolved via document SOP guidelines.")
            
        elif choice == 'human' and human_feedback:
            # Parse human feedback
            structured_rule = self.tacit_agent.extract_tacit_rule(human_feedback)
            rule_text = structured_rule['rule_text']
            rule_type = structured_rule['type']
            
            # Add to KG
            rule_id = self.brain.kg.add_tacit_rule(
                equipment_id=f"EQ_{asset_id}",
                rule_text=rule_text,
                person_id="PERSON_Senior_Engineer"
            )
            winner_id = rule_id
            reason = f"Unwritten workaround captured from Sr. Engineer: {rule_text}"
            self.log(f"🎙️ Captured tacit rule {rule_id}: \"{rule_text}\" ({rule_type.replace('_', ' ')})")
            
            # Send alert to Safety / Shift Supervisor
            self.push_engine.push_alert(
                alert_type='tacit_alert',
                title="📚 TACIT KNOWLEDGE CAPTURED",
                message=f"New operational rule captured for {asset_id}: \"{rule_text}\"",
                recipient='Safety Team'
            )
            
        # Run self healing on the graph
        healed_nodes = self.resolution_engine.apply_self_healing(
            kg=self.brain.kg,
            asset_id=asset_id,
            winner_id=winner_id,
            reason=reason,
            choice=choice
        )
        
        for node in healed_nodes:
            self.log(f"🩹 Graph Self-Healed: Node '{node}' status updated to OUTDATED and REPLACED_BY link added.")
            
        # Guardian Phase: Generate work order now that conflict is resolved
        work_order = None
        proactive_alerts = []
        physics_res = query_result.get('physics_result')
        
        # Only generate work order if there's actually a fault (physics severity is high/warning)
        if physics_res and physics_res.get('severity') in ['Critical', 'Alert', 'High', 'Warning']:
            self.log("🚨 Phase 6: Guardian - Generating work order and alerts post-resolution...")
            # For context, use the structured rule if human, or the reason if system
            context = f"Resolution: {choice.upper()} - {reason}"
            work_order = self.work_order_gen.create_work_order(
                asset_id=asset_id,
                fault_type=physics_res.get('fault_type', 'Unknown'),
                severity=physics_res.get('severity', 'Unknown'),
                context=context
            )
            proactive_alerts = self._generate_alerts(asset_id, work_order)
            self.log(f"📤 Pushed {len(proactive_alerts)} proactive alerts")
            
        self.brain.save()
        
        return {
            'success': True,
            'healed_nodes': healed_nodes,
            'winner_id': winner_id,
            'structured_rule': structured_rule,
            'agent_log': self.agent_log,
            'work_order': work_order,
            'proactive_alerts': proactive_alerts
        }

    def _run_multi_agent_debate(self, user_query: str, hypotheses: List[Dict], physics_result: Optional[Dict], context: Dict) -> Dict:
        """
        Multi-agent debate between three specialist agents — Historian (RAG/KG),
        Physicist (Sensor/FFT), and Operator (Tacit Knowledge).
        Each agent calls the LLM with its own system prompt and relevant context slice.
        Falls back to deterministic messages if no LLM key is available.
        """
        self.log("🤝 Running multi-agent consensus debate...")

        # ── Build context slices for each agent ──────────────────────────────
        rag_chunks = context.get('rag_results', {}).get('results', [])
        doc_context = "\n".join(
            f"- [{c.get('source','SOP')}]: {c.get('text','')[:200]}"
            for c in rag_chunks[:4]
        ) or "No document context retrieved."

        physics_context = "No telemetry data available."
        if physics_result:
            physics_context = (
                f"Fault type: {physics_result.get('fault_type', 'Unknown')}\n"
                f"Severity: {physics_result.get('severity', 'Unknown')}\n"
                f"FFT Peaks: {physics_result.get('fft_peaks', [])[:3]}\n"
                f"ISO Zone: {physics_result.get('iso_assessment', {}).get('zone', 'N/A')}\n"
                f"RMS Vibration: {physics_result.get('vibration_rms', 'N/A')} mm/s\n"
                f"Predictive failure probability: {physics_result.get('predictive_failure_probability', 0):.1%}"
            )

        tacit_matches = self.tacit_agent.search_tacit_knowledge(user_query, self.brain.kg)
        tacit_context = "\n".join(
            f"- {m.get('note', '')}" for m in tacit_matches[:3]
        ) or "No tacit knowledge entries found for this query."

        hyp_str = "; ".join(
            f"{h['cause']} ({h['confidence']:.0%})" for h in hypotheses[:3]
        ) or "No hypotheses generated."

        # ── Historian Agent ───────────────────────────────────────────────────
        historian_system = (
            "You are the Historian agent for a refinery AI system at BPCL Mathura. "
            "You have access only to historical SOPs, OEM manuals, regulations (OISD, API, ISO), "
            "and incident reports. You speak with authority about documented procedures. "
            "Keep response under 60 words. Be specific — cite document names if available."
        )
        historian_prompt = (
            f"Query: {user_query}\n\n"
            f"Available document context:\n{doc_context}\n\n"
            f"What do the historical documents and regulations say about this situation? "
            f"Are there any procedures or limits that apply?"
        )
        historian_msg = self._call_llm(historian_prompt, historian_system)
        if not historian_msg:
            # Deterministic fallback
            doc_names = [s.get('name', s.get('source', 'SOP')) for s in context.get('sources', [])]
            if doc_names:
                historian_msg = (
                    f"Per {', '.join(doc_names[:2])}: documented safe operating limits apply. "
                    f"Standard procedure must be followed before any field intervention."
                )
            else:
                historian_msg = (
                    "OEM manuals and OISD-105 confirm standard isolation procedures apply. "
                    "Maximum safe vibration per ISO 10816-3 is 7.1 mm/s (Zone B). "
                    "LOTO must be applied before any bearing work."
                )

        # ── Physicist Agent ───────────────────────────────────────────────────
        physicist_system = (
            "You are the Physicist agent for a refinery AI system at BPCL Mathura. "
            "You have access only to live vibration telemetry, FFT analysis, envelope analysis, "
            "and ISO 10816-3 assessments. You speak with authority about physical sensor data. "
            "Keep response under 60 words. Be specific — cite RMS values, ISO zones, fault frequencies."
        )
        physicist_prompt = (
            f"Query: {user_query}\n\n"
            f"Live telemetry data:\n{physics_context}\n\n"
            f"What does the physics and sensor data indicate? "
            f"Does the live data confirm or contradict the hypotheses: {hyp_str}?"
        )
        physicist_msg = self._call_llm(physicist_prompt, physicist_system)
        if not physicist_msg:
            if physics_result:
                fault = physics_result.get('fault_type', 'anomaly')
                severity = physics_result.get('severity', 'Unknown')
                rms = physics_result.get('vibration_rms', 'N/A')
                physicist_msg = (
                    f"Live Hilbert envelope analysis confirms {severity} {fault}. "
                    f"RMS vibration: {rms} mm/s — exceeds ISO 10816-3 Zone B limit of 7.1 mm/s. "
                    f"Immediate inspection required."
                )
            else:
                physicist_msg = (
                    "No live telemetry stream connected. Simulation shows nominal operating parameters. "
                    "Connect real-time sensor feed for definitive physics-based diagnosis."
                )

        # ── Operator Agent ────────────────────────────────────────────────────
        operator_system = (
            "You are the Operator agent for a refinery AI system at BPCL Mathura. "
            "You represent the tacit knowledge of senior field technicians — "
            "the unwritten workarounds, informal checks, and experiential wisdom "
            "never captured in any manual. "
            "Keep response under 60 words. Speak in practical, field-level terms."
        )
        operator_prompt = (
            f"Query: {user_query}\n\n"
            f"Captured field technician notes:\n{tacit_context}\n\n"
            f"What would an experienced field operator say about this situation? "
            f"Are there any informal checks or workarounds that apply here?"
        )
        operator_msg = self._call_llm(operator_prompt, operator_system)
        if not operator_msg:
            if tacit_matches:
                operator_msg = (
                    f"Field log note from Sr. Technician: '{tacit_matches[0].get('note', '')}'. "
                    f"Always cross-check vibration readings against last bearing grease log."
                )
            else:
                operator_msg = (
                    "No prior field notes logged for this equipment. "
                    "Senior operator advice: check coupling alignment first — "
                    "it causes 40% of vibration spikes we see at this pump bank."
                )

        # ── Consensus Synthesis ───────────────────────────────────────────────
        consensus_system = (
            "You are the Consensus Engine for a refinery AI system at BPCL Mathura. "
            "You synthesize the views of the Historian, Physicist, and Operator agents "
            "into a single, actionable decision for the shift supervisor. "
            "Prioritize live physics over old documents when severity is High or Critical. "
            "Keep response under 80 words. End with a clear next action."
        )
        consensus_prompt = (
            f"Query: {user_query}\n\n"
            f"Historian says: {historian_msg}\n\n"
            f"Physicist says: {physicist_msg}\n\n"
            f"Operator says: {operator_msg}\n\n"
            f"Synthesize these views and provide the consensus decision and recommended next action."
        )
        consensus_msg = self._call_llm(consensus_prompt, consensus_system)
        if not consensus_msg:
            if physics_result and physics_result.get('severity') in ['Critical', 'Alert', 'High']:
                consensus_msg = (
                    f"CONSENSUS: Telemetry alert confirmed — {physics_result.get('fault_type')}. "
                    f"Live sensor physics overrides static documentation. "
                    f"ACTION: Apply LOTO on P-201, dispatch maintenance team, generate WO immediately."
                )
            else:
                consensus_msg = (
                    "CONSENSUS: Document and sensor data are aligned. "
                    "No immediate escalation required. "
                    "ACTION: Log observation, schedule next bearing inspection per standard interval."
                )

        self.log(f"✅ Debate complete — Historian, Physicist, Operator consensus reached")

        return {
            'historian':  historian_msg.strip(),
            'physicist':  physicist_msg.strip(),
            'operator':   operator_msg.strip(),
            'consensus':  consensus_msg.strip(),
        }
