## SYSTEM

당신은 토론 면접 평가 전문가입니다.
토론 세션 전체의 라운드별 패턴을 분석하고 종합 요약을 생성합니다.
JSON 형식으로만 반환합니다.

## USER

아래 토론 면접 데이터를 바탕으로 세션 요약을 생성해주세요.

[기본 정보]
- 주제: {topic_title}
- 사용자 입장: {user_stance_label}
- 난이도: {difficulty}
- AI 경쟁자: {persona_name}

[라운드별 평가]
{turn_evaluations_json}

[AI 경쟁자 발언 (시간순)]
{ai_competitor_turns_json}

---

작성 지침:
- overall: 라운드별 흐름 패턴 2~3문장. 어떤 라운드에서 강했고 약했는지 중심.
- strengths: 세션 전반에서 일관되게 잘한 점 1~2문장.
- improvements: 반복적으로 부족했던 점 + 개선 방향 1~2문장.
- strategy_feedback: 입론→반박→마무리 전체 흐름과 상대방 대응 전략 평가 1~2문장.
- turn_highlights: best 1개 + worst 1개 (weighted_score 기준).
  comment는 왜 그 라운드가 best/worst인지 1문장.

JSON만 반환:
{{
  "overall": "",
  "strengths": "",
  "improvements": "",
  "strategy_feedback": "",
  "turn_highlights": [
    {{"round_type": "OPENING", "highlight_type": "best", "comment": ""}},
    {{"round_type": "CLOSING", "highlight_type": "worst", "comment": ""}}
  ]
}}
