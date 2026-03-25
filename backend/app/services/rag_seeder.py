"""Idempotent seeder for the RAG knowledge base.

Chunks are written at help-center level — plain language only.
No internal API names, no backend terminology, no implementation details.
"""
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict

from sqlalchemy.orm import Session

from app.models.doc_chunk import DocChunk
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

# ── Knowledge base ────────────────────────────────────────────────────────────
# All content is user-facing. No internal API names, service names, or backend
# terminology. Think help-center article, not developer documentation.

CHUNKS: List[Dict] = [

    # ── NAVIGATION ────────────────────────────────────────────────────────────

    {
        "chunk_key": "nav_getting_started",
        "section": "navigation",
        "title": "Getting Started with MoveWise",
        "content": (
            "Welcome to MoveWise! Here's how to get started:\n\n"
            "1. Create your account or log in.\n"
            "2. Complete your Profile Setup. This is a short 3-step wizard that asks about "
            "your work schedule, sleep habits, and hobbies. Your profile helps us personalize "
            "every analysis to your lifestyle.\n"
            "3. Once your profile is set up, click 'New Analysis' from the navigation bar or "
            "the Dashboard.\n"
            "4. Enter your current address and the destination address you're considering moving to.\n"
            "5. Click 'Analyze' and return to the Dashboard. Your analysis will be ready in "
            "about 15–45 seconds.\n"
            "6. Click any analysis card on the Dashboard to see the full report with scores, "
            "detailed tabs, and AI-generated insights."
        ),
    },
    {
        "chunk_key": "nav_dashboard",
        "section": "navigation",
        "title": "The Dashboard",
        "content": (
            "The Dashboard is your home base in MoveWise. It shows:\n\n"
            "- Your most recent analyses (up to 10), displayed as cards.\n"
            "- Each card shows the origin and destination addresses, the overall score and grade, "
            "and the current status (Pending, Processing, Completed, or Failed).\n"
            "- Summary stats at the top: total analyses run, date of your last report, and how "
            "many unique destinations you've explored.\n"
            "- A chat widget in the bottom corner where you can ask MoveWise AI questions.\n\n"
            "Click any completed analysis card to open the full detail report. "
            "Use the 'New Analysis' button to start a new comparison."
        ),
    },
    {
        "chunk_key": "nav_new_analysis",
        "section": "navigation",
        "title": "Starting a New Analysis",
        "content": (
            "To start a new analysis:\n\n"
            "1. Click 'New Analysis' in the navigation bar or on the Dashboard.\n"
            "2. In the 'Current Address' field, type your current home address. "
            "Start typing and suggestions will appear — select the correct one.\n"
            "3. In the 'Destination Address' field, type the address of the location "
            "you're considering moving to. Again, use the autocomplete suggestions.\n"
            "4. Click the 'Analyze' button.\n\n"
            "You'll be taken back to the Dashboard immediately. Your new analysis will "
            "appear as a card with a 'Pending' or 'Processing' status. It typically "
            "completes in 15–45 seconds and the status updates automatically — you don't "
            "need to refresh the page."
        ),
    },
    {
        "chunk_key": "nav_profile_setup",
        "section": "navigation",
        "title": "Profile Setup Wizard",
        "content": (
            "The Profile Setup wizard appears the first time you log in after creating your account. "
            "It has three steps:\n\n"
            "Step 1 — Work Schedule: Enter your typical work hours, your work address, "
            "and how you prefer to commute (driving, transit, bicycling, or walking). "
            "If you work from home, check the 'Work from Home' box instead of entering an address.\n\n"
            "Step 2 — Sleep & Environment: Enter your typical sleep hours and choose your "
            "noise preference (Quiet, Moderate, or Lively).\n\n"
            "Step 3 — Hobbies & Interests: Select the activities you enjoy from the list "
            "(gym, hiking, parks, restaurants, coffee shops, bars, movies, shopping, library, sports). "
            "Pick as many as apply.\n\n"
            "Your profile is used to personalize the analysis scores — especially the "
            "Lifestyle and Convenience scores. You can update it anytime from Profile Settings."
        ),
    },
    {
        "chunk_key": "nav_profile_settings",
        "section": "navigation",
        "title": "Profile Settings Page",
        "content": (
            "The Profile Settings page lets you update your preferences after the initial setup. "
            "To get there, click your name or avatar in the top-right corner and select "
            "'Profile Settings', or navigate directly from the menu.\n\n"
            "The page has two tabs:\n\n"
            "Profile Information — Edit your work schedule, work address, commute preference, "
            "sleep hours, noise preference, and hobbies. Click 'Save Changes' when done. "
            "The Save button is only active when you've made a change.\n\n"
            "Change Password — Enter your current password, then your new password twice. "
            "Click 'Change Password' to update it."
        ),
    },
    {
        "chunk_key": "nav_analysis_detail",
        "section": "navigation",
        "title": "Analysis Detail Page",
        "content": (
            "The Analysis Detail page shows the full report for one analysis. "
            "To open it, click any completed analysis card on the Dashboard.\n\n"
            "At the top, you'll see the origin and destination addresses, the overall "
            "score, and the letter grade.\n\n"
            "Below that are six tabs:\n"
            "- Overview: A summary of all five category scores and an AI-written narrative.\n"
            "- Safety: Crime and safety data for the destination area.\n"
            "- Cost: A breakdown of cost-of-living differences between your current and destination locations.\n"
            "- Noise: Noise level data and how it matches your noise preference.\n"
            "- Lifestyle: How many places matching your hobbies are nearby.\n"
            "- Commute: Estimated commute time from the destination to your work address.\n\n"
            "If the analysis is still processing, you'll see a loading indicator. "
            "The page updates automatically when it's ready."
        ),
    },
    {
        "chunk_key": "nav_general_tips",
        "section": "navigation",
        "title": "General Navigation Tips",
        "content": (
            "Here are some quick tips for navigating MoveWise:\n\n"
            "- The navigation bar at the top gives you access to Dashboard, New Analysis, "
            "and Profile Settings from anywhere in the app.\n"
            "- Your analyses are always saved. You can come back and review them anytime "
            "from the Dashboard.\n"
            "- The chat widget (bottom-right of the Dashboard) can answer questions about "
            "your analyses, compare destinations, or explain any score or field.\n"
            "- To log out, use the menu in the top-right corner.\n"
            "- If an analysis shows 'Failed', it means something went wrong during processing. "
            "You can create a new analysis with the same addresses to try again."
        ),
    },

    # ── SCORES ────────────────────────────────────────────────────────────────

    {
        "chunk_key": "score_safety",
        "section": "scores",
        "title": "Safety Score",
        "content": (
            "The Safety Score (0–100) measures how safe the destination area is based on "
            "local crime statistics compared to national averages.\n\n"
            "A higher score means a safer area. The score reflects the overall crime rate "
            "in the destination area — including both violent and property crime.\n\n"
            "Score ranges:\n"
            "- 80–100: Excellent — significantly safer than average\n"
            "- 70–79: Good — safer than average\n"
            "- 60–69: Fair — near average\n"
            "- 50–59: Needs Attention — somewhat higher crime than average\n"
            "- Below 50: Concerning — notably higher crime rate\n\n"
            "The Safety Score is one of the most heavily weighted factors in the Overall Score."
        ),
    },
    {
        "chunk_key": "score_affordability",
        "section": "scores",
        "title": "Affordability Score",
        "content": (
            "The Affordability Score (0–100) reflects how the cost of living at the destination "
            "compares to your current location.\n\n"
            "A higher score means the destination is more affordable relative to where you live now. "
            "If the destination is cheaper than your current location, your score will be high. "
            "If it's more expensive, your score will be lower.\n\n"
            "The score takes into account typical expenses such as housing, groceries, utilities, "
            "transportation, healthcare, and entertainment.\n\n"
            "Score ranges:\n"
            "- 80–100: Excellent — noticeably cheaper than your current location\n"
            "- 70–79: Good — similar or slightly cheaper\n"
            "- 60–69: Fair — somewhat more expensive\n"
            "- 50–59: Needs Attention — meaningfully more expensive\n"
            "- Below 50: Concerning — significantly more expensive\n\n"
            "Affordability is one of the most heavily weighted factors in the Overall Score."
        ),
    },
    {
        "chunk_key": "score_noise",
        "section": "scores",
        "title": "Noise / Environment Score",
        "content": (
            "The Noise Score (0–100) measures how quiet or loud the destination area is "
            "and how well that matches your noise preference.\n\n"
            "A higher score means the area is closer to your preferred noise level. "
            "If you prefer a quiet environment and the destination is quiet, your score will be high. "
            "If you prefer a lively atmosphere, louder areas will score better for you.\n\n"
            "Score ranges:\n"
            "- 80–100: Excellent — closely matches your noise preference\n"
            "- 70–79: Good — reasonably close to your preference\n"
            "- 60–69: Fair — moderate match\n"
            "- 50–59: Needs Attention — some mismatch with your preference\n"
            "- Below 50: Concerning — significant mismatch\n\n"
            "You can update your noise preference (Quiet, Moderate, or Lively) in Profile Settings."
        ),
    },
    {
        "chunk_key": "score_lifestyle",
        "section": "scores",
        "title": "Lifestyle Score",
        "content": (
            "The Lifestyle Score (0–100) measures how well the destination matches your "
            "hobbies and interests based on nearby places and amenities.\n\n"
            "We look for places matching the hobbies you selected in your profile — "
            "such as gyms, parks, restaurants, coffee shops, and more — and check how many "
            "are available near the destination address.\n\n"
            "A higher score means more of your preferred amenities are nearby.\n\n"
            "Score ranges:\n"
            "- 80–100: Excellent — great match for your interests\n"
            "- 70–79: Good — most of your preferred amenities are nearby\n"
            "- 60–69: Fair — decent selection\n"
            "- 50–59: Needs Attention — limited options for your interests\n"
            "- Below 50: Concerning — few amenities matching your hobbies\n\n"
            "Update your hobbies in Profile Settings to personalize this score."
        ),
    },
    {
        "chunk_key": "score_convenience",
        "section": "scores",
        "title": "Convenience / Commute Score",
        "content": (
            "The Convenience Score (0–100) measures how convenient your daily commute "
            "to work would be from the destination address.\n\n"
            "It's based on the estimated travel time from the destination to your work address, "
            "using your preferred commute method (driving, transit, bicycling, or walking).\n\n"
            "A shorter commute means a higher score. If you work from home, your Convenience "
            "Score is automatically set to the maximum since there's no commute.\n\n"
            "Score ranges:\n"
            "- 80–100: Excellent — very short or no commute\n"
            "- 70–79: Good — manageable commute\n"
            "- 60–69: Fair — moderate commute time\n"
            "- 50–59: Needs Attention — longer than average\n"
            "- Below 50: Concerning — very long commute\n\n"
            "Update your work address and commute preference in Profile Settings."
        ),
    },
    {
        "chunk_key": "score_overall",
        "section": "scores",
        "title": "Overall Score and Grade",
        "content": (
            "The Overall Score (0–100) is a combined measure across all five analysis categories: "
            "Safety, Affordability, Noise/Environment, Lifestyle, and Convenience.\n\n"
            "Safety and Affordability are the most heavily weighted factors. "
            "Environment is weighted moderately. Lifestyle and Convenience have lighter but "
            "meaningful weight.\n\n"
            "The Overall Score is converted to a letter grade:\n"
            "- A+ (90–100): Outstanding\n"
            "- A (85–89): Excellent\n"
            "- A- (80–84): Very Good\n"
            "- B+ (75–79): Good\n"
            "- B (70–74): Above Average\n"
            "- B- (65–69): Average\n"
            "- C+ (60–64): Below Average\n"
            "- C (55–59): Fair\n"
            "- C- (50–54): Needs Improvement\n"
            "- D (below 50): Challenging\n\n"
            "Use the Overall Score to quickly compare destinations at a glance, then dive "
            "into individual tabs for the full picture."
        ),
    },
    {
        "chunk_key": "score_status_labels",
        "section": "scores",
        "title": "Score Status Labels",
        "content": (
            "Each individual score (Safety, Affordability, Noise, Lifestyle, Convenience) "
            "is labeled with a status to help you quickly understand it:\n\n"
            "- Excellent: Score 80 or above — this is a strong point for the destination.\n"
            "- Good: Score 70–79 — performing well.\n"
            "- Fair: Score 60–69 — acceptable, with some room for improvement.\n"
            "- Needs Attention: Score 50–59 — worth considering before deciding.\n"
            "- Concerning: Score below 50 — this area may be a significant drawback.\n\n"
            "Strengths are categories scoring 75 or above. "
            "Areas of concern are categories scoring below 60. "
            "These are highlighted in the Overview tab of your analysis."
        ),
    },

    # ── PROFILE FIELDS ────────────────────────────────────────────────────────

    {
        "chunk_key": "field_work_hours",
        "section": "fields_profile",
        "title": "Work Hours",
        "content": (
            "The Work Hours fields let you set your typical start and end time for the workday "
            "(for example, 9:00 AM to 5:00 PM).\n\n"
            "Why it matters: Your work hours are used when analyzing how crime patterns in your "
            "destination area overlap with the times you're likely commuting or at home. "
            "This helps give you a more accurate picture of how safe the destination feels "
            "during your daily routine.\n\n"
            "You can set these in the Profile Setup wizard (Step 1) or update them at any time "
            "in Profile Settings under the Profile Information tab."
        ),
    },
    {
        "chunk_key": "field_work_address",
        "section": "fields_profile",
        "title": "Work Address",
        "content": (
            "The Work Address field is where you enter the address of your workplace.\n\n"
            "Why it matters: MoveWise uses your work address to calculate how long your commute "
            "would be from each destination you analyze. This directly affects the Convenience Score.\n\n"
            "Type your work address and select the correct suggestion from the autocomplete dropdown. "
            "If you work from home, check the 'Work from Home' toggle instead — you don't need "
            "to enter an address.\n\n"
            "You can update your work address in Profile Settings under the Profile Information tab."
        ),
    },
    {
        "chunk_key": "field_work_from_home",
        "section": "fields_profile",
        "title": "Work From Home Toggle",
        "content": (
            "The 'Work from Home' toggle lets you indicate that you don't commute to a physical office.\n\n"
            "When this is turned on:\n"
            "- You don't need to enter a work address.\n"
            "- Your Convenience Score for every analysis will automatically be set to the maximum, "
            "since there's no commute to factor in.\n\n"
            "When this is turned off:\n"
            "- You'll need to provide a work address.\n"
            "- Your Convenience Score will be calculated based on the estimated commute time "
            "from each destination to your work address.\n\n"
            "You can change this setting anytime in Profile Settings."
        ),
    },
    {
        "chunk_key": "field_commute_preference",
        "section": "fields_profile",
        "title": "Commute Preference",
        "content": (
            "The Commute Preference setting lets you choose how you typically travel to work. "
            "There are four options:\n\n"
            "- Driving: Commute time is calculated by car.\n"
            "- Transit: Commute time is calculated using public transportation.\n"
            "- Bicycling: Commute time is calculated by bike.\n"
            "- Walking: Commute time is calculated on foot.\n\n"
            "Why it matters: When MoveWise calculates your Convenience Score for a destination, "
            "it estimates travel time to your work address using whichever mode you've selected. "
            "Choose the one that best reflects how you'd actually get to work.\n\n"
            "You can update your commute preference in Profile Settings under the Profile Information tab."
        ),
    },
    {
        "chunk_key": "field_sleep_noise",
        "section": "fields_profile",
        "title": "Sleep Hours and Noise Preference",
        "content": (
            "Sleep Hours: Set your typical bedtime and wake-up time "
            "(for example, 11:00 PM to 7:00 AM). "
            "This helps contextualize noise data — we look at how active or quiet the "
            "destination area tends to be during the hours you sleep.\n\n"
            "Noise Preference: Choose the kind of environment you prefer:\n"
            "- Quiet: You prefer peaceful, low-noise surroundings.\n"
            "- Moderate: You're comfortable with some ambient noise.\n"
            "- Lively: You enjoy an energetic, active atmosphere.\n\n"
            "Your noise preference directly affects the Noise Score. A destination that "
            "matches your preference will score higher. "
            "Both settings can be updated in Profile Settings under the Profile Information tab."
        ),
    },
    {
        "chunk_key": "field_hobbies",
        "section": "fields_profile",
        "title": "Hobbies and Interests",
        "content": (
            "The Hobbies section lets you select the activities and interests that matter most "
            "to you. MoveWise uses this to look for nearby places that match your lifestyle "
            "when scoring a destination.\n\n"
            "Available options:\n"
            "- Gym: Fitness centers and health clubs nearby.\n"
            "- Hiking: Access to trails and nature paths.\n"
            "- Parks: Green spaces and public parks.\n"
            "- Restaurants: Dining options in the area.\n"
            "- Coffee: Coffee shops and cafés.\n"
            "- Bars: Bars and nightlife venues.\n"
            "- Movies: Cinemas and movie theaters.\n"
            "- Shopping: Retail stores and shopping centers.\n"
            "- Library: Public libraries.\n"
            "- Sports: Sports venues, courts, and stadiums.\n\n"
            "Select as many as apply. The more hobbies you select, the more tailored "
            "your Lifestyle Score will be. Update your selections anytime in Profile Settings."
        ),
    },

    # ── ANALYSIS FIELDS ───────────────────────────────────────────────────────

    {
        "chunk_key": "field_current_address",
        "section": "fields_analysis",
        "title": "Current Address",
        "content": (
            "The Current Address field is where you enter the address you currently live at.\n\n"
            "Why it matters: Your current address is the baseline MoveWise uses for comparisons. "
            "Cost differences, for example, are calculated relative to your current location — "
            "so the Affordability Score tells you whether the destination is cheaper or more "
            "expensive than where you live now.\n\n"
            "Tips:\n"
            "- Use a specific street address rather than just a city or zip code for the most "
            "accurate results.\n"
            "- Start typing and select from the autocomplete suggestions that appear.\n\n"
            "This field appears on the New Analysis page when you start a new analysis."
        ),
    },
    {
        "chunk_key": "field_destination_address",
        "section": "fields_analysis",
        "title": "Destination Address",
        "content": (
            "The Destination Address field is where you enter the address of the location "
            "you're considering moving to.\n\n"
            "MoveWise analyzes this address across five dimensions: safety, cost of living, "
            "noise levels, nearby amenities, and commute time.\n\n"
            "Tips:\n"
            "- Use a specific street address for the most accurate results.\n"
            "- If you're exploring a neighborhood rather than a specific home, you can enter "
            "a representative address in that area.\n"
            "- Use the autocomplete suggestions to ensure the address is recognized correctly.\n\n"
            "You can run multiple analyses with different destination addresses to compare "
            "several options side by side."
        ),
    },
    {
        "chunk_key": "field_analysis_tabs",
        "section": "fields_analysis",
        "title": "Analysis Report Tabs",
        "content": (
            "The full analysis report is organized into six tabs:\n\n"
            "Overview: A high-level summary showing all five scores at a glance, "
            "identified strengths and concerns, and an AI-written narrative summarizing "
            "what the move would mean for your lifestyle.\n\n"
            "Safety: Detailed information about crime and safety in the destination area, "
            "including how it compares to your current location and national averages.\n\n"
            "Cost: A side-by-side comparison of estimated monthly and annual expenses "
            "between your current and destination locations, broken down by category "
            "(housing, groceries, utilities, transportation, healthcare, entertainment).\n\n"
            "Noise: Information about the noise level in the destination area and how it "
            "aligns with your noise preference.\n\n"
            "Lifestyle: A look at what amenities and places matching your hobbies are "
            "available near the destination.\n\n"
            "Commute: Your estimated commute time from the destination to your work address, "
            "shown for all four travel modes (driving, transit, bicycling, walking)."
        ),
    },
    {
        "chunk_key": "field_ai_insights",
        "section": "fields_analysis",
        "title": "AI Insights Section",
        "content": (
            "The AI Insights section appears in the Overview tab of each completed analysis. "
            "It contains three parts:\n\n"
            "Summary: A written narrative explaining what the move would mean for your "
            "day-to-day life, considering all five analysis dimensions together.\n\n"
            "Lifestyle Changes: A list of specific changes you'd likely experience — "
            "for example, a shorter commute, quieter surroundings, or more dining options nearby.\n\n"
            "Action Steps: Practical suggestions for next steps based on the analysis results "
            "— such as things to research further before making a decision.\n\n"
            "These insights are generated automatically based on the analysis data and your "
            "profile preferences. They're meant to help you interpret the numbers in plain language."
        ),
    },
    {
        "chunk_key": "field_what_is_analyzed",
        "section": "fields_analysis",
        "title": "What Gets Analyzed",
        "content": (
            "When you run an analysis on a destination, MoveWise examines five key areas:\n\n"
            "1. Safety: Local crime rates and how safe the area is compared to your current "
            "location and national averages.\n\n"
            "2. Cost of Living: A comparison of typical monthly expenses — housing, groceries, "
            "utilities, transportation, healthcare, and entertainment — between your current "
            "and destination locations.\n\n"
            "3. Noise Levels: How quiet or loud the destination area tends to be and how that "
            "matches your noise preference.\n\n"
            "4. Nearby Amenities: How many places matching your hobbies and interests "
            "(gyms, parks, restaurants, etc.) are located near the destination.\n\n"
            "5. Commute: How long it would take you to get to work from the destination, "
            "using your preferred mode of transportation.\n\n"
            "Each area produces a score from 0 to 100, which are combined into the Overall Score."
        ),
    },

    # ── FAQ ───────────────────────────────────────────────────────────────────

    {
        "chunk_key": "faq_how_long",
        "section": "faq",
        "title": "How Long Does an Analysis Take?",
        "content": (
            "After you submit a new analysis, it typically takes 15–45 seconds to complete.\n\n"
            "While it's running, the analysis card on your Dashboard will show a 'Pending' or "
            "'Processing' status. The status updates automatically — you don't need to refresh "
            "the page.\n\n"
            "Once the analysis is done, the card will update to 'Completed' and you can click "
            "it to view the full report.\n\n"
            "If something goes wrong, the card will show 'Failed'. In that case, you can try "
            "creating a new analysis with the same addresses."
        ),
    },
    {
        "chunk_key": "faq_update_profile",
        "section": "faq",
        "title": "Can I Update My Profile After Setup?",
        "content": (
            "Yes! You can update your profile at any time.\n\n"
            "Go to Profile Settings (click your name or avatar in the top-right corner, "
            "then select 'Profile Settings'). Under the 'Profile Information' tab, you can "
            "edit your work schedule, work address, commute preference, sleep hours, noise "
            "preference, and hobbies.\n\n"
            "Click 'Save Changes' when you're done. The button will only be active after "
            "you've made at least one change.\n\n"
            "Note: Profile changes apply to new analyses only. Analyses you've already run "
            "were calculated using your profile at the time they were created."
        ),
    },
    {
        "chunk_key": "faq_rerun_analysis",
        "section": "faq",
        "title": "Can I Rerun an Analysis?",
        "content": (
            "There is no 'Rerun' button for existing analyses. If you want a fresh analysis "
            "for the same pair of addresses — for example, after updating your profile — "
            "simply create a new analysis with the same current and destination addresses.\n\n"
            "Go to 'New Analysis', enter the same addresses, and click 'Analyze'. "
            "The new analysis will reflect your current profile settings and the latest data."
        ),
    },
    {
        "chunk_key": "faq_multiple_analyses",
        "section": "faq",
        "title": "Can I Have Multiple Analyses?",
        "content": (
            "Yes, you can run as many analyses as you like. Your Dashboard shows your 10 most "
            "recent analyses.\n\n"
            "Running multiple analyses for different destination addresses is a great way to "
            "compare several options side by side. You can also ask the MoveWise AI chat to "
            "compare your analyses, rank them by any factor, or highlight the best option "
            "for your priorities."
        ),
    },
    {
        "chunk_key": "faq_password_change",
        "section": "faq",
        "title": "How to Change My Password",
        "content": (
            "To change your password:\n\n"
            "1. Go to Profile Settings (click your name or avatar in the top-right, "
            "then 'Profile Settings').\n"
            "2. Click the 'Change Password' tab.\n"
            "3. Enter your current password in the first field.\n"
            "4. Enter your new password in the second field.\n"
            "5. Enter your new password again in the third field to confirm.\n"
            "6. Click 'Change Password'.\n\n"
            "Your password must be at least 6 characters long. "
            "If you've forgotten your current password, please contact support."
        ),
    },
]


# ── Seeder ────────────────────────────────────────────────────────────────────

def _hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def seed_knowledge_base(db: Session) -> None:
    """Idempotently seed doc_chunks. Skips unchanged chunks, re-embeds updated ones."""
    current_keys = {c["chunk_key"] for c in CHUNKS}
    seeded = updated = skipped = 0

    # Batch-embed all new/changed chunks in one API call
    chunks_needing_embed = []
    for chunk in CHUNKS:
        new_hash = _hash(chunk["content"])
        row = db.query(DocChunk).filter(DocChunk.chunk_key == chunk["chunk_key"]).first()
        if row is None or row.content_hash != new_hash:
            chunks_needing_embed.append((chunk, new_hash, row))
        else:
            skipped += 1

    if chunks_needing_embed:
        texts = [c["content"] for c, _, _ in chunks_needing_embed]
        embeddings = embedding_service.embed_texts(texts)

        for i, (chunk, new_hash, row) in enumerate(chunks_needing_embed):
            vec = embeddings[i] if embeddings else None
            now = datetime.now(timezone.utc)

            if row is None:
                db.add(DocChunk(
                    chunk_key=chunk["chunk_key"],
                    section=chunk["section"],
                    title=chunk["title"],
                    content=chunk["content"],
                    embedding=vec,
                    content_hash=new_hash,
                    created_at=now,
                    updated_at=now,
                ))
                seeded += 1
            else:
                row.section = chunk["section"]
                row.title = chunk["title"]
                row.content = chunk["content"]
                row.embedding = vec
                row.content_hash = new_hash
                row.updated_at = now
                updated += 1

        db.commit()

    # Remove retired chunks
    deleted = db.query(DocChunk).filter(DocChunk.chunk_key.notin_(current_keys)).delete(synchronize_session=False)
    if deleted:
        db.commit()

    logger.info(
        "[RAG] Knowledge base seed complete: %d inserted, %d updated, %d skipped, %d deleted",
        seeded, updated, skipped, deleted,
    )
