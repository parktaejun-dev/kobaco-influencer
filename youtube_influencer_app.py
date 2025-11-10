"""
유튜브 인플루언서 검색 엔진 v4.3 (AI Enhanced + Smart Tier)
- Gemini AI를 활용한 광고 효과 예측
- 스마트 티어 시스템 (채널 건강도 평가)
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
import brand_safety_analyzer

# Gemini AI (선택적 import)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="유튜브 인플루언서 검색 엔진 v4.3",
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

/* 프로그레스 애니메이션 */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.analyzing {
    animation: pulse 1.5s ease-in-out infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.spinner {
    animation: spin 1s linear infinite;
}

/* 체크 애니메이션 */
@keyframes checkFade {
    0% { opacity: 0; transform: translateY(-10px); }
    100% { opacity: 1; transform: translateY(0); }
}

.check-item-animated {
    animation: checkFade 0.5s ease-out;
}
</style>
""", unsafe_allow_html=True)

# --- 제목 ---
st.title("🎬 유튜브 인플루언서 검색 엔진 v4.3")
st.caption("Smart Tier System 🔥 | AI Brand Safety Analysis ✅")
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

# --- 메인 로직 ---
if youtube_api_loaded and youtube_api_key:

    # === 1컬럼 레이아웃 ===
    st.subheader("📝 채널 정보 입력")

    # URL 입력
    youtube_url = st.text_input(
        "유튜브 채널 URL",
        placeholder="예: https://www.youtube.com/@channelname",
        key="youtube_url_input"
    )

    # 처리 시작 (URL 입력시 유튜브 정보 표시)
    if youtube_url:
        # CPM 값을 세션에서 가져오기 (슬라이더는 나중에 표시)
        cpm_value = st.session_state.get('cpm_slider', 30000)

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

                        # 비용 계산 (채널 건강도 정보를 얻기 위한 초기 계산)
                        cost_data = cost_calculator.estimate_ad_cost_korea(
                            subscriber_count=subscriber_count,
                            avg_views=avg_views,
                            engagement_rate=avg_engagement_rate,
                            avg_likes=avg_likes,
                            avg_comments=avg_comments,
                            recent_90day_avg_views=None,
                            cpm_krw=cpm_value
                        )

                        # === 결과 표시 ===
                        st.markdown("---")
                        st.header("📊 채널 개요")

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

                        # 참여 질 설명
                        with st.expander("💡 참여 질이란? (클릭하여 자세히 보기)"):
                            st.markdown("""
                            ### 📊 댓글/좋아요 비율이란?

                            **진짜 팬 vs 이벤트 참여자를 구분하는 지표입니다.**

                            **비율 기준:**
                            - ✅ **15% 이상**: 대화형 커뮤니티 (우수)
                              - 시청자들이 적극적으로 댓글을 남기고 소통합니다
                              - 좋아요 100개당 댓글 15개 이상
                              - 진정한 팬층이 형성된 채널

                            - ✓ **5-15%**: 정상 범위
                              - 일반적인 수준의 참여도
                              - 좋아요 100개당 댓글 5-15개
                              - 평균적인 채널

                            - ⚠️ **5% 미만**: 이벤트형 (저품질)
                              - 좋아요 100개당 댓글 5개 미만
                              - "좋아요 누르면 경품 추첨" 같은 이벤트로 유입된 참여자
                              - 실제 콘텐츠에 관심이 없는 시청자 다수

                            **왜 중요한가요?**

                            **이벤트형 채널의 문제점:**
                            1. **낮은 광고 효과**: "좋아요만 누르고 가는" 시청자는 광고를 제대로 보지 않습니다
                            2. **허수 참여**: 경품 때문에 온 사람들은 브랜드에 관심이 없습니다
                            3. **전환율 낮음**: 실제 구매로 이어질 가능성이 매우 낮습니다

                            **대화형 커뮤니티의 장점:**
                            1. **진성 팬층**: 댓글을 남기는 사람은 콘텐츠를 진지하게 시청합니다
                            2. **높은 신뢰도**: 인플루언서와 팬의 관계가 돈독합니다
                            3. **광고 효과 극대화**: 추천을 신뢰하고 실제 구매로 이어집니다

                            **광고주 입장에서:**
                            - 댓글이 많은 채널 = 진짜 영향력이 있는 채널
                            - 좋아요만 많은 채널 = 이벤트로 부풀려진 허수일 가능성
                            """)

                        # 채널 건강도 표시 (v4.3 신규)
                        channel_health = cost_data.get('channel_health', {})
                        if channel_health:
                            health_ratio = channel_health['ratio']
                            health_level = channel_health['level']
                            health_emoji = channel_health['emoji']
                            health_desc = channel_health['description']
                            health_color = channel_health['color']
                            health_multiplier = channel_health['multiplier']

                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, rgba({int(health_color[1:3], 16)}, {int(health_color[3:5], 16)}, {int(health_color[5:7], 16)}, 0.1) 0%, #ffffff 100%); padding: 20px; border-radius: 12px; border-left: 5px solid {health_color}; margin: 15px 0;">
                                <div style="display: flex; align-items: center; justify-content: space-between;">
                                    <div>
                                        <div style="font-size: 1.5em; font-weight: bold; color: {health_color}; margin-bottom: 5px;">
                                            {health_emoji} 채널 건강도: {health_level}
                                        </div>
                                        <div style="font-size: 1em; color: #666;">
                                            조회수/구독자 비율: <strong>{health_ratio:.2f}%</strong> |
                                            티어 조정 계수: <strong>×{health_multiplier}</strong>
                                        </div>
                                        <div style="font-size: 0.9em; color: #555; margin-top: 8px;">
                                            {health_desc}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # 건강도 기준 설명
                            with st.expander("💡 채널 건강도란? (클릭하여 자세히 보기)"):
                                st.markdown("""
                                ### 📊 조회수/구독자 비율이란?

                                **건강한 채널의 지표:**
                                - 구독자 수만 많은 게 아니라, 실제로 시청하는 구독자가 많은 채널
                                - 조회수가 구독자 수에 비례하는 활발한 채널

                                **비율 기준:**
                                - 🔥 **30% 이상**: 초건강 (10만 구독자 → 3만+ 조회수)
                                - ✅ **20-30%**: 매우 건강 (10만 구독자 → 2-3만 조회수)
                                - ✅ **15-20%**: 건강 (10만 구독자 → 1.5-2만 조회수)
                                - ⚖️ **10-15%**: 정상 (10만 구독자 → 1-1.5만 조회수)
                                - ⚠️ **7-10%**: 약간 약화 (10만 구독자 → 7천-1만 조회수)
                                - ⚠️ **5-7%**: 약화 (10만 구독자 → 5천-7천 조회수)
                                - 🟡 **3-5%**: 죽어감 (10만 구독자 → 3천-5천 조회수)
                                - 🔴 **3% 미만**: 죽음 (구독자만 많고 조회수 없음)

                                **왜 중요한가요?**
                                - 구독자 수는 "과거의 영광"일 수 있습니다
                                - 실제 광고 효과는 "현재 조회수"로 결정됩니다
                                - 건강도가 낮으면 광고 집행 효과가 떨어집니다

                                **티어 조정 계수:**
                                - 건강도가 낮은 채널은 광고 비용이 하향 조정됩니다
                                - 반대로 매우 건강한 채널은 프리미엄이 붙습니다
                                - 공정한 가격 책정을 위한 시스템입니다
                                """)

                        # CPM 단가 조정
                        st.markdown("---")
                        st.markdown("### 💰 CPM 단가 설정")
                        st.caption("💡 브랜디드 PPL 기준 (제품 1개당 30초~1분 내외 노출)")
                        cpm_value = st.slider(
                            "1,000뷰당 비용 (원)",
                            min_value=10000,
                            max_value=100000,
                            value=30000,
                            step=5000,
                            help="광고 시장 상황에 따라 CPM 단가를 조정할 수 있습니다. 기본값: 30,000원",
                            key='cpm_slider'
                        )

                        # CPM 값으로 비용 재계산
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

                        # 광고 비용 표시
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
                            st.write("**v4.3 개선사항 (2025-11)**")
                            st.write("• 스마트 티어 시스템 도입 (채널 건강도 평가)")
                            st.write("• 조회수/구독자 비율 기반 8단계 건강도 측정")
                            st.write("• 건강도에 따른 가격 조정 (0.3x ~ 1.2x)")
                            st.write("• 구독자 뻥튀기 문제 해결")
                            st.write("")
                            st.write("**v4.2 개선사항 (2025-11)**")
                            st.write("• 티어별 최소 보장 금액 합리화 (Mega 4,750만→1,500만)")
                            st.write("• CPM 우선 작동, 티어는 보조 역할로 조정")
                            st.write("• 브랜드 세이프티 6개 카테고리 체크리스트")
                            st.write("")
                            st.write("**v4.1 개선사항**")
                            st.write("• CPM 기준 30,000원으로 조정 (시장 반영)")
                            st.write("• 최근 90일 CPM 계산 (죽은 채널 방지)")
                            st.write("• 참여 질 보정: 댓글/좋아요 비율 분석")
                            st.caption("데이터 출처: PageOne Formula, Shopify, Descript, ADOPTER Media (2024-2025)")

                        # AI 분석 버튼
                        st.markdown("---")
                        ai_button_clicked = False
                        if GEMINI_AVAILABLE and gemini_api_loaded:
                            ai_button_clicked = st.button("🤖 AI 분석 시작", type="primary", use_container_width=True, key="ai_analysis_btn")

                        # AI 분석 실행 (버튼이 클릭되었을 때)
                        if GEMINI_AVAILABLE and gemini_api_loaded and ai_button_clicked:
                            st.markdown("---")
                            st.subheader("🤖 AI 브랜드세이프티 점검")

                            # 프로그레스 표시
                            progress_placeholder = st.empty()
                            progress_placeholder.markdown("""
                                <div class="analyzing" style="
                                    background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 100%);
                                    padding: 20px;
                                    border-radius: 12px;
                                    border-left: 5px solid #1976d2;
                                    text-align: center;
                                ">
                                    <div class="spinner" style="font-size: 3em; margin-bottom: 15px;">🤖</div>
                                    <div style="font-size: 1.2em; font-weight: bold; color: #1976d2; margin-bottom: 10px;">
                                        AI 분석 진행 중...
                                    </div>
                                    <div style="font-size: 1em; color: #666;">
                                        브랜드 안전성 검사 및 광고 효과 예측 중입니다 (약 10초 소요)
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                            # AI 분석 실행
                            ai_result = brand_safety_analyzer.analyze_with_gemini(
                                snippet['title'],
                                subscriber_count,
                                avg_views,
                                avg_engagement_rate,
                                recent_videos,
                                cost_data,
                                gemini_api_loaded
                            )

                            # 프로그레스 제거
                            progress_placeholder.empty()

                            # 에러 처리
                            if ai_result and "error" in ai_result:
                                st.error(f"AI 분석 중 오류 발생: {ai_result['error']}")
                            elif ai_result:

                                # ============================================
                                # 1단계: 채널 장단점
                                # ============================================
                                st.markdown("---")
                                st.subheader("📊 채널 장단점")

                                # 콘텐츠 품질 점수 (큰 카드)
                                quality_score = ai_result['content_quality']['score']
                                st.markdown(f"""
<div style="background-color: #f5f5f5; padding: 25px; border-radius: 12px; text-align: center; border: 2px solid #1976d2; margin-bottom: 20px;">
    <h3 style="margin: 0 0 15px 0; color: #1976d2;">콘텐츠 품질 점수</h3>
    <div style="font-size: 3em; font-weight: bold; color: #1976d2; margin: 10px 0;">
        {quality_score}<span style="font-size: 0.4em; opacity: 0.7;">/100</span>
    </div>
    <div style="font-size: 1.1em; color: #666;">
        전문성: {ai_result['content_quality']['professionalism']} | 일관성: {ai_result['content_quality']['consistency']}
    </div>
</div>
                                """, unsafe_allow_html=True)

                                # 타겟 오디언스 + 강점/약점
                                detail_col1, detail_col2, detail_col3 = st.columns(3)

                                with detail_col1:
                                    st.markdown("**🎯 타겟 오디언스**")
                                    st.info(ai_result['detailed_analysis']['target_audience'])

                                with detail_col2:
                                    st.markdown("**✅ 강점**")
                                    for strength in ai_result['detailed_analysis']['strengths']:
                                        st.write(f"• {strength}")

                                with detail_col3:
                                    st.markdown("**⚠️ 주의사항**")
                                    if ai_result['detailed_analysis'].get('weaknesses'):
                                        for weakness in ai_result['detailed_analysis']['weaknesses']:
                                            st.write(f"• {weakness}")
                                    else:
                                        st.write("• 특이사항 없음")

                                # ============================================
                                # 2단계: AI 광고 효과 해설
                                # ============================================
                                st.markdown("---")
                                st.markdown(f"""
<div style="background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 100%); padding: 20px; border-radius: 12px; border-left: 5px solid #1976d2; margin: 15px 0;">
    <div style="display: flex; align-items: start;">
        <div style="font-size: 2em; margin-right: 15px;">🤖</div>
        <div>
            <div style="font-size: 1.1em; font-weight: bold; color: #1976d2; margin-bottom: 8px;">
                AI 광고 효과 분석
            </div>
            <div style="font-size: 1em; line-height: 1.6; color: #333;">
                {ai_result['ad_effect']['summary']}
            </div>
        </div>
    </div>
</div>
                                """, unsafe_allow_html=True)

                                # ============================================
                                # 3단계: 브랜드 안전성
                                # ============================================
                                st.markdown("---")
                                st.subheader("🛡️ 브랜드 안전성 검사")
                                
                                safety_score = ai_result['brand_safety']['score']
                                action = ai_result['recommendation']['action']

                                # 점수에 따른 색상 및 상태 결정 (엄격한 기준)
                                if safety_score >= 90:
                                    safety_color = "#4caf50"
                                    safety_bg = "#e8f5e9"
                                    safety_border = "#4caf50"
                                    safety_status = "매우 안전"
                                    safety_emoji = "🟢"
                                    action_badge = "✅ 광고 집행 적극 권장"
                                    action_color = "#4caf50"
                                elif safety_score >= 80:
                                    safety_color = "#8bc34a"
                                    safety_bg = "#f1f8e9"
                                    safety_border = "#8bc34a"
                                    safety_status = "안전"
                                    safety_emoji = "🟢"
                                    action_badge = "✅ 광고 집행 가능"
                                    action_color = "#8bc34a"
                                elif safety_score >= 70:
                                    safety_color = "#ff9800"
                                    safety_bg = "#fff3e0"
                                    safety_border = "#ff9800"
                                    safety_status = "주의 필요"
                                    safety_emoji = "🟡"
                                    action_badge = "⚠️ 신중한 검토 필요"
                                    action_color = "#ff9800"
                                else:
                                    safety_color = "#f44336"
                                    safety_bg = "#ffebee"
                                    safety_border = "#f44336"
                                    safety_status = "위험"
                                    safety_emoji = "🔴"
                                    action_badge = "🚨 광고 집행 중단 권고"
                                    action_color = "#f44336"

                                # 대형 브랜드 안전성 카드
                                st.markdown(f"""
<div style="background: linear-gradient(135deg, {safety_bg} 0%, #ffffff 100%); padding: 30px; border-radius: 15px; border: 3px solid {safety_border}; margin: 20px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="flex: 1; text-align: center;">
            <div style="font-size: 5em; margin-bottom: 10px;">{safety_emoji}</div>
            <div style="font-size: 3.5em; font-weight: bold; color: {safety_color}; margin-bottom: 10px;">
                {safety_score}<span style="font-size: 0.5em; opacity: 0.7;">/100</span>
            </div>
            <div style="font-size: 1.3em; color: {safety_color}; font-weight: bold;">
                {safety_status}
            </div>
        </div>
        <div style="width: 2px; height: 150px; background: rgba(0,0,0,0.1); margin: 0 30px;"></div>
        <div style="flex: 2;">
            <div style="background-color: {action_color}; color: white; padding: 15px 25px; border-radius: 10px; font-size: 1.5em; font-weight: bold; text-align: center; margin-bottom: 20px;">
                {action_badge}
            </div>
            <div style="font-size: 1.1em; line-height: 1.6; color: #333;">
                <strong>평가:</strong> {ai_result['recommendation']['reason']}
            </div>
        </div>
    </div>
</div>
                                """, unsafe_allow_html=True)

                                # 브랜드 안전성 체크리스트 (6개 카테고리)
                                st.markdown("#### 🔍 브랜드 세이프티 체크리스트")

                                # 6개 카테고리 정의
                                categories = [
                                    ("content_safety", "📋 1. 콘텐츠 안전성", "선정성, 폭력성, 혐오/차별, 언어"),
                                    ("legal_ethics", "⚖️ 2. 법적/윤리적 리스크", "저작권, 허위정보, 불법 행위, 광고 표시"),
                                    ("reputation", "📊 3. 평판 리스크", "과거 논란, 정치/종교, 구독자 평판"),
                                    ("community", "👥 4. 커뮤니티 건전성", "댓글 관리, 구독자 특성, 타 인플루언서"),
                                    ("brand_fit", "🎯 5. 브랜드 적합성", "가치관 부합, 경쟁사, 광고 품질"),
                                    ("additional_checks", "✅ 6. 추가 확인 사항", "채널 투명성, 콘텐츠 일관성, 플랫폼 정책")
                                ]

                                # 3열로 표시
                                for i in range(0, len(categories), 3):
                                    cols = st.columns(3)
                                    for j in range(3):
                                        if i + j < len(categories):
                                            key, title, desc = categories[i + j]

                                            with cols[j]:
                                                if key in ai_result:
                                                    category_data = ai_result[key]
                                                    score = category_data.get('score', 0)
                                                    issues = category_data.get('issues', [])

                                                    # 점수에 따른 색상 (엄격한 기준)
                                                    if score >= 90:
                                                        color = "#4caf50"
                                                        bg = "#e8f5e9"
                                                        status_text = "우수"
                                                    elif score >= 80:
                                                        color = "#8bc34a"
                                                        bg = "#f1f8e9"
                                                        status_text = "양호"
                                                    elif score >= 70:
                                                        color = "#ff9800"
                                                        bg = "#fff3e0"
                                                        status_text = "보통"
                                                    else:
                                                        color = "#f44336"
                                                        bg = "#ffebee"
                                                        status_text = "위험"

                                                    # 이슈 표시
                                                    issues_html = ""
                                                    if issues:
                                                        issues_html = "<br>".join([f"• {issue}" for issue in issues])
                                                    else:
                                                        issues_html = "• 특이사항 없음"

                                                    st.markdown(f"""
                                                    <div style="background-color: {bg}; padding: 15px; border-radius: 10px; border-left: 4px solid {color}; margin-bottom: 15px; height: 100%;">
                                                        <div style="font-weight: bold; margin-bottom: 8px; color: {color};">
                                                            {title}
                                                        </div>
                                                        <div style="font-size: 2em; font-weight: bold; color: {color}; margin: 10px 0;">
                                                            {score}<span style="font-size: 0.5em; opacity: 0.7;">/100</span>
                                                        </div>
                                                        <div style="font-size: 0.9em; color: #666; margin-bottom: 8px;">
                                                            {desc}
                                                        </div>
                                                        <div style="font-size: 0.85em; color: #555;">
                                                            {issues_html}
                                                        </div>
                                                    </div>
                                                    """, unsafe_allow_html=True)

                                # 기존 4개 체크리스트 (호환성 유지)
                                if 'checklist' in ai_result.get('brand_safety', {}):
                                    st.markdown("---")
                                    st.markdown("##### 상세 체크리스트")

                                    checklist = ai_result['brand_safety']['checklist']
                                    check_col1, check_col2 = st.columns(2)

                                    checklist_items = [
                                        ("inappropriate_content", "부적절한 콘텐츠"),
                                        ("controversial_topics", "논란성 주제"),
                                        ("profanity", "비속어/욕설"),
                                        ("brand_alignment", "브랜드 부합도")
                                    ]

                                    for idx, (key, label) in enumerate(checklist_items):
                                        col = check_col1 if idx % 2 == 0 else check_col2

                                        with col:
                                            if key in checklist:
                                                item = checklist[key]
                                                status = item.get('status', 'unknown')
                                                detail = item.get('detail', '정보 없음')

                                                if status == "pass":
                                                    icon = "✅"
                                                    bg_color = "#e8f5e9"
                                                    border_color = "#4caf50"
                                                elif status == "warning":
                                                    icon = "⚠️"
                                                    bg_color = "#fff3e0"
                                                    border_color = "#ff9800"
                                                else:
                                                    icon = "❌"
                                                    bg_color = "#ffebee"
                                                    border_color = "#f44336"

                                                st.markdown(f"""
                                                <div style="background-color: {bg_color}; padding: 12px; border-radius: 8px; border-left: 4px solid {border_color}; margin-bottom: 10px;">
                                                    <div style="font-size: 1.1em; font-weight: bold; margin-bottom: 5px;">
                                                        {icon} {label}
                                                    </div>
                                                    <div style="font-size: 0.95em; color: #666;">
                                                        {detail}
                                                    </div>
                                                </div>
                                                """, unsafe_allow_html=True)

                                # 리스크가 있는 경우 경고 표시
                                if ai_result['risk_assessment'].get('red_flags'):
                                    st.error("🚩 **발견된 브랜드 리스크**")
                                    for flag in ai_result['risk_assessment']['red_flags']:
                                        st.markdown(f"""
                                        <div style="background-color: #ffebee; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 5px solid #f44336;">
                                            <strong>⚠️ {flag}</strong>
                                        </div>
                                        """, unsafe_allow_html=True)

                                    # 중단 권고 시 여기서 멈춤
                                    if action == "block":
                                        st.info("💡 이 채널은 브랜드 이미지에 부정적 영향을 줄 수 있어 광고 집행을 권장하지 않습니다.")
                                        st.stop()

                                # 주의 필요 시 경고
                                if action == "caution" and ai_result['risk_assessment'].get('concerns'):
                                    with st.expander("⚠️ 주의사항 확인", expanded=True):
                                        st.warning("이 채널은 일부 주의사항이 있습니다. 신중한 검토 후 광고 집행을 결정하세요.")
                                        for concern in ai_result['risk_assessment']['concerns']:
                                            st.write(f"• {concern}")

                    else:
                        st.warning("⚠️ 최근 영상 정보를 가져올 수 없습니다.")

else:
    st.info("⚠️ 서비스 설정이 완료되지 않았습니다. 관리자에게 문의하세요.")

# 푸터
st.markdown("---")
st.caption("Made with ❤️ | 유튜브 인플루언서 검색 엔진 v4.3 (2025) | Powered by Gemini AI + Smart Tier System")
