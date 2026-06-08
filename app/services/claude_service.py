import json
import anthropic
from anthropic import APIStatusError
from flask import current_app

_SYSTEM_PROMPT = """당신은 전문 러닝 코치입니다. 러너의 운동 세션 데이터를 분석하여 자연스럽고 격려적인 한국어 피드백을 제공합니다.

피드백 작성 규칙:
- 전체 운동 평가 → 심박수 분석 → 발 압력/균형 분석 → 위험 징후 및 개선 권고 순서로 3-5개 단락 작성
- 수치는 단독 나열 대신 자연스러운 문장에 녹여서 표현
- 긍정적인 부분을 먼저 언급한 뒤 개선점 제안
- 위험(risks) 항목이 있을 경우 반드시 언급하고 구체적인 조언 제공
- 데이터가 없는 항목(available: false)은 언급하지 않음
- 전문적이되 친근하고 동기 부여가 되는 어조 사용
- 반드시 일반 텍스트로만 작성하고, *, **, #, -, > 등 마크다운 기호는 절대 사용하지 않음
- 목록이 필요한 경우 번호(1. 2. 3.)나 쉼표로 연결된 문장으로 대체"""


def generate_feedback(session_analysis: dict) -> str:
    api_key = current_app.config.get("ANTHROPIC_API_KEY") or ""
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다. 백엔드 .env 파일을 확인하세요.")

    client = anthropic.Anthropic(api_key=api_key)

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

    return _strip_markdown(response.content[0].text)


def _strip_markdown(text: str) -> str:
    import re
    text = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)   # *bold*, **bold**, ***bold***
    text = re.sub(r'#{1,6}\s*', '', text)                  # ## 제목
    text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)  # 줄 시작 - * + 목록
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)  # > 인용
    text = re.sub(r'`(.+?)`', r'\1', text)                 # `코드`
    return text.strip()


_API_ERROR_MESSAGES = {
    "credit_balance_too_low":    "Anthropic 크레딧이 부족합니다. console.anthropic.com/settings/billing 에서 충전해 주세요.",
    "authentication_error":      "ANTHROPIC_API_KEY가 유효하지 않습니다. 키를 확인해 주세요.",
    "permission_error":          "API 키에 해당 모델 접근 권한이 없습니다.",
    "rate_limit_error":          "API 요청 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.",
    "overloaded_error":          "Anthropic 서버가 일시적으로 과부하 상태입니다. 잠시 후 재시도해 주세요.",
}


def _friendly_api_error(exc: APIStatusError) -> str:
    body = exc.response.json() if exc.response is not None else {}
    error_type = body.get("error", {}).get("type", "")
    msg = body.get("error", {}).get("message", "")

    for key, friendly in _API_ERROR_MESSAGES.items():
        if key in error_type or key in msg.lower().replace(" ", "_"):
            return friendly

    return f"Claude API 오류 (HTTP {exc.status_code}): {msg or error_type}"
