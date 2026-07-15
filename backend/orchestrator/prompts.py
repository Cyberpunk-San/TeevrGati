class HypothesisPrompts:
    """
    Prompt templates for generating diagnostic hypotheses.
    """
    
    @staticmethod
    def generate_hypotheses_prompt(query: str, context: str, asset_id: str) -> str:
        return f"""
You are an industrial maintenance expert analyzing a problem with equipment.

**Equipment:** {asset_id}
**Question:** {query}

**Context from documents and knowledge graph:**
{context}

**Task:** Generate 3 possible causes for the problem, ranked by likelihood.

Format your response as JSON:
{{
    "hypotheses": [
        {{
            "cause": "Brief cause description",
            "confidence": 0.85,
            "evidence": "Specific evidence from context that supports this"
        }}
    ]
}}

If you're uncertain, assign lower confidence scores. Never exceed 0.95 confidence unless you have direct evidence.

**Important:** If the context doesn't contain enough information, set confidence scores appropriately low and note the gaps.
"""


class SynthesisPrompts:
    """
    Prompt templates for synthesizing final diagnostic answers.
    """
    
    @staticmethod
    def synthesize_answer_prompt(query: str, hypotheses: str, physics: str) -> str:
        return f"""
You are synthesizing a response for an industrial technician.

**Original Question:** {query}

**Document-based hypotheses:**
{hypotheses}

**Physics analysis result:**
{physics}

**Task:** Write a clear, actionable response for the technician. Include:
1. What the likely problem is
2. What evidence supports this
3. Recommended next steps
4. Any safety considerations

Format: Use clear sections with bullet points. Keep it under 200 words.
"""
