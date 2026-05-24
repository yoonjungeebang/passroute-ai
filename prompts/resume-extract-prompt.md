다음 이력서/포트폴리오 텍스트에서 정보를 추출해 JSON으로만 반환해.
설명, 마크다운, 백틱 없이 순수 JSON으로만 반환할 것.
항목이 없으면 빈 배열[] 또는 null로 반환할 것.

텍스트:
{text}

반환 형식:
{
  "name": "이름",
  "email": "이메일",
  "phone": "전화번호",
  "birth_date": "생년월일 YYYY-MM-DD",
  "location": "거주지",
  "github": "GitHub URL",
  "blog": "블로그/포트폴리오 URL",
  "summary": "전체 프로필 요약 2-3문장",

  "skills": ["스킬1", "스킬2"],

  "experience": [
    {
      "company": "회사명",
      "role": "직책/직무",
      "employment_type": "정규직/계약직/인턴/프리랜서",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM 또는 present",
      "description": "주요 업무 및 성과"
    }
  ],

  "education": [
    {
      "school": "학교명",
      "degree": "학사/석사/박사/전문학사",
      "major": "전공",
      "status": "졸업/재학/휴학/중퇴",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM 또는 present",
      "gpa": "학점 (없으면 null)"
    }
  ],

  "projects": [
    {
      "name": "프로젝트명",
      "description": "설명",
      "role": "본인 역할",
      "tech_stack": ["기술1", "기술2"],
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM 또는 present",
      "url": "링크 (없으면 null)"
    }
  ],

  "certifications": [
    {
      "name": "자격증명",
      "issuer": "발급 기관",
      "date": "YYYY-MM",
      "grade": "등급/점수 (없으면 null)"
    }
  ],

  "languages": [
    {
      "language": "영어/일본어/중국어 등",
      "test": "TOEIC/TOEFL/OPIc/JLPT/HSK/TOPIK 등",
      "score": "점수 또는 등급",
      "date": "취득일 YYYY-MM (없으면 null)"
    }
  ],

  "activities": [
    {
      "type": "대외활동/봉사/동아리/학회/공모전",
      "name": "활동명",
      "role": "역할",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM 또는 present",
      "description": "내용"
    }
  ],

  "awards": [
    {
      "name": "수상명",
      "issuer": "주최 기관",
      "date": "YYYY-MM",
      "description": "내용 (없으면 null)"
    }
  ],

  "military": {
    "status": "미필/복무중/병역특례/면제/완료",
    "branch": "육군/해군/공군/해병대/사회복무 등 (없으면 null)",
    "start_date": "YYYY-MM (없으면 null)",
    "end_date": "YYYY-MM (없으면 null)"
  }
  
  "desired_job": "희망 직무 (없으면 null)",
  "linkedin": "LinkedIn URL (없으면 null)",
  "overseas_experience": [
    {
      "country": "국가",
      "purpose": "어학연수/워킹홀리데이/교환학생/해외취업 등",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM"
    }
  ],
  "disability": {
    "status": true/false,
    "detail": "장애 유형 또는 보훈 내용 (없으면 null)"
  },
  "driving_license": "1종보통/2종보통/없음 등 (없으면 null)"

}