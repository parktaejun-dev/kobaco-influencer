"""
유튜브 인플루언서 검색 엔진 v4.0 (Redesigned)
사용자가 유튜브 링크를 입력하면 채널 정보를 분석하고 광고 비용을 산출합니다.
- v4.0 개선: 참여 질 보정, 콘텐츠 포맷 프리미엄
- 2컬럼 레이아웃: 좌측(입력), 우측(결과)
- 다크/라이트 테마 호환
"""

import streamlit as st
import requests
import re
from datetime import datetime
import os
import cost_calculator
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="유튜브 인플루언서 검색 엔진 v4.0",
    page_icon="🎬",
    layout="wide"
)

# --- 스타일 (다크/라이트 테마 호환) ---
st.markdown("""
<style>
/* 강조 박스 - 테마 호환 */
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

/* 버튼 그룹 스타일 */
.button-group {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# --- 제목 ---
st.title("🎬 유튜브 인플루언서 검색 엔진 v4.0")

# --- API 키 로드 ---
try:
    api_key = st.secrets["YOUTUBE_API_KEY"]
    api_key_loaded = True
except:
    try:
        api_key = os.environ.get("YOUTUBE_API_KEY")
        if api_key:
            api_key_loaded = True
        else:
            api_key = None
            api_key_loaded = False
    except:
        api_key = None
        api_key_loaded = False

if not api_key_loaded:
    st.error("⚠️ API 키가 설정되지 않았습니다. 관리자에게 문의하세요.")

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
    """평균 좋아요, 댓글 계산 (v4.0)"""
    if not videos:
        return 0, 0

    total_likes = sum(int(video['statistics'].get('likeCount', 0)) for video in videos)
    total_comments = sum(int(video['statistics'].get('commentCount', 0)) for video in videos)

    return total_likes // len(videos), total_comments // len(videos)

def format_number(num):
    """숫자를 읽기 쉬운 형식으로 변환"""
    return f"{num:,}"

# --- 메인 로직 ---
if api_key_loaded and api_key:

    # === 2컬럼 레이아웃 ===
    left_col, right_col = st.columns([1, 1])

    # === 좌측 컬럼: 입력 영역 ===
    with left_col:
        st.subheader("📝 채널 정보 입력")

        # 유튜브 URL 입력
        youtube_url = st.text_input(
            "유튜브 채널 URL",
            placeholder="예: https://www.youtube.com/@channelname",
            key="youtube_url_input"
        )

        # CPM 단가 조정
        st.write("**CPM 단가 설정**")
        cpm_value = st.slider(
            "1,000뷰당 비용 (원)",
            min_value=10000,
            max_value=100000,
            value=30000,
            step=5000,
            help="광고 시장 상황에 따라 CPM 단가를 조정할 수 있습니다. 기본값: 30,000원"
        )
        st.caption(f"현재 CPM: {format_number(cpm_value)}원/1,000뷰")

        # 콘텐츠 포맷 선택 (버튼 그룹)
        st.write("**광고 콘텐츠 유형**")
        st.caption("기본값이 적용됩니다. 필요 시 선택하세요.")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📌 기본", use_container_width=True, type="primary"):
                st.session_state.content_format = "기본"
            if st.button("📺 단순 노출형", use_container_width=True):
                st.session_state.content_format = "단순 노출형"

        with col2:
            if st.button("⭐ 제품 리뷰", use_container_width=True):
                st.session_state.content_format = "제품 리뷰"
            if st.button("🔍 비교/추천", use_container_width=True):
                st.session_state.content_format = "비교/추천"

        with col3:
            if st.button("💬 사용후기", use_container_width=True):
                st.session_state.content_format = "사용후기"
            if st.button("🎯 장기 캠페인", use_container_width=True):
                st.session_state.content_format = "장기 캠페인"

        # 기본값 설정
        if 'content_format' not in st.session_state:
            st.session_state.content_format = "기본"

        st.info(f"**선택된 유형:** {st.session_state.content_format}")

        # 포맷 설명
        with st.expander("📖 광고 유형별 설명"):
            st.write("**기본 (1.0x):** 일반적인 광고")
            st.write("**단순 노출형 (1.0x):** 브이로그 중 제품 삽입")
            st.write("**제품 리뷰 (1.2x):** 단독 리뷰 영상 (+20%)")
            st.write("**비교/추천 (1.35x):** 여러 제품 비교 또는 추천 (+35%)")
            st.write("**사용후기 (1.35x):** 장기 사용 리뷰 (+35%)")
            st.write("**장기 캠페인 (1.5x):** 3회 이상 연재형 (+50%)")

    # === 우측 컬럼: 결과 표시 ===
    with right_col:
        st.subheader("📊 분석 결과")

        if not youtube_url:
            st.info("← 좌측에 유튜브 채널 URL을 입력하세요")
        else:
            with st.spinner("채널 정보를 분석하는 중..."):
                channel_identifier, pattern = extract_channel_id(youtube_url)

                if not channel_identifier:
                    st.error("❌ 올바른 유튜브 채널 URL을 입력해주세요.")
                else:
                    # 채널 정보 가져오기
                    if pattern and 'channel/' in pattern:
                        channel_info = get_channel_info_by_id(channel_identifier, api_key)
                    else:
                        channel_info = get_channel_info_by_username(channel_identifier, api_key)

                    if not channel_info:
                        st.error("❌ 채널 정보를 가져올 수 없습니다. URL을 확인해주세요.")
                    else:
                        stats = channel_info['statistics']
                        snippet = channel_info['snippet']

                        subscriber_count = int(stats.get('subscriberCount', 0))
                        video_count = int(stats.get('videoCount', 0))
                        total_view_count = int(stats.get('viewCount', 0))

                        tier_name, tier_range = cost_calculator.get_influencer_tier(subscriber_count)

                        # === 1. 광고 비용 (상단 최우선 표시) ===
                        st.markdown("### 💰 1회 광고 적정 비용")

                        # 최근 영상 분석
                        recent_videos = get_recent_videos(channel_info['id'], api_key, max_results=10)

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
                                content_format=st.session_state.content_format,
                                cpm_krw=cpm_value
                            )

                            final_cost = cost_data['final_cost']
                            min_cost = cost_data['min_cost']
                            max_cost = cost_data['max_cost']

                            # 비용 표시 (간단하게)
                            st.markdown(f"""
                            <div class="cost-card">
                                <div class="cost-label">최소</div>
                                <div class="cost-value" style="font-size: 1.5em;">{format_number(min_cost)}원</div>
                            </div>
                            """, unsafe_allow_html=True)

                            st.markdown(f"""
                            <div class="cost-card" style="border-color: #1976d2; border-width: 3px;">
                                <div class="cost-label">평균 (권장)</div>
                                <div class="cost-value">{format_number(final_cost)}원</div>
                            </div>
                            """, unsafe_allow_html=True)

                            st.markdown(f"""
                            <div class="cost-card">
                                <div class="cost-label">최대</div>
                                <div class="cost-value" style="font-size: 1.5em;">{format_number(max_cost)}원</div>
                            </div>
                            """, unsafe_allow_html=True)

                            st.caption(f"💡 한국 시장 기준 | {tier_name} ({tier_range} 구독자)")

                            # === 2. 참여 질 분석 (설명 추가) ===
                            st.markdown("---")
                            st.markdown("### 🎯 참여 질 분석")

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
                                <strong>{quality_emoji} {quality_text}</strong><br>
                                댓글/좋아요 비율: <strong>{comment_like_ratio:.2f}%</strong><br>
                                <small>{quality_desc}</small>
                            </div>
                            """, unsafe_allow_html=True)

                            # === 3. 채널 기본 정보 ===
                            st.markdown("---")
                            st.markdown("### 📺 채널 정보")

                            if 'thumbnails' in snippet:
                                st.image(snippet['thumbnails']['medium']['url'], width=150)

                            st.write(f"**채널명:** {snippet['title']}")
                            st.write(f"**등급:** {tier_name}")
                            st.write(f"**구독자:** {format_number(subscriber_count)}명")
                            st.write(f"**총 영상:** {format_number(video_count)}개")
                            st.write(f"**총 조회수:** {format_number(total_view_count)}회")

                            # === 4. 참여 지표 ===
                            st.markdown("---")
                            st.markdown("### 📈 참여 지표 (최근 10개 영상)")

                            metric_col1, metric_col2 = st.columns(2)
                            metric_col1.metric("평균 조회수", format_number(avg_views))
                            metric_col2.metric("평균 참여율", f"{avg_engagement_rate:.2f}%")

                            metric_col3, metric_col4 = st.columns(2)
                            metric_col3.metric("평균 좋아요", format_number(avg_likes))
                            metric_col4.metric("평균 댓글", format_number(avg_comments))

                            # 참고사항
                            with st.expander("📝 참고사항"):
                                st.write("**비용 산정 기준**")
                                st.write("• 1회 전용 광고 영상(Dedicated Video) 기준")
                                st.write("• 단순 언급(Mention)은 30-50% 저렴")
                                st.write("• 콘텐츠 재사용권 포함 시 20-50% 추가")
                                st.write("• 독점 계약 시 30-100% 추가 가능")
                                st.write("")
                                st.write("**v4.0 개선사항**")
                                st.write("• 참여 질 보정: 댓글/좋아요 비율 분석")
                                st.write("• 콘텐츠 포맷 프리미엄: 광고 유형별 차등 적용")
                                st.caption("데이터 출처: PageOne Formula, Shopify, Descript, ADOPTER Media (2024-2025)")

                        else:
                            st.warning("⚠️ 최근 영상 정보를 가져올 수 없습니다.")

    # === 하단: 최근 영상 분석 (전체 너비) ===
    if youtube_url and channel_info and recent_videos:
        st.markdown("---")
        st.markdown("## 🎥 최근 영상 분석 (최근 10개)")

        # 테이블 형식으로 가독성 개선
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

        # 간단한 차트
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

else:
    st.info("⚠️ 서비스 설정이 완료되지 않았습니다. 관리자에게 문의하세요.")

# 푸터
st.markdown("---")
st.caption("Made with ❤️ | 유튜브 인플루언서 검색 엔진 v4.0 (2025)")
