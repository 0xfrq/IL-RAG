from groq import AsyncGroq
from config import GROQ_MODEL
client = AsyncGroq()
async def generate_text(
    system_prompt: str,
    user_prompt: str,
):
    response = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""