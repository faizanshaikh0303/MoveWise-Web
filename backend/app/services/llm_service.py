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
        user_preferences: Dict[str, Any] = None,
        overall_scores: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive lifestyle analysis using real data from:
        - FBI Crime Data Explorer API (crime data)
        - HowLoud SoundScore / Google Places + OpenStreetMap (noise modeling)
        - Static 2024 cost of living data (cost)
        """
        
        # Build context prompt with real data
        prompt = self._build_analysis_prompt(
            current_address,
            destination_address,
            crime_data,
            amenities_data,
            cost_data,
            noise_data,
            commute_data,
            user_preferences,
            overall_scores
        )
        
        try:
            # Call Groq API
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """You are a relocation expert helping people make informed decisions about moving. 

You have access to REAL data from authoritative sources:
- FBI Crime Data Explorer: state-level crime rates with temporal analysis
- HowLoud SoundScore API / Google Places + OpenStreetMap: calibrated noise modeling
- Static 2024 cost of living data: city and state-level estimates

Provide clear, data-driven insights with a friendly, personalized tone. Focus on actionable recommendations based on the user's specific schedule, preferences, and the real data provided."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=2500
            )
            
            analysis_text = chat_completion.choices[0].message.content
            
            # Extract structured insights
            return self._parse_llm_response(analysis_text)
            
        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "overview_summary": "Analysis temporarily unavailable. Please check the detailed data tabs for comprehensive information.",
                "lifestyle_changes": [],
                "ai_insights": str(e),
                "action_steps": []
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
        user_preferences: Dict[str, Any] = None,
        overall_scores: Dict[str, Any] = None
    ) -> str:
        """Build comprehensive prompt with real data"""
        
        # Extract data safely
        current_crime = crime_data.get('current', {})
        dest_crime = crime_data.get('destination', {})
        crime_comp = crime_data.get('comparison', {})
        
        current_noise = noise_data.get('current', {})
        dest_noise = noise_data.get('destination', {})
        noise_comp = noise_data.get('comparison', {})
        
        current_cost = cost_data.get('current', {})
        dest_cost = cost_data.get('destination', {})
        cost_comp = cost_data.get('comparison', {})
        
        dest_amenities = amenities_data.get('destination', {})
        
        prompt = f"""Analyze the lifestyle impact of moving from {current_address} to {destination_address}.

═══════════════════════════════════════════════════════════════
REAL CRIME DATA (FBI Crime Data Explorer - State-level, 2025)
═══════════════════════════════════════════════════════════════

CURRENT LOCATION:
• Total Crimes: {current_crime.get('total_crimes', 0)} crimes in 30 days
• Daily Average: {current_crime.get('daily_average', 0)} crimes/day
• Safety Score: {current_crime.get('safety_score', 0)}/100
• Crime Rate: {current_crime.get('crime_rate_per_100k', 0)}/100k population

Crime Types:
• Violent: {current_crime.get('categories', {}).get('violent', 0)}
• Property: {current_crime.get('categories', {}).get('property', 0)}
• Larceny: {current_crime.get('categories', {}).get('larceny', 0)}
• Burglary: {current_crime.get('categories', {}).get('burglary', 0)}

Temporal Analysis:
• During Sleep Hours (10PM-6AM): {current_crime.get('temporal_analysis', {}).get('crimes_during_sleep_hours', 0)} crimes
• During Work Hours (9AM-5PM): {current_crime.get('temporal_analysis', {}).get('crimes_during_work_hours', 0)} crimes
• During Commute: {current_crime.get('temporal_analysis', {}).get('crimes_during_commute', 0)} crimes
• Peak Crime Hours: {current_crime.get('temporal_analysis', {}).get('peak_hours', [])}

DESTINATION LOCATION:
• Total Crimes: {dest_crime.get('total_crimes', 0)} crimes in 30 days
• Daily Average: {dest_crime.get('daily_average', 0)} crimes/day
• Safety Score: {dest_crime.get('safety_score', 0)}/100
• Crime Rate: {dest_crime.get('crime_rate_per_100k', 0)}/100k population

Crime Types:
• Violent: {dest_crime.get('categories', {}).get('violent', 0)}
• Property: {dest_crime.get('categories', {}).get('property', 0)}
• Larceny: {dest_crime.get('categories', {}).get('larceny', 0)}
• Burglary: {dest_crime.get('categories', {}).get('burglary', 0)}

Temporal Analysis:
• During Sleep Hours (10PM-6AM): {dest_crime.get('temporal_analysis', {}).get('crimes_during_sleep_hours', 0)} crimes
• During Work Hours (9AM-5PM): {dest_crime.get('temporal_analysis', {}).get('crimes_during_work_hours', 0)} crimes
• During Commute: {dest_crime.get('temporal_analysis', {}).get('crimes_during_commute', 0)} crimes
• Peak Crime Hours: {dest_crime.get('temporal_analysis', {}).get('peak_hours', [])}

COMPARISON:
• Crime Difference: {crime_comp.get('crime_difference', 0):+d} crimes/month
• Safety Score Change: {crime_comp.get('score_difference', 0):+.1f} points
• Assessment: {crime_comp.get('recommendation', 'Review crime patterns')}

═══════════════════════════════════════════════════════════════
REAL NOISE DATA (HowLoud SoundScore / Google Places + OpenStreetMap)
═══════════════════════════════════════════════════════════════

CURRENT LOCATION:
• Estimated Noise: {current_noise.get('estimated_db', 0):.1f} dB
• Category: {current_noise.get('noise_category', 'Unknown')}
• Noise Score: {current_noise.get('noise_score', 0)}/100
• Description: {current_noise.get('description', '')}

DESTINATION LOCATION:
• Estimated Noise: {dest_noise.get('estimated_db', 0):.1f} dB
• Category: {dest_noise.get('noise_category', 'Unknown')}
• Noise Score: {dest_noise.get('noise_score', 0)}/100
• Description: {dest_noise.get('description', '')}

COMPARISON:
• dB Difference: {noise_comp.get('db_difference', 0):+.1f} dB
• Description: {noise_comp.get('recommendation', 'Similar')}
• User Preference: {user_preferences.get('noise_preference', 'moderate') if user_preferences else 'moderate'}
• Match Quality: {noise_comp.get('preference_match', {}).get('quality', 'fair')}
• Recommendation: {noise_comp.get('recommendation', 'Review noise levels')}

═══════════════════════════════════════════════════════════════
REAL COST DATA (Static 2024 Cost of Living Estimates)
═══════════════════════════════════════════════════════════════

CURRENT LOCATION:
• Total Monthly: ${current_cost.get('total_monthly', 0):,.2f}
• Total Annual: ${current_cost.get('total_annual', 0):,.2f}
• Affordability Score: {current_cost.get('affordability_score', 0)}/100
• Cost Index: {current_cost.get('cost_index', 1.0)}

Breakdown:
• Housing: ${current_cost.get('housing', {}).get('monthly_rent', 0):,.2f}/month
• Utilities: ${current_cost.get('expenses', {}).get('utilities', 0):,.2f}
• Groceries: ${current_cost.get('expenses', {}).get('groceries', 0):,.2f}
• Transportation: ${current_cost.get('expenses', {}).get('transportation', 0):,.2f}
• Healthcare: ${current_cost.get('expenses', {}).get('healthcare', 0):,.2f}
• Entertainment: ${current_cost.get('expenses', {}).get('entertainment', 0):,.2f}

DESTINATION LOCATION:
• Total Monthly: ${dest_cost.get('total_monthly', 0):,.2f}
• Total Annual: ${dest_cost.get('total_annual', 0):,.2f}
• Affordability Score: {dest_cost.get('affordability_score', 0)}/100
• Cost Index: {dest_cost.get('cost_index', 1.0)}

Breakdown:
• Housing: ${dest_cost.get('housing', {}).get('monthly_rent', 0):,.2f}/month
• Utilities: ${dest_cost.get('expenses', {}).get('utilities', 0):,.2f}
• Groceries: ${dest_cost.get('expenses', {}).get('groceries', 0):,.2f}
• Transportation: ${dest_cost.get('expenses', {}).get('transportation', 0):,.2f}
• Healthcare: ${dest_cost.get('expenses', {}).get('healthcare', 0):,.2f}
• Entertainment: ${dest_cost.get('expenses', {}).get('entertainment', 0):,.2f}

COMPARISON:
• Monthly Difference: ${cost_comp.get('monthly_difference', 0):+,.2f}
• Annual Difference: ${cost_comp.get('annual_difference', 0):+,.2f}
• Percent Change: {cost_comp.get('percent_change', 0):+.1f}%
• Assessment: {cost_comp.get('recommendation', 'Review costs')}

═══════════════════════════════════════════════════════════════
AMENITIES & LIFESTYLE
═══════════════════════════════════════════════════════════════

Destination Amenities:
• Total Count: {dest_amenities.get('total_count', 0)}

By Type:
"""
        
        # Add amenity breakdown
        for amenity_type, count in dest_amenities.get('by_type', {}).items():
            prompt += f"• {amenity_type.title()}: {count}\n"
        
        prompt += f"""
═══════════════════════════════════════════════════════════════
COMMUTE INFORMATION
═══════════════════════════════════════════════════════════════

• Duration: {commute_data.get('duration_minutes', 0)} minutes
• Distance: {commute_data.get('distance', 'Unknown')}
• Method: {commute_data.get('method', 'driving').title()}
"""

        if user_preferences:
            prompt += f"""
═══════════════════════════════════════════════════════════════
USER PREFERENCES & SCHEDULE
═══════════════════════════════════════════════════════════════

• Work Schedule: {user_preferences.get('work_hours', 'Not specified')}
• Sleep Schedule: {user_preferences.get('sleep_hours', 'Not specified')}
• Noise Tolerance: {user_preferences.get('noise_preference', 'moderate').title()}
• Hobbies/Interests: {', '.join(user_preferences.get('hobbies', ['None specified']))}
"""

        if overall_scores:
            prompt += f"""
═══════════════════════════════════════════════════════════════
OVERALL SCORES (Weighted Composite)
═══════════════════════════════════════════════════════════════

Overall Score: {overall_scores.get('overall_score', 0)}/100 (Grade: {overall_scores.get('grade', 'N/A')})

Component Scores:
• Safety: {overall_scores.get('component_scores', {}).get('safety', {}).get('score', 0)}/100 (30% weight)
• Affordability: {overall_scores.get('component_scores', {}).get('affordability', {}).get('score', 0)}/100 (25% weight)
• Environment: {overall_scores.get('component_scores', {}).get('environment', {}).get('score', 0)}/100 (20% weight)
• Lifestyle: {overall_scores.get('component_scores', {}).get('lifestyle', {}).get('score', 0)}/100 (15% weight)
• Convenience: {overall_scores.get('component_scores', {}).get('convenience', {}).get('score', 0)}/100 (10% weight)

Strengths: {', '.join(overall_scores.get('strengths', []))}
Concerns: {', '.join([c['area'] for c in overall_scores.get('concerns', [])])}
"""

        prompt += """
═══════════════════════════════════════════════════════════════
INSTRUCTIONS
═══════════════════════════════════════════════════════════════

Based on this REAL DATA, provide:

1. OVERVIEW (2-3 sentences)
   - Summarize the most important changes
   - Highlight key data points
   - Set the tone (positive, cautious, mixed)

2. LIFESTYLE CHANGES (exactly 6 bullet points with ✓)
   - Sleep quality (reference crime data during sleep hours + noise levels)
   - Amenities access (reference actual amenity counts)
   - Dining/entertainment (reference data)
   - Safety (reference specific crime numbers and trends)
   - Commute (reference actual time)
   - Cost (reference actual dollar amounts)
   - Be SPECIFIC with data points, not generic

3. DETAILED INSIGHTS (3-4 paragraphs)
   - Deep dive into the most significant changes
   - Reference specific numbers from the data
   - Explain what the data means for daily life
   - Consider user's schedule and preferences
   - Provide context and interpretation
   - End with encouraging guidance

4. PERSONALIZED ACTION STEPS (5-7 specific actions)
   - Based on the ACTUAL data provided
   - Address any concerns identified
   - Suggest specific next steps
   - Include visit times based on crime peak hours
   - Budget planning with actual dollar amounts
   - Security measures if crime during sleep hours is high
   - Noise mitigation if needed
   - Be concrete and actionable, not generic

Format EXACTLY as:
---OVERVIEW---
[2-3 sentence summary]

---LIFESTYLE_CHANGES---
✓ [Change 1 with specific data]
✓ [Change 2 with specific data]
✓ [Change 3 with specific data]
✓ [Change 4 with specific data]
✓ [Change 5 with specific data]
✓ [Change 6 with specific data]

---INSIGHTS---
[3-4 detailed paragraphs with data interpretation]

---ACTION_STEPS---
→ [Step 1: Specific action]
→ [Step 2: Specific action]
→ [Step 3: Specific action]
→ [Step 4: Specific action]
→ [Step 5: Specific action]
"""
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse structured LLM response"""
        
        try:
            parts = response_text.split("---")
            
            overview = ""
            lifestyle_changes = []
            insights = ""
            action_steps = []
            
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
                    insights_text = parts[i + 1].strip() if i + 1 < len(parts) else ""
                    # Stop at ACTION_STEPS if present
                    if "---ACTION_STEPS---" in insights_text:
                        insights = insights_text.split("---ACTION_STEPS---")[0].strip()
                    else:
                        insights = insights_text
                elif "ACTION_STEPS" in part:
                    steps_text = parts[i + 1].strip() if i + 1 < len(parts) else ""
                    action_steps = [
                        line.strip() for line in steps_text.split("\n")
                        if line.strip() and ("→" in line or "•" in line or line.startswith("-") or line.startswith("1"))
                    ]
            
            return {
                "overview_summary": overview or "Analysis generated successfully.",
                "lifestyle_changes": lifestyle_changes[:6],  # Max 6 items
                "ai_insights": insights or response_text,
                "action_steps": action_steps[:7]  # Max 7 steps
            }
            
        except Exception as e:
            print(f"Parse error: {e}")
            return {
                "overview_summary": "Analysis generated successfully.",
                "lifestyle_changes": [],
                "ai_insights": response_text,
                "action_steps": []
            }


llm_service = LLMService()