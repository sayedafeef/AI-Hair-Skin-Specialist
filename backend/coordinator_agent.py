import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

ROUTER_MODEL = os.environ.get("GROQ_ROUTER_MODEL", "openai/gpt-oss-20b")

ROUTER_SYSTEM_PROMPT = (
    "You are a triage assistant for a telehealth app with two specialists: "
    "a skin specialist (dermatology - rashes, acne, moles, eczema, psoriasis, "
    "skin infections, discoloration) and a hair specialist (trichology - hair "
    "loss, scalp conditions, dandruff, alopecia, hair thinning, scalp itching). "
    "Given the patient's description, decide which specialist should handle "
    "this case. Respond with ONLY valid JSON matching this schema: "
    '{"specialty": "skin" | "hair"}. If the concern could reasonably involve '
    "both (e.g. scalp psoriasis), choose the specialist most central to the "
    "primary complaint."
)


def classify_concern(patient_text):
    """Uses a lightweight Groq text model to route a patient's concern to
    either the skin or hair specialist agent, independent of which frontend
    page the request originated from. Defaults to 'skin' on any parsing
    failure so the pipeline never breaks on a routing hiccup."""
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is missing from environment variables.")

    client = Groq(api_key=groq_api_key)

    response = client.chat.completions.create(
        model=ROUTER_MODEL,
        messages=[
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Patient description: {patient_text}"},
        ],
        temperature=0,
        max_tokens=300,
        reasoning_effort="low",
        reasoning_format="hidden",
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "routing_decision",
                "schema": {
                    "type": "object",
                    "properties": {
                        "specialty": {"type": "string", "enum": ["skin", "hair"]},
                    },
                    "required": ["specialty"],
                    "additionalProperties": False,
                },
            },
        },
    )

    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
        specialty = parsed.get("specialty", "skin")
    except (json.JSONDecodeError, TypeError, AttributeError):
        specialty = "skin"

    return specialty if specialty in ("skin", "hair") else "skin"
