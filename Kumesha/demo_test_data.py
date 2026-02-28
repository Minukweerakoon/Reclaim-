"""
Quick Test Data Generator
=========================

Generates sample test data for the demo
"""

SAMPLE_SCENARIOS = {
    "perfect_match": {
        "text": "Silver iPhone 13 Pro with blue protective case, lost at main university library yesterday evening around 6 PM",
        "item_type": "iPhone",
        "color": "silver",
        "location": "library",
        "time": "evening"
    },
    
    "color_mismatch": {
        "text": "Brown leather handbag with two side pockets",
        "reality": "Black handbag in image",
        "triggers": "XAI Color Mismatch explanation"
    },
    
    "brand_mismatch": {
        "text": "Apple iPhone 13 Pro",
        "image_shows": "Samsung Galaxy phone",
        "triggers": "XAI Brand Mismatch explanation"
    },
    
    "unusual_context": {
        "text": "Umbrella lost at gym at midnight",
        "plausibility": "LOW (23%)",
        "triggers": "Spatial-temporal warning"
    },
    
    "incomplete_description": {
        "text": "lost my phone",
        "missing": ["color", "brand", "location", "time"],
        "triggers": "Low completeness score, clarification questions"
    }
}

GEMINI_CHAT_FLOW = [
    {
        "user": "Hi, I lost my phone",
        "bot_extracts": {"intention": "lost"},
        "bot_asks": "What kind of phone?"
    },
    {
        "user": "It's a silver iPhone 13 Pro with a blue case",
        "bot_extracts": {
            "item_type": "iPhone",
            "color": "silver",
            "brand": "Apple"
        },
        "bot_asks": "Where did you last see it?"
    },
    {
        "user": "I think I left it at the library yesterday evening",
        "bot_extracts": {
            "location": "library",
            "time": "yesterday evening"
        },
        "triggers": "Spatial-temporal validation (HIGH plausibility)"
    }
]

API_ENDPOINTS = {
    "chat": "/api/chat/message",
    "spatial_temporal": "/api/validate/context",
    "text_validation": "/validate/text",
    "image_validation": "/validate/image",
    "voice_validation": "/validate/voice",
    "complete_validation": "/validate/complete",
    "feedback": "/api/feedback/submit"
}

EXPECTED_RESULTS = {
    "high_plausibility": {
        "iPhone + library + evening": 0.85,
        "laptop + classroom + afternoon": 0.82,
        "wallet + cafeteria + noon": 0.78
    },
    
    "low_plausibility": {
        "umbrella + gym + midnight": 0.23,
        "textbook + parking + night": 0.31
    },
    
    "xai_triggers": {
        "color": "brown vs black",
        "brand": "Apple vs Samsung",
        "condition": "new vs poor quality image"
    }
}
