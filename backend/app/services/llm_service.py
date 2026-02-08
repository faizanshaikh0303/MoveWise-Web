from groq import Groq
from app.core.config import settings
from typing import Dict, Any, List


class LLMService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        
    def generate_lifestyle_analysis(
        self,
        current_address: str,
        destination_address: str,
        crime_data: Dict[str, Any],
        amenities_data: Dict[str, Any],
        cost_data: Dict[str, Any],
        noise_data: Dict[str, Any],
        commute_data: Dict[str, Any],
        user_preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive lifestyle analysis using Groq LLM
        """
        
        # Build context prompt
        prompt = self._build_analysis_prompt(
            current_address,
            destination_address,
            crime_data,
            amenities_data,
            cost_data,
            noise_data,
            commute_data,
            user_preferences
        )
        
        try:
            # Call Groq API
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a relocation expert helping people make informed decisions about moving. Provide clear, data-driven insights with a friendly tone."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",  # Current free model on Groq
                temperature=0.7,
                max_tokens=2000
            )
            
            analysis_text = chat_completion.choices[0].message.content
            
            # Extract structured insights
            return self._parse_llm_response(analysis_text)
            
        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "overview_summary": "Analysis temporarily unavailable. Please check the data tabs for detailed information.",
                "lifestyle_changes": [],
                "ai_insights": str(e)
            }
    
    def _build_analysis_prompt(
        self,
        current_address: str,
        destination_address: str,
        crime_data: Dict[str, Any],
        amenities_data: Dict[str, Any],
        cost_data: Dict[str, Any],
        noise_data: Dict[str, Any],
        commute_data: Dict[str, Any],
        user_preferences: Dict[str, Any] = None
    ) -> str:
        """Build structured prompt for LLM"""
        
        prompt = f"""Analyze the lifestyle impact of moving from {current_address} to {destination_address}.

DATA SUMMARY:

Crime & Safety:
- Current location crime rate: {crime_data.get('current_crime_rate', 'N/A')}
- New location crime rate: {crime_data.get('destination_crime_rate', 'N/A')}

Amenities:
- Current: {amenities_data.get('current_amenities', {})}
- New: {amenities_data.get('destination_amenities', {})}

Cost of Living:
- Current: ${cost_data.get('current_cost', 'N/A')}/month
- New: ${cost_data.get('destination_cost', 'N/A')}/month
- Change: {cost_data.get('change_percentage', 'N/A')}%

Noise Environment:
- Current: {noise_data.get('current_noise_level', 'N/A')}
- New: {noise_data.get('destination_noise_level', 'N/A')}

Commute:
- Duration: {commute_data.get('duration_minutes', 'N/A')} minutes
- Method: {commute_data.get('method', 'N/A')}
"""

        if user_preferences:
            prompt += f"\nUSER PREFERENCES:\n"
            prompt += f"- Work schedule: {user_preferences.get('work_hours', 'N/A')}\n"
            prompt += f"- Sleep schedule: {user_preferences.get('sleep_hours', 'N/A')}\n"
            prompt += f"- Noise tolerance: {user_preferences.get('noise_preference', 'N/A')} (user prefers {user_preferences.get('noise_preference', 'moderate')} environments)\n"
            prompt += f"- Hobbies: {', '.join(user_preferences.get('hobbies', []))}\n"

        prompt += """
Please provide:

1. OVERVIEW (2-3 sentences summarizing the move's impact)

2. LIFESTYLE CHANGES (exactly 6 bullet points, each starting with a check mark emoji ✓):
   - Focus on: sleep quality (considering noise levels vs user preference), amenities access, dining/entertainment, safety, commute, cost
   - Be specific and data-driven
   - IMPORTANT: Compare the noise environment to the user's noise tolerance preference
   - Keep each point concise (1 sentence)

3. DETAILED INSIGHTS (3-4 paragraphs):
   - Expand on the most important changes
   - Provide actionable advice
   - Consider user preferences, especially noise tolerance vs actual noise levels
   - Address whether the noise environment matches the user's preference
   - End with an encouraging note

Format your response EXACTLY as:
---OVERVIEW---
[2-3 sentence summary]

---LIFESTYLE_CHANGES---
✓ [Change 1]
✓ [Change 2]
✓ [Change 3]
✓ [Change 4]
✓ [Change 5]
✓ [Change 6]

---INSIGHTS---
[Detailed analysis paragraphs]
"""
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse structured LLM response"""
        
        try:
            parts = response_text.split("---")
            
            overview = ""
            lifestyle_changes = []
            insights = ""
            
            for i, part in enumerate(parts):
                part = part.strip()
                
                if "OVERVIEW" in part:
                    overview = parts[i + 1].strip() if i + 1 < len(parts) else ""
                elif "LIFESTYLE_CHANGES" in part:
                    changes_text = parts[i + 1].strip() if i + 1 < len(parts) else ""
                    lifestyle_changes = [
                        line.strip() for line in changes_text.split("\n")
                        if line.strip() and ("✓" in line or "•" in line or line.startswith("-"))
                    ]
                elif "INSIGHTS" in part:
                    insights = parts[i + 1].strip() if i + 1 < len(parts) else ""
            
            return {
                "overview_summary": overview or "Analysis generated successfully.",
                "lifestyle_changes": lifestyle_changes[:6],  # Max 6 items
                "ai_insights": insights or response_text
            }
            
        except Exception as e:
            print(f"Parse error: {e}")
            return {
                "overview_summary": "Analysis generated successfully.",
                "lifestyle_changes": [],
                "ai_insights": response_text
            }


llm_service = LLMService()
