import os

from dotenv import load_dotenv
from groq import Groq

from image_utils import encode_image_to_base64

load_dotenv()

SPECIALIST_PROMPTS = {
    "skin": (
        "You are an expert AI dermatology consultant. Examine the patient's "
        "concerns and provided image/video context carefully. Provide a clear, "
        "empathetic, and professional response outlining potential observations, "
        "recommended skincare, and when to consult a face-to-face dermatologist. "
        "Always respond in English, regardless of the language used in the "
        "patient's description. Respond with only the final consultation text - "
        "do not include any internal reasoning, analysis steps, or <think> tags."
    ),
    "hair": (
        "You are an expert AI trichology (hair and scalp) consultant. Examine "
        "the patient's concerns and provided image/video context carefully. "
        "Provide a clear, empathetic, and professional response outlining "
        "potential observations about hair loss, scalp condition, or hair "
        "health, recommended care, and when to consult a face-to-face "
        "trichologist or dermatologist. Always respond in English, regardless "
        "of the language used in the patient's description. Respond with only "
        "the final consultation text - do not include any internal reasoning, "
        "analysis steps, or <think> tags."
    ),
}


def get_specialist_response(specialty, patient_text, image_filepath=None, video_filepath=None):
    """Generates a specialist consultation response using Groq's vision model.

    `specialty` must be one of the keys in SPECIALIST_PROMPTS ("skin" or "hair").
    """
    if specialty not in SPECIALIST_PROMPTS:
        raise ValueError(f"Unknown specialty: {specialty}")

    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is missing from environment variables.")

    client = Groq(api_key=groq_api_key)

    messages = [{"role": "system", "content": SPECIALIST_PROMPTS[specialty]}]
    user_content = [{"type": "text", "text": f"Patient symptoms description: {patient_text}"}]

    if image_filepath:
        base64_image, mime_type = encode_image_to_base64(image_filepath)
        user_content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
            }
        )

    if video_filepath and not image_filepath:
        user_content.append(
            {"type": "text", "text": "[Note: Patient provided a video file for review.]"}
        )

    messages.append({"role": "user", "content": user_content})

    model_name = os.environ.get("GROQ_VISION_MODEL", "qwen/qwen3.8-27b")

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.3,
        max_tokens=800,
        reasoning_effort="none",
        reasoning_format="hidden",
    )

    return response.choices[0].message.content
