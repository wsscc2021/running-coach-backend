import json
import anthropic
from flask import current_app

_SYSTEM_PROMPT = """당신은 전문 러닝 코치입니다. 러너의 운동 세션 데이터를 분석하여 자연스럽고 격려적인 한국어 피드백을 제공합니다.

피드백 작성 규칙:
- 전체 운동 평가 → 심박수 분석 → 발 압력/균형 분석 → 위험 징후 및 개선 권고 순서로 3-5개 단락 작성
- 수치는 단독 나열 대신 자연스러운 문장에 녹여서 표현
- 긍정적인 부분을 먼저 언급한 뒤 개선점 제안
- 위험(risks) 항목이 있을 경우 반드시 언급하고 구체적인 조언 제공
- 데이터가 없는 항목(available: false)은 언급하지 않음
- 전문적이되 친근하고 동기 부여가 되는 어조 사용"""


def generate_feedback(session_analysis: dict) -> str:
    client = anthropic.Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])

    analysis_json = json.dumps(session_analysis, ensure_ascii=False, indent=2)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"다음 러닝 세션 분석 결과를 바탕으로 코칭 피드백을 작성해주세요:\n\n{analysis_json}",
            }
        ],
    )

    return response.content[0].text
