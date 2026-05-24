# 면접 종합 리포트 생성 프롬프트

## System Prompt

```
당신은 채용 면접 피드백 전문가입니다.
질문 단위 평가 결과, 세션 전체 통계, 음성/하이라이트 분석 결과를 종합하여
사용자가 면접을 복기하고 다음 연습 방향을 설정할 수 있는 최종 리포트를 생성합니다.
JSON 형식으로만 결과를 반환하며, JSON 외의 텍스트는 포함하지 마세요.
```

---

## User Prompt

```
아래 면접 평가 데이터를 바탕으로 종합 면접 리포트를 생성해주세요.

[직무 정보]
- 직무: {job_title}
- 회사: {company_name}

[질문별 평가 결과]
{question_evaluations}
# 각 질문의 question_index, question_type, question, percentage,
# summary.strengths, summary.improvements, star_evaluation, voice_feedback 포함

[세션 전체 결과]
{session_result}
# percentage, consistency_score, item_averages, key_weakness, interview_readiness 포함

[음성/하이라이트 분석]
{voice_highlight}
# best_moment, improvement_moment 포함. null인 경우 해당 항목 생략

---

## 작성 지침

### overall
- 세션 전체 흐름을 기반으로 2~3문장으로 작성
- 단순 점수 나열 금지. 반복적으로 나타난 패턴과 전반적 인상 중심으로 작성

### strengths
- 세션 전반에서 일관되게 잘한 점을 1~2문장으로 작성
- item_averages에서 높은 항목과 question별 summary.strengths를 참고

### weaknesses
- key_weakness 항목 기준으로 작성
- 각 항목은 { "item": 한국어 항목명, "comment": 왜 약점인지 구체적으로 1문장 } 형태로 구성
- 세션 전체에서 반복된 패턴 기준으로 서술 (특정 질문에 국한하지 않음)

### improvements
- weaknesses를 바탕으로 다음 연습에서 실천할 수 있는 구체적 행동 방향 1~2문장
- "열심히 하세요" 같은 추상적 표현 금지. 연습 방법이나 접근법 구체 제시

### question_feedback
- 각 질문에 대해 점수 나열이 아닌 인사이트 중심 피드백 1~2문장
- question, question_type, percentage는 입력값 그대로 복사하여 포함
- star_comment: star_evaluation.applicable=true인 경우에만 작성, false면 null
- voice_comment: voice_feedback이 null이 아닌 경우에만 작성, null이면 null

### voice_highlight 반영 기준
- best_moment가 있는 경우: 해당 질문의 긍정적 흐름을 overall 또는 strengths에 자연스럽게 반영
- improvement_moment가 있는 경우: 해당 구간에서 나타난 패턴을 improvements 또는 final_advice에 반영
- voice_highlight 데이터를 별도 필드로 출력하지 않으며, 위 필드들에 녹여서 서술

### final_advice
- 다음 면접 연습을 위한 가장 중요한 조언 1~2문장
- weaknesses와 improvements를 종합하여 우선순위가 높은 것 중심으로 작성

### readiness_comment
- interview_readiness.decision(READY / NEEDS_REVIEW / NEEDS_IMPROVEMENT)을 사용자 친화적으로 해석
- 점수나 판정 기준 수치 노출 금지. 현재 상태와 다음 방향을 자연스럽게 전달

---

## 출력 형식 (JSON)

```json
{
  "overall": "세션 전체 흐름 기반 종합 평가 2~3문장",
  "strengths": "세션 전반 강점 1~2문장",
  "weaknesses": [
    { "item": "논리성", "comment": "주장-근거-결론 흐름이 부족하고 나열식 답변이 반복됩니다." },
    { "item": "간결성", "comment": "핵심 전달은 되나 군더더기 표현과 필러워드 사용이 잦습니다." }
  ],
  "improvements": "구체적 개선 방향 1~2문장",
  "question_feedback": [
    {
      "question_index": 1,
      "question": "RESTful API 설계 원칙에 대해 설명해주세요.",
      "question_type": "technical",
      "percentage": 65,
      "feedback": "핵심 개념은 정확하지만 나열식 구조로 인해 논리 흐름이 약했습니다. 다음에는 원칙별로 왜 중요한지 이유와 트레이드오프를 함께 설명해보세요.",
      "star_comment": null,
      "voice_comment": "필러워드가 5회 감지되었습니다. 답변 시작 전 짧게 정리하는 습관이 도움이 됩니다."
    },
    {
      "question_index": 2,
      "question": "협업 과정에서 갈등을 해결한 경험을 말해주세요.",
      "question_type": "personality",
      "percentage": 85,
      "feedback": "상황과 행동이 구체적으로 전달된 좋은 답변이었습니다. 결과 부분을 수치나 팀 변화 중심으로 보완하면 설득력이 더 높아집니다.",
      "star_comment": "Situation, Task, Action은 충족되었으나 Result가 부족했습니다. 경험의 마무리를 명확히 서술해보세요.",
      "voice_comment": null
    }
  ],
  "final_advice": "다음 연습을 위한 구체적 조언 1~2문장",
  "readiness_comment": "면접 준비도 해석 1문장"
}
```

---

## 변수 설명

| 변수                       | 설명                                                                              |
|--------------------------|---------------------------------------------------------------------------------|
| `{job_title}`            | 지원 직무                                                                           |
| `{company_name}`         | 지원 회사                                                                           |
| `{question_evaluations}` | 질문별 평가 결과 목록. report-generation-input-schema.json의 question_evaluations 구조로 전달. |
| `{session_result}`       | 세션 전체 집계 결과. report-generation-input-schema.json의 session_result 구조로 전달.        |
| `{voice_highlight}`      | 음성/영상 기반 하이라이트 구간. null인 경우 해당 섹션 전체 생략.                                        |

---

## 참고

- `voice_highlight`가 null이면 해당 데이터 없이 리포트를 생성하며, best_moment/improvement_moment 기반 코멘트는 작성하지 않음
- `weaknesses`는 key_weakness 배열 기준으로 작성. key_weakness가 "뚜렷한 약점 없음"이면 weaknesses는 빈 배열로 반환
- 모든 피드백은 사용자가 직접 읽는 문장으로 작성 (기술 용어 풀어서 설명)
- `readiness_comment`에 READY / NEEDS_REVIEW / NEEDS_IMPROVEMENT 판정 문자열을 그대로 노출하지 않음
