"""Dashboard-level AI chat agent with tool calling (Groq + llama-3.3-70b)."""
from groq import Groq
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.services.embedding_service import embedding_service
from typing import List, Dict, Any, Optional
import json

RAG_SIMILARITY_THRESHOLD = 0.35  # tune if retrieval is too strict / too loose


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
    {
        "type": "function",
        "function": {
            "name": "search_app_guide",
            "description": (
                "Search the MoveWise user guide to answer how-to, navigation, or "
                "field/score explanation questions. Use this BEFORE answering any "
                "question about how to use the app, navigate pages, set up a profile, "
                "understand what a score means, or interpret any field or result. "
                "Do NOT use this for questions about the user's specific saved analyses."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's question rephrased as a standalone search query.",
                    },
                    "section": {
                        "type": "string",
                        "enum": ["navigation", "scores", "fields_profile", "fields_analysis", "faq"],
                        "description": "Optional: narrow the search to one section when the topic is clear.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_analyses",
            "description": (
                "Filter analyses by current or destination address keywords, then rank "
                "the matches. Use this when the user specifies a location filter like "
                "'analyses from NY', 'moves to Texas', or 'where I'm moving from California'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "current_address_contains": {
                        "type": "string",
                        "description": (
                            "Case-insensitive substring to match against the current "
                            "(origin) address. E.g. 'NY', 'California', 'New York'."
                        ),
                    },
                    "destination_address_contains": {
                        "type": "string",
                        "description": (
                            "Case-insensitive substring to match against the destination "
                            "address. E.g. 'TX', 'Austin', 'Texas'."
                        ),
                    },
                    "priority": {
                        "type": "string",
                        "enum": [
                            "safety", "affordability", "noise",
                            "lifestyle", "commute", "overall",
                        ],
                        "description": "Rank the filtered results by this criterion.",
                    },
                },
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

Tool routing rules:
- Use search_app_guide for ANY how-to, navigation, or explanation question:
  "How do I set up my profile?" → search_app_guide(query="how to set up profile")
  "What does the safety score mean?" → search_app_guide(query="safety score explanation", section="scores")
  "How do I start a new analysis?" → search_app_guide(query="how to start new analysis", section="navigation")
  "What is commute preference?" → search_app_guide(query="commute preference field", section="fields_profile")
- Use analysis tools only for questions about THIS USER's specific saved data:
  "Which move saves the most money?" → rank_analyses(priority="affordability")
  "Tell me more about Austin" → get_analysis_details(analysis_id=<id>)
  "Compare Austin and Denver" → compare_analyses(analysis_ids=[...])
  "Which is safest?" → rank_analyses(priority="safety")

Never fabricate app instructions — always call search_app_guide first for how-to questions.
Never fabricate data — only use what the tools return.
Be concise and data-driven. Quote specific numbers when you have them."""

    # ── Tool execution ────────────────────────────────────────────────────────

    def _execute_tool(
        self, tool_name: str, tool_args: Dict, analyses_by_id: Dict, db: Optional[Session] = None
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

        if tool_name == "filter_analyses":
            current_filter = (tool_args.get("current_address_contains") or "").lower()
            dest_filter = (tool_args.get("destination_address_contains") or "").lower()
            priority = tool_args.get("priority", "overall")

            matches = [
                a for a in analyses_by_id.values()
                if (not current_filter or current_filter in a["current_address"].lower())
                and (not dest_filter or dest_filter in a["destination_address"].lower())
            ]

            if not matches:
                return json.dumps({
                    "filtered": [],
                    "message": (
                        f"No analyses found matching "
                        f"{'current address containing ' + repr(current_filter) if current_filter else ''}"
                        f"{'destination address containing ' + repr(dest_filter) if dest_filter else ''}."
                        " Try a broader keyword."
                    ),
                })

            score_key = {
                "safety": "safety_score",
                "affordability": "affordability_score",
                "noise": "environment_score",
                "lifestyle": "lifestyle_score",
                "commute": "convenience_score",
                "overall": "overall_score",
            }.get(priority, "overall_score")

            matches.sort(key=lambda a: -(a.get(score_key) or 0))

            return json.dumps({
                "filter": {
                    "current_contains": current_filter or None,
                    "destination_contains": dest_filter or None,
                },
                "priority": priority,
                "count": len(matches),
                "ranked": [
                    {
                        "rank": i + 1,
                        "id": a["id"],
                        "from": a["current_address"],
                        "to": a["destination_address"],
                        "overall_score": a.get("overall_score"),
                        "grade": a.get("grade"),
                        score_key: a.get(score_key),
                        "monthly_difference": a.get("cost_data", {})
                            .get("comparison", {}).get("monthly_difference"),
                    }
                    for i, a in enumerate(matches)
                ],
            }, indent=2)

        if tool_name == "search_app_guide":
            query = tool_args.get("query", "")
            section_filter = tool_args.get("section")
            if not query:
                return json.dumps({"found": False, "message": "No query provided."})

            vec = embedding_service.embed_text(query)
            if vec is None:
                return json.dumps({"found": False, "message": "Guide search is temporarily unavailable."})

            sql = text("""
                SELECT chunk_key, section, title, content,
                       1 - (embedding <=> CAST(:qvec AS vector)) AS similarity
                FROM doc_chunks
                WHERE (:section IS NULL OR section = :section)
                ORDER BY embedding <=> CAST(:qvec AS vector)
                LIMIT 4
            """)
            rows = db.execute(sql, {"qvec": str(vec), "section": section_filter}).fetchall()
            results = [
                {"title": r.title, "section": r.section, "content": r.content, "similarity": round(r.similarity, 3)}
                for r in rows
                if r.similarity >= RAG_SIMILARITY_THRESHOLD
            ]
            if not results:
                return json.dumps({"found": False, "message": "No relevant guide content found for that query."})
            return json.dumps({"found": True, "results": results}, indent=2)

        return f"Unknown tool: {tool_name}"

    # ── Main agentic loop ─────────────────────────────────────────────────────

    def chat(
        self,
        user_message: str,
        history: List[Dict[str, str]],
        analyses_summary: List[Dict],
        analyses_by_id: Dict[int, Dict],
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        system_prompt = self._build_system_prompt(analyses_summary)

        messages: List[Dict] = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        tool_calls_made: List[Dict] = []

        try:
            # Agentic loop — up to 5 tool-call rounds for complex queries
            for _ in range(5):
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
                    result = self._execute_tool(tc.function.name, args, analyses_by_id, db)
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
