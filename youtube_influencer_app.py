"""
유튜브 인플루언서 검색 엔진 v4.0 (AI Enhanced)
- Gemini AI를 활용한 광고 효과 예측
- 1컬럼 레이아웃
- 콘텐츠 품질 자동 분석
"""

import streamlit as st
import requests
import re
from datetime import datetime
import os
import cost_calculator
import pandas as pd
import json

# Gemini AI (선택적 import)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="유튜브 인플루언서 검색 엔진 v4.0",
    page_icon="🎬",
    layout="wide"
)

# --- 스타일 ---
st.markdown("""
<style>
/* 강조 박스 */
.info-box {
    padding: 15px;
    border-radius: 8px;
    margin: 15px 0;
    border-left: 5px solid #1976d2;
    background-color: rgba(25, 118, 210, 0.1);
}

.warning-box {
    padding: 15px;
    border-radius: 8px;
    margin: 15px 0;
    border-left: 5px solid #ff9800;
    background-color: rgba(255, 152, 0, 0.1);
}

.success-box {
    padding: 15px;
    border-radius: 8px;
    margin: 15px 0;
    border-left: 5px solid #4caf50;
    background-color: rgba(76, 175, 80, 0.1);
}

/* AI 분석 박스 */
.ai-box {
    padding: 20px;
    border-radius: 12px;
    margin: 15px 0;
    border: 2px solid #9c27b0;
    background-color: rgba(156, 39, 176, 0.05);
}

/* 비용 표시 카드 */
.cost-card {
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    margin: 10px 0;
    border: 2px solid rgba(25, 118, 210, 0.5);
    background-color: rgba(25, 118, 210, 0.05);
}

.cost-value {
    font-size: 2em;
    font-weight: bold;
    color: #1976d2;
    margin: 10px 0;
}

.cost-label {
    font-size: 1.1em;
    opacity: 0.8;
    margin: 5px 0;
}
</style>
""", unsafe_allow_html=True)

# --- 제목 ---
st.title("🎬 유튜브 인플루언서 검색 엔진 v4.0")
st.caption("🤖 AI 기반 광고 효과 예측 기능 탑재")

# --- API 키 로드 ---
# YouTube API
try:
    youtube_api_key = st.secrets["YOUTUBE_API_KEY"]
    youtube_api_loaded = True
except:
    try:
        youtube_api_key = os.environ.get("YOUTUBE_API_KEY")
        youtube_api_loaded = bool(youtube_api_key)
    except:
        youtube_api_key = None
        youtube_api_loaded = False

# Gemini API
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
    gemini_api_loaded = True
except:
    try:
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        gemini_api_loaded = bool(gemini_api_key)
    except:
        gemini_api_key = None
        gemini_api_loaded = False

if not youtube_api_loaded:
    st.error("⚠️ YouTube API 키가 설정되지 않았습니다.")

if GEMINI_AVAILABLE and gemini_api_loaded:
    genai.configure(api_key=gemini_api_key)
    st.success("✅ AI 분석 기능 활성화됨 (Gemini)")
elif not GEMINI_AVAILABLE:
    st.warning("⚠️ Gemini AI 패키지가 설치되지 않았습니다. `pip install google-generativeai`")
else:
    st.info("💡 Gemini API 키를 설정하면 AI 분석 기능을 사용할 수 있습니다.")

# --- 함수 정의 ---

def extract_channel_id(url):
    """유튜브 URL에서 채널 ID를 추출하는 함수"""
    channel_id_pattern = r'youtube\.com/channel/([a-zA-Z0-9_-]+)'
    unicode_patterns = [
        r'youtube\.com/@([^/?&]+)',
        r'youtube\.com/c/([^/?&]+)',
        r'youtube\.com/user/([^/?&]+)',
    ]

    match = re.search(channel_id_pattern, url)
    if match:
        return match.group(1), channel_id_pattern

    for pattern in unicode_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), pattern

    return None, None

def get_channel_info_by_id(channel_id, api_key):
    """채널 ID로 채널 정보를 가져오는 함수"""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        'part': 'snippet,statistics,contentDetails',
        'id': channel_id,
        'key': api_key
    }

    response = requests.get(url, params=params)
    data = response.json()

    if 'items' in data and len(data['items']) > 0:
        return data['items'][0]
    return None

def get_channel_info_by_username(username, api_key):
    """사용자 이름으로 채널 정보를 가져오는 함수"""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        'part': 'snippet,statistics,contentDetails',
        'forHandle': username,
        'key': api_key
    }

    response = requests.get(url, params=params)
    data = response.json()

    if 'items' in data and len(data['items']) > 0:
        return data['items'][0]
    return None

def get_recent_videos(channel_id, api_key, max_results=10):
    """최근 업로드된 비디오 정보를 가져오는 함수"""
    channel_info = get_channel_info_by_id(channel_id, api_key)
    if not channel_info:
        return []

    uploads_playlist_id = channel_info['contentDetails']['relatedPlaylists']['uploads']

    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        'part': 'contentDetails',
        'playlistId': uploads_playlist_id,
        'maxResults': max_results,
        'key': api_key
    }

    response = requests.get(url, params=params)
    data = response.json()

    if 'items' not in data:
        return []

    video_ids = [item['contentDetails']['videoId'] for item in data['items']]

    videos_url = "https://www.googleapis.com/youtube/v3/videos"
    videos_params = {
        'part': 'statistics,snippet',
        'id': ','.join(video_ids),
        'key': api_key
    }

    videos_response = requests.get(videos_url, params=videos_params)
    videos_data = videos_response.json()

    return videos_data.get('items', [])

def calculate_engagement_rate(video_stats):
    """참여율 계산"""
    views = int(video_stats.get('viewCount', 0))
    likes = int(video_stats.get('likeCount', 0))
    comments = int(video_stats.get('commentCount', 0))

    if views == 0:
        return 0

    engagement_rate = ((likes + comments) / views) * 100
    return round(engagement_rate, 2)

def calculate_average_views(videos):
    """평균 조회수 계산"""
    if not videos:
        return 0

    total_views = sum(int(video['statistics'].get('viewCount', 0)) for video in videos)
    return total_views // len(videos)

def calculate_average_stats(videos):
    """평균 좋아요, 댓글 계산"""
    if not videos:
        return 0, 0

    total_likes = sum(int(video['statistics'].get('likeCount', 0)) for video in videos)
    total_comments = sum(int(video['statistics'].get('commentCount', 0)) for video in videos)

    return total_likes // len(videos), total_comments // len(videos)

def format_number(num):
    """숫자를 읽기 쉬운 형식으로 변환"""
    return f"{num:,}"

def analyze_with_gemini(channel_name, subscriber_count, avg_views, engagement_rate, recent_videos, cost_data):
    """Gemini AI를 사용한 종합 분석"""
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
다음 유튜브 채널에 대한 인플루언서 마케팅 분석을 수행해주세요.

## 채널 정보
- 채널명: {channel_name}
- 구독자: {format_number(subscriber_count)}명
- 평균 조회수: {format_number(avg_views)}회
- 평균 참여율: {engagement_rate:.2f}%
- 광고 견적: {format_number(cost_data['final_cost'])}원

## 최근 5개 영상
{video_summary}

다음 항목을 분석하여 JSON 형식으로 답변해주세요:

1. **콘텐츠 품질 점수** (0-100): 제목의 전문성, 일관성, 브랜드 협업 적합성
2. **예상 광고 효과**:
   - 예상 최소/평균/최대 조회수
   - 예상 클릭률 (CTR, %)
   - 예상 전환율 (%, 보수적으로)
   - 예상 ROI (투자 대비 수익률, %, 보수적으로)
3. **타겟 오디언스**: 연령대, 관심사 추정
4. **강점** (3가지)
5. **주의사항** (있다면)
6. **종합 추천**: "적극 추천" / "추천" / "조건부 추천" / "비추천"

반드시 다음 JSON 형식으로만 답변하세요:
{{
  "quality_score": 85,
  "ad_effect": {{
    "views_min": 60000,
    "views_avg": 80000,
    "views_max": 120000,
    "ctr": 3.5,
    "conversion_rate": 1.5,
    "roi": 250
  }},
  "target_audience": "25-40세 IT 관심층",
  "strengths": ["전문적인 콘텐츠", "높은 참여율", "일관된 주제"],
  "concerns": ["일부 영상 조회수 편차"],
  "recommendation": "추천"
}}
"""

        model = genai.GenerativeModel('gemini-1.5-flash-latest')
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
        st.error(f"AI 분석 중 오류 발생: {str(e)}")
        return None

# --- 메인 로직 ---
if youtube_api_loaded and youtube_api_key:

    # === 1컬럼 레이아웃 ===
    st.subheader("📝 채널 정보 입력")

    # 유튜브 URL 입력
    youtube_url = st.text_input(
        "유튜브 채널 URL",
        placeholder="예: https://www.youtube.com/@channelname",
        key="youtube_url_input"
    )

    # CPM 단가 조정
    st.write("**CPM 단가 설정**")
    st.caption("💡 브랜디드 PPL 기준 (제품 1개당 30초~1분 내외 노출)")
    cpm_value = st.slider(
        "1,000뷰당 비용 (원)",
        min_value=10000,
        max_value=100000,
        value=30000,
        step=5000,
        help="광고 시장 상황에 따라 CPM 단가를 조정할 수 있습니다. 기본값: 30,000원"
    )

    # 처리 시작
    if youtube_url:
        with st.spinner("채널 정보를 분석하는 중..."):
            channel_identifier, pattern = extract_channel_id(youtube_url)

            if not channel_identifier:
                st.error("❌ 올바른 유튜브 채널 URL을 입력해주세요.")
            else:
                # 채널 정보 가져오기
                if pattern and 'channel/' in pattern:
                    channel_info = get_channel_info_by_id(channel_identifier, youtube_api_key)
                else:
                    channel_info = get_channel_info_by_username(channel_identifier, youtube_api_key)

                if not channel_info:
                    st.error("❌ 채널 정보를 가져올 수 없습니다. URL을 확인해주세요.")
                else:
                    stats = channel_info['statistics']
                    snippet = channel_info['snippet']

                    subscriber_count = int(stats.get('subscriberCount', 0))
                    video_count = int(stats.get('videoCount', 0))
                    total_view_count = int(stats.get('viewCount', 0))

                    tier_name, tier_range = cost_calculator.get_influencer_tier(subscriber_count)

                    # 최근 영상 분석
                    recent_videos = get_recent_videos(channel_info['id'], youtube_api_key, max_results=10)

                    if recent_videos:
                        avg_views = calculate_average_views(recent_videos)
                        avg_likes, avg_comments = calculate_average_stats(recent_videos)

                        engagement_rates = [
                            calculate_engagement_rate(video['statistics'])
                            for video in recent_videos
                        ]
                        avg_engagement_rate = sum(engagement_rates) / len(engagement_rates)

                        # 비용 계산
                        cost_data = cost_calculator.estimate_ad_cost_korea(
                            subscriber_count=subscriber_count,
                            avg_views=avg_views,
                            engagement_rate=avg_engagement_rate,
                            avg_likes=avg_likes,
                            avg_comments=avg_comments,
                            recent_90day_avg_views=None,
                            cpm_krw=cpm_value
                        )

                        final_cost = cost_data['final_cost']
                        min_cost = cost_data['min_cost']
                        max_cost = cost_data['max_cost']

                        # === 결과 표시 ===
                        st.markdown("---")
                        st.header("📊 분석 결과")

                        # 채널 기본 정보
                        col_info1, col_info2 = st.columns([1, 2])

                        with col_info1:
                            if 'thumbnails' in snippet:
                                st.image(snippet['thumbnails']['medium']['url'], width=200)

                        with col_info2:
                            st.subheader(snippet['title'])
                            st.write(f"**등급:** {tier_name} ({tier_range} 구독자)")
                            st.write(f"**구독자:** {format_number(subscriber_count)}명")
                            st.write(f"**총 영상:** {format_number(video_count)}개")
                            st.write(f"**총 조회수:** {format_number(total_view_count)}회")

                        # 참여 지표
                        st.markdown("---")
                        st.subheader("📈 참여 지표 (최근 10개 영상)")

                        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                        metric_col1.metric("평균 조회수", format_number(avg_views))
                        metric_col2.metric("평균 참여율", f"{avg_engagement_rate:.2f}%")
                        metric_col3.metric("평균 좋아요", format_number(avg_likes))
                        metric_col4.metric("평균 댓글", format_number(avg_comments))

                        # 참여 질 분석
                        comment_like_ratio = (avg_comments / avg_likes * 100) if avg_likes > 0 else 0

                        if comment_like_ratio >= 15:
                            quality_emoji = "✅"
                            quality_text = "대화형 커뮤니티 (우수)"
                            quality_desc = "시청자와 활발한 소통이 이루어지는 채널입니다. 광고 효과가 높을 것으로 예상됩니다."
                            box_class = "success-box"
                        elif comment_like_ratio < 5:
                            quality_emoji = "⚠️"
                            quality_text = "이벤트형 (저품질)"
                            quality_desc = "좋아요 대비 댓글이 적어 단순 이벤트 참여 가능성이 있습니다. 광고 효과가 제한적일 수 있습니다."
                            box_class = "warning-box"
                        else:
                            quality_emoji = "✓"
                            quality_text = "정상 범위"
                            quality_desc = "일반적인 수준의 참여도를 보이는 채널입니다."
                            box_class = "info-box"

                        st.markdown(f"""
                        <div class="{box_class}">
                            <strong>🎯 참여 질 분석: {quality_emoji} {quality_text}</strong><br>
                            댓글/좋아요 비율: <strong>{comment_like_ratio:.2f}%</strong><br>
                            <small>{quality_desc}</small>
                        </div>
                        """, unsafe_allow_html=True)

                        # 광고 비용
                        st.markdown("---")
                        st.subheader("💰 1회 광고 적정 비용")

                        cost_col1, cost_col2, cost_col3 = st.columns(3)

                        with cost_col1:
                            st.markdown(f"""
                            <div class="cost-card">
                                <div class="cost-label">최소</div>
                                <div class="cost-value" style="font-size: 1.5em;">{format_number(min_cost)}원</div>
                            </div>
                            """, unsafe_allow_html=True)

                        with cost_col2:
                            st.markdown(f"""
                            <div class="cost-card" style="border-color: #1976d2; border-width: 3px;">
                                <div class="cost-label">평균 (권장)</div>
                                <div class="cost-value">{format_number(final_cost)}원</div>
                            </div>
                            """, unsafe_allow_html=True)

                        with cost_col3:
                            st.markdown(f"""
                            <div class="cost-card">
                                <div class="cost-label">최대</div>
                                <div class="cost-value" style="font-size: 1.5em;">{format_number(max_cost)}원</div>
                            </div>
                            """, unsafe_allow_html=True)

                        st.caption(f"💡 한국 시장 기준 | 브랜디드 PPL (30초~1분 노출) | CPM: {format_number(cpm_value)}원")

                        # AI 분석
                        if GEMINI_AVAILABLE and gemini_api_loaded:
                            st.markdown("---")
                            st.subheader("🤖 AI 광고 효과 예측")

                            if st.button("AI 분석 시작", type="primary", use_container_width=True):
                                with st.spinner("🤖 AI가 채널을 분석하고 광고 효과를 예측하는 중... (약 10초 소요)"):
                                    ai_result = analyze_with_gemini(
                                        snippet['title'],
                                        subscriber_count,
                                        avg_views,
                                        avg_engagement_rate,
                                        recent_videos,
                                        cost_data
                                    )

                                    if ai_result:
                                        st.markdown(f"""
                                        <div class="ai-box">
                                            <h4>🎯 AI 종합 분석 결과</h4>
                                            <p><strong>콘텐츠 품질 점수:</strong> {ai_result['quality_score']}/100</p>
                                            <p><strong>종합 추천:</strong> {ai_result['recommendation']}</p>
                                        </div>
                                        """, unsafe_allow_html=True)

                                        # 예상 광고 효과
                                        st.markdown("### 📊 예상 광고 효과")

                                        effect_col1, effect_col2 = st.columns(2)

                                        with effect_col1:
                                            st.metric("예상 조회수 (최소)", format_number(ai_result['ad_effect']['views_min']))
                                            st.metric("예상 조회수 (평균)", format_number(ai_result['ad_effect']['views_avg']))
                                            st.metric("예상 조회수 (최대)", format_number(ai_result['ad_effect']['views_max']))

                                        with effect_col2:
                                            st.metric("예상 클릭률 (CTR)", f"{ai_result['ad_effect']['ctr']}%")
                                            st.metric("예상 전환율", f"{ai_result['ad_effect']['conversion_rate']}%")
                                            st.metric("예상 ROI", f"{ai_result['ad_effect']['roi']}%")

                                        # 타겟 오디언스
                                        st.info(f"**타겟 오디언스:** {ai_result['target_audience']}")

                                        # 강점과 주의사항
                                        strength_col, concern_col = st.columns(2)

                                        with strength_col:
                                            st.markdown("**✅ 강점**")
                                            for strength in ai_result['strengths']:
                                                st.write(f"• {strength}")

                                        with concern_col:
                                            st.markdown("**⚠️ 주의사항**")
                                            if ai_result.get('concerns'):
                                                for concern in ai_result['concerns']:
                                                    st.write(f"• {concern}")
                                            else:
                                                st.write("• 특이사항 없음")

                        # 최근 영상 분석
                        st.markdown("---")
                        st.subheader("🎥 최근 영상 분석 (최근 10개)")

                        # 테이블
                        video_table_data = []
                        for i, video in enumerate(recent_videos, 1):
                            video_stats = video['statistics']
                            video_snippet = video['snippet']

                            title = video_snippet['title'][:40] + "..." if len(video_snippet['title']) > 40 else video_snippet['title']
                            views = int(video_stats.get('viewCount', 0))
                            likes = int(video_stats.get('likeCount', 0))
                            comments = int(video_stats.get('commentCount', 0))
                            engagement = calculate_engagement_rate(video_stats)

                            video_table_data.append({
                                '순서': f"{i}",
                                '제목': title,
                                '조회수': format_number(views),
                                '좋아요': format_number(likes),
                                '댓글': format_number(comments),
                                '참여율': f"{engagement}%"
                            })

                        df_videos = pd.DataFrame(video_table_data)
                        st.dataframe(df_videos, use_container_width=True, hide_index=True)

                        # 차트
                        chart_col1, chart_col2 = st.columns(2)

                        with chart_col1:
                            st.write("**조회수 추이**")
                            chart_data = pd.DataFrame({
                                '영상': [f"{i+1}" for i in range(len(recent_videos))],
                                '조회수': [int(v['statistics'].get('viewCount', 0)) for v in recent_videos]
                            })
                            st.bar_chart(chart_data.set_index('영상'), height=300)

                        with chart_col2:
                            st.write("**참여율 추이**")
                            engagement_data = pd.DataFrame({
                                '영상': [f"{i+1}" for i in range(len(recent_videos))],
                                '참여율': [calculate_engagement_rate(v['statistics']) for v in recent_videos]
                            })
                            st.line_chart(engagement_data.set_index('영상'), height=300)

                        # 참고사항
                        with st.expander("📝 참고사항"):
                            st.write("**비용 산정 기준**")
                            st.write("• 브랜디드 PPL 기준 (제품 1개당 30초~1분 내외 단순 노출)")
                            st.write("• 단순 언급(Mention)은 30-50% 저렴")
                            st.write("• 콘텐츠 재사용권 포함 시 20-50% 추가")
                            st.write("• 독점 계약 시 30-100% 추가 가능")
                            st.write("")
                            st.write("**v4.1 개선사항**")
                            st.write("• CPM 기준 30,000원으로 조정 (시장 반영)")
                            st.write("• 최근 90일 CPM 계산 (죽은 채널 방지)")
                            st.write("• 참여 질 보정: 댓글/좋아요 비율 분석")
                            st.write("• AI 광고 효과 예측: Gemini AI 활용")
                            st.caption("데이터 출처: PageOne Formula, Shopify, Descript, ADOPTER Media (2024-2025)")

                    else:
                        st.warning("⚠️ 최근 영상 정보를 가져올 수 없습니다.")

else:
    st.info("⚠️ 서비스 설정이 완료되지 않았습니다. 관리자에게 문의하세요.")

# 푸터
st.markdown("---")
st.caption("Made with ❤️ | 유튜브 인플루언서 검색 엔진 v4.1 (2025) | Powered by Gemini AI")
