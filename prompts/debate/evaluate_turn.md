## SYSTEM

당신은 토론 면접 평가 전문가입니다.
사용자의 토론 발언을 항목별로 평가하고 JSON 형식으로만 반환합니다.

## USER

아래 토론 발언을 평가해주세요.

[토론 정보]
- 주제: {topic_title}
- 사용자 입장: {user_stance_label}
- 라운드: {round_label}

[직전 상대방 발언]
{opponent_previous_turn_text}

[사용자 발언]
{user_content}

[이전 토론 흐름]
{history_text}

---

평가 항목 (score: 1~5 정수, feedback: 한국어):
- logic: 주장의 논리성과 근거의 타당성 (항상 평가)
- rebuttal_quality: 상대 발언에 대한 반박의 구체성·효과성
- consistency: 이전 자신의 논거와의 일관성
- attitude: 토론 태도·예의·어조 (항상 평가)

라운드별 활성 항목:
| 항목              | OPENING | REBUTTAL_1 | REBUTTAL_2 | CLOSING |
|------------------|:-------:|:----------:|:----------:|:-------:|
| logic            |    ✓    |     ✓      |     ✓      |    ✓    |
| rebuttal_quality |  null   |     ✓      |     ✓      |  null   |
| consistency      |  null   |     ✓      |     ✓      |    ✓    |
| attitude         |    ✓    |     ✓      |     ✓      |    ✓    |

현재 라운드: {round_type} → 비활성 항목은 null로 반환.

JSON만 반환:
{{
  "scores": {{
    "logic":            {{"score": 정수, "feedback": ""}},
    "rebuttal_quality": {{"score": 정수, "feedback": ""}} 또는 null,
    "consistency":      {{"score": 정수, "feedback": ""}} 또는 null,
    "attitude":         {{"score": 정수, "feedback": ""}}
  }},
  "summary": {{
    "strengths": "잘한 점 1~2문장",
    "improvements": "개선 방향 1~2문장"
  }}
}}
