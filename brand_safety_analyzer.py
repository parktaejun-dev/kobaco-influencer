"""
브랜드 세이프티 분석 모듈
Gemini AI를 활용한 YouTube 채널 브랜드 안전성 검사

6개 카테고리 체크리스트:
1. 콘텐츠 안전성 (Content Safety)
2. 법적/윤리적 리스크 (Legal & Ethics)
3. 평판 리스크 (Reputation Risk)
4. 커뮤니티 건전성 (Community Health)
5. 브랜드 적합성 (Brand Fit)
6. 추가 확인 사항 (Additional Checks)
"""

import json

# Gemini AI (선택적 import)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def format_number(num):
    """숫자를 읽기 쉬운 형식으로 변환"""
    return f"{num:,}"


def analyze_with_gemini(channel_name, subscriber_count, avg_views, engagement_rate, recent_videos, cost_data, gemini_api_loaded):
    """
    Gemini AI를 사용한 종합 브랜드 세이프티 분석

    Parameters:
    -----------
    channel_name : str
        채널명
    subscriber_count : int
        구독자 수
    avg_views : int
        평균 조회수
    engagement_rate : float
        참여율 (%)
    recent_videos : list
        최근 영상 목록
    cost_data : dict
        광고 비용 정보
    gemini_api_loaded : bool
        Gemini API 로드 여부

    Returns:
    --------
    dict or None : AI 분석 결과 (JSON 형식)
    """
    if not GEMINI_AVAILABLE or not gemini_api_loaded:
        return None

    try:
        # 영상 정보 요약
        video_info = []
        for i, video in enumerate(recent_videos[:5], 1):
            title = video['snippet']['title']
            views = int(video['statistics'].get('viewCount', 0))
            likes = int(video['statistics'].get('likeCount', 0))
            comments = int(video['statistics'].get('commentCount', 0))
            video_info.append(f"{i}. 제목: {title[:50]}..., 조회수: {format_number(views)}, 좋아요: {format_number(likes)}, 댓글: {format_number(comments)}")

        video_summary = "\n".join(video_info)

        prompt = f"""
다음 유튜브 채널을 브랜드 세이프티 체크리스트에 따라 분석해주세요.

## 채널 정보
- 채널명: {channel_name}
- 구독자: {format_number(subscriber_count)}명
- 평균 조회수: {format_number(avg_views)}회
- 평균 참여율: {engagement_rate:.2f}%
- 광고 견적: {format_number(cost_data['final_cost'])}원

## 최근 5개 영상
{video_summary}

## 체크리스트

### 1. 콘텐츠 안전성 (Content Safety)
- **선정성**: 선정적 표현, 노출 의상, 성적 암시 여부 (0-100점)
- **폭력성**: 폭력 장면, 위험 행동, 혐오스러운 이미지 (0-100점)
- **혐오/차별**: 인종/성별/장애 차별, 외모 비하 (0-100점)
- **언어**: 욕설, 비속어, 공격적 표현 (0-100점)

### 2. 법적/윤리적 리스크 (Legal & Ethics)
- **저작권**: 무단 사용, 저작권 경고 이력 (0-100점)
- **허위정보**: 검증 안 된 정보, 가짜뉴스 (0-100점)
- **불법 행위**: 불법 미화, 탈법 조장 (0-100점)
- **광고 표시**: 협찬 숨김, 표기 의무 위반 (0-100점)

### 3. 평판 리스크 (Reputation Risk)
- **과거 논란**: 스캔들, 법적 분쟁 (0-100점)
- **정치/종교**: 극단적 입장, 특정 지지 (0-100점)
- **구독자 평판**: 댓글 반응, 안티 여부 (0-100점)

### 4. 커뮤니티 건전성 (Community Health)
- **댓글 관리**: 악성 댓글 대응 (0-100점)
- **구독자 특성**: 유기적 성장, 봇 의심 (0-100점)
- **타 인플루언서**: 논란 인물 협업 (0-100점)

### 5. 브랜드 적합성 (Brand Fit)
- **가치관 부합**: 브랜드 이미지 일치 (0-100점)
- **경쟁사**: 최근 협업 이력 (0-100점)
- **광고 품질**: 과거 협찬 퀄리티 (0-100점)

### 6. 추가 확인 사항 (Additional Checks)
- **채널 투명성**: 운영자 정보 공개 (0-100점)
- **콘텐츠 일관성**: 주제 일관성, 업로드 주기 (0-100점)
- **플랫폼 정책**: 커뮤니티 가이드라인 위반 이력 (0-100점)

각 카테고리별로 0-100점을 부여하고, 발견된 리스크를 분석해주세요.

### 광고 효과 예측
**조회수 예측**: 최근 10개 영상 기준으로 최소/평균/최대 예측
**AI 해설**: 광고 효과에 대한 종합 의견 (2-3문장)

### 상세 분석
- **타겟 오디언스**: 연령대, 관심사
- **강점**: 3-5개
- **약점**: 있다면 나열

반드시 다음 JSON 형식으로만 답변하세요:
{{
  "content_safety": {{
    "score": 90,
    "sexual_content": 95,
    "violence": 95,
    "hate_speech": 95,
    "language": 85,
    "issues": ["경미한 욕설 1-2회 사용"]
  }},
  "legal_ethics": {{
    "score": 95,
    "copyright": 95,
    "misinformation": 95,
    "illegal_activity": 100,
    "ad_disclosure": 95,
    "issues": []
  }},
  "reputation": {{
    "score": 85,
    "past_controversies": 90,
    "political_religious": 95,
    "subscriber_sentiment": 80,
    "issues": ["2년 전 경미한 논란 있었으나 해결"]
  }},
  "community": {{
    "score": 90,
    "comment_management": 90,
    "subscriber_authenticity": 95,
    "influencer_associations": 90,
    "issues": []
  }},
  "brand_fit": {{
    "score": 85,
    "value_alignment": 85,
    "competitor_history": 90,
    "ad_quality": 80,
    "issues": []
  }},
  "additional_checks": {{
    "score": 90,
    "transparency": 85,
    "content_consistency": 95,
    "platform_compliance": 95,
    "issues": []
  }},
  "overall_score": 89,
  "risk_assessment": {{
    "level": "low",
    "red_flags": [],
    "concerns": ["일부 영상 조회수 편차"]
  }},
  "recommendation": {{
    "action": "proceed",
    "reason": "전반적으로 안전한 채널, 브랜드 이미지 손상 위험 낮음"
  }},
  "content_quality": {{
    "score": 85,
    "professionalism": "high",
    "consistency": "excellent"
  }},
  "ad_effect": {{
    "views_prediction": {{
      "min": 60000,
      "avg": 80000,
      "max": 120000
    }},
    "summary": "높은 참여율과 전문성을 바탕으로 광고 효과가 우수할 것으로 예상됩니다. 타겟 오디언스와의 부합도가 높아 긍정적인 브랜드 인지도 향상이 기대됩니다."
  }},
  "detailed_analysis": {{
    "target_audience": "25-40세 IT 관심층",
    "strengths": ["전문적인 콘텐츠", "높은 참여율", "일관된 주제"],
    "weaknesses": ["조회수 편차"]
  }},
  "brand_safety": {{
    "score": 89,
    "checklist": {{
      "inappropriate_content": {{"status": "pass", "detail": "부적절한 콘텐츠 없음"}},
      "controversial_topics": {{"status": "pass", "detail": "논란 주제 없음"}},
      "profanity": {{"status": "warning", "detail": "경미한 욕설 1-2회"}},
      "brand_alignment": {{"status": "pass", "detail": "브랜드 이미지와 부합"}}
    }}
  }}
}}
"""

        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)

        # JSON 파싱
        response_text = response.text.strip()
        # JSON 코드 블록 제거
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        result = json.loads(response_text.strip())
        return result

    except Exception as e:
        # 에러 발생시 None 반환하고, 에러 메시지는 dict로 반환
        return {"error": str(e)}
