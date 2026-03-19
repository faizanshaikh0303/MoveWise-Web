"""Dashboard-level AI chat agent with tool calling (Groq + llama-3.3-70b)."""
from groq import Groq
from app.core.config import settings
from typing import List, Dict, Any
import json


# ── Tool definitions (Groq / OpenAI-compatible function calling) ──────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_analysis_details",
            "description": (
                "Fetch the full data for one specific move analysis — crime, cost, "
                "noise, commute, amenities, and all scores. Use this when the user "
                "asks about a specific destination in detail."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis_id": {
                        "type": "integer",
                        "description": "The ID of the analysis to retrieve.",
                    }
                },
                "required": ["analysis_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_analyses",
            "description": (
                "Compare two or more analyses side by side. Use this when the user "
                "wants to pit destinations against each other."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of analysis IDs to compare.",
                    },
                    "focus": {
                        "type": "string",
                        "enum": ["overall", "financial", "safety", "lifestyle", "commute"],
                        "description": "Which aspect to focus the comparison on.",
                    },
                },
                "required": ["analysis_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rank_analyses",
            "description": (
                "Rank all of the user's analyses by a specific priority. Use this "
                "when the user asks 'which move is best for X' without specifying "
                "particular destinations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "priority": {
                        "type": "string",
                        "enum": [
                            "safety", "affordability", "noise",
                            "lifestyle", "commute", "overall",
                        ],
                        "description": "The criterion to rank analyses by.",
                    }
                },
                "required": ["priority"],
            },
        },
    },
]


class ChatService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    # ── System prompt ─────────────────────────────────────────────────────────

    def _build_system_prompt(self, analyses_summary: List[Dict]) -> str:
        if not analyses_summary:
            return (
                "You are MoveWise AI, a financial and relocation advisor. "
                "The user has not run any analyses yet. "
                "Encourage them to create their first analysis to get started. "
                "Be friendly and concise."
            )

        rows = "\n".join(
            f"  #{a['id']}: {a['from']} → {a['to']} | "
            f"Score {a['overall_score']}/100 ({a['grade']}) | "
            f"Safety {a['safety']} · Affordability {a['affordability']} · "
            f"Noise {a['noise']} · Commute {a['commute']} min"
            for a in analyses_summary
        )

        return f"""You are MoveWise AI, an intelligent financial and relocation advisor.
You have full access to the user's {len(analyses_summary)} saved move analysis/analyses:

{rows}

Use your tools proactively:
- "Which move saves the most money?" → rank_analyses(priority="affordability")
- "Tell me more about Austin" → get_analysis_details(analysis_id=<id>)
- "Compare Austin and Denver" → compare_analyses(analysis_ids=[...])
- "Which is safest?" → rank_analyses(priority="safety")

Be concise and data-driven. Quote specific numbers when you have them.
Never fabricate data — only use what the tools return."""

    # ── Tool execution ────────────────────────────────────────────────────────

    def _execute_tool(
        self, tool_name: str, tool_args: Dict, analyses_by_id: Dict
    ) -> str:
        if tool_name == "get_analysis_details":
            aid = tool_args.get("analysis_id")
            a = analyses_by_id.get(aid)
            if not a:
                return f"Analysis #{aid} not found."

            cost = a.get("cost_data", {})
            crime = a.get("crime_data", {})
            noise = a.get("noise_data", {})
            commute = a.get("commute_data", {})

            return json.dumps({
                "id": a["id"],
                "from": a["current_address"],
                "to": a["destination_address"],
                "overall_score": a.get("overall_score"),
                "grade": a.get("grade"),
                "safety_score": a.get("safety_score"),
                "affordability_score": a.get("affordability_score"),
                "environment_score": a.get("environment_score"),
                "lifestyle_score": a.get("lifestyle_score"),
                "convenience_score": a.get("convenience_score"),
                "monthly_cost_current": cost.get("current", {}).get("total_monthly"),
                "monthly_cost_destination": cost.get("destination", {}).get("total_monthly"),
                "monthly_difference": cost.get("comparison", {}).get("monthly_difference"),
                "annual_difference": cost.get("comparison", {}).get("annual_difference"),
                "crime_rate_destination": crime.get("destination", {}).get("crime_rate_per_100k"),
                "safety_score_destination": crime.get("destination", {}).get("safety_score"),
                "noise_db": noise.get("destination", {}).get("estimated_db"),
                "noise_category": noise.get("destination", {}).get("noise_category"),
                "commute_minutes": commute.get("duration_minutes"),
                "commute_method": commute.get("method"),
                "overview": a.get("overview_summary", ""),
            }, indent=2)

        if tool_name == "compare_analyses":
            ids = tool_args.get("analysis_ids", [])
            focus = tool_args.get("focus", "overall")
            results = []
            for aid in ids:
                a = analyses_by_id.get(aid)
                if not a:
                    continue
                cost = a.get("cost_data", {})
                results.append({
                    "id": a["id"],
                    "destination": a["destination_address"],
                    "overall_score": a.get("overall_score"),
                    "grade": a.get("grade"),
                    "safety_score": a.get("safety_score"),
                    "affordability_score": a.get("affordability_score"),
                    "environment_score": a.get("environment_score"),
                    "commute_minutes": a.get("commute_data", {}).get("duration_minutes"),
                    "monthly_difference": cost.get("comparison", {}).get("monthly_difference"),
                    "annual_difference": cost.get("comparison", {}).get("annual_difference"),
                })

            key_map = {
                "financial": lambda x: x.get("monthly_difference") or 0,
                "safety": lambda x: -(x.get("safety_score") or 0),
                "commute": lambda x: x.get("commute_minutes") or 999,
                "lifestyle": lambda x: -(x.get("environment_score") or 0),
            }
            results.sort(key=key_map.get(focus, lambda x: -(x.get("overall_score") or 0)))

            return json.dumps({"focus": focus, "comparison": results}, indent=2)

        if tool_name == "rank_analyses":
            priority = tool_args.get("priority", "overall")
            score_key = {
                "safety": "safety_score",
                "affordability": "affordability_score",
                "noise": "environment_score",
                "lifestyle": "lifestyle_score",
                "commute": "convenience_score",
                "overall": "overall_score",
            }.get(priority, "overall_score")

            ranked = sorted(
                analyses_by_id.values(),
                key=lambda a: -(a.get(score_key) or 0),
            )
            return json.dumps({
                "priority": priority,
                "ranking": [
                    {
                        "rank": i + 1,
                        "id": a["id"],
                        "destination": a["destination_address"],
                        "score": a.get(score_key),
                        "overall_score": a.get("overall_score"),
                        "grade": a.get("grade"),
                    }
                    for i, a in enumerate(ranked)
                ],
            }, indent=2)

        return f"Unknown tool: {tool_name}"

    # ── Main agentic loop ─────────────────────────────────────────────────────

    def chat(
        self,
        user_message: str,
        history: List[Dict[str, str]],
        analyses_summary: List[Dict],
        analyses_by_id: Dict[int, Dict],
    ) -> Dict[str, Any]:
        system_prompt = self._build_system_prompt(analyses_summary)

        messages: List[Dict] = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        tool_calls_made: List[Dict] = []

        try:
            # Agentic loop — up to 3 tool-call rounds
            for _ in range(3):
                response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=1000,
                )
                choice = response.choices[0]

                # No tool calls → final answer ready
                if not choice.message.tool_calls:
                    return {
                        "reply": choice.message.content,
                        "tool_calls": tool_calls_made,
                    }

                # Append assistant message with tool_calls
                messages.append({
                    "role": "assistant",
                    "content": choice.message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in choice.message.tool_calls
                    ],
                })

                # Execute tools and feed results back
                for tc in choice.message.tool_calls:
                    args = json.loads(tc.function.arguments)
                    result = self._execute_tool(tc.function.name, args, analyses_by_id)
                    tool_calls_made.append({"tool": tc.function.name, "args": args})
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

            # Exhausted tool rounds — ask for final answer without tools
            final = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )
            return {
                "reply": final.choices[0].message.content,
                "tool_calls": tool_calls_made,
            }

        except Exception as e:
            print(f"Chat agent error: {e}")
            return {
                "reply": "I'm having trouble right now. Please try again.",
                "tool_calls": [],
            }


chat_service = ChatService()
