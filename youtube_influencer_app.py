"""
유튜브 인플루언서 검색 엔진 v4.0
사용자가 유튜브 링크를 입력하면 채널 정보를 분석하고 광고 비용을 산출합니다.
- v4.0 개선: 참여 질 보정, 콘텐츠 포맷 프리미엄, 최근 90일 CPM
- 흰색 배경 디자인
- 보고서 인쇄 기능
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

# --- 스타일 (흰색 배경 기반) ---
st.markdown("""
<style>
/* 전체 배경을 흰색으로 */
.stApp {
    background-color: white;
}

/* 메인 컨텐츠 영역 */
.main {
    background-color: white;
}

/* 인쇄 스타일 */
@media print {
    .no-print {
        display: none !important;
    }
    .stApp {
        background-color: white;
    }
    .print-only {
        display: block !important;
    }
}

.print-only {
    display: none;
}

/* 비용 범위 바 */
.cost-range-bar {
    width: 100%;
    background-color: #f8f9fa;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 2px solid #0066cc;
    margin: 20px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.cost-range-line {
    width: 100%;
    height: 12px;
    background: linear-gradient(90deg, #a8d5ff 0%, #0066cc 50%, #a8d5ff 100%);
    border-radius: 6px;
    margin: 15px 0;
    position: relative;
}

.cost-label {
    font-size: 1.2em;
    font-weight: bold;
    color: #0066cc;
    margin-bottom: 10px;
}

.cost-minmax {
    display: flex;
    justify-content: space-between;
    font-size: 1em;
    color: #333;
    padding: 0 10px;
    font-weight: 600;
}

.cost-avg {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    top: -30px;
    font-weight: bold;
    font-size: 1.4em;
    color: #0066cc;
    background-color: white;
    padding: 5px 15px;
    border-radius: 8px;
    border: 2px solid #0066cc;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}

/* 강조 박스 (중요 계산 요소) */
.highlight-box {
    background-color: #fff8e1;
    border-left: 5px solid #ffa000;
    padding: 15px;
    margin: 15px 0;
    border-radius: 5px;
    font-size: 1.05em;
}

.highlight-box-blue {
    background-color: #e3f2fd;
    border-left: 5px solid #1976d2;
    padding: 15px;
    margin: 15px 0;
    border-radius: 5px;
    font-size: 1.05em;
}

.highlight-box-green {
    background-color: #e8f5e9;
    border-left: 5px solid #388e3c;
    padding: 15px;
    margin: 15px 0;
    border-radius: 5px;
    font-size: 1.05em;
}

/* v4.0 신규 배지 */
.new-badge {
    display: inline-block;
    background-color: #ff4444;
    color: white;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: bold;
    margin-left: 5px;
}

/* 계산 단계 표시 */
.calc-step {
    background-color: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 12px;
    margin: 10px 0;
}

.calc-step-title {
    font-weight: bold;
    color: #0066cc;
    font-size: 1.1em;
    margin-bottom: 5px;
}

.calc-step-value {
    font-size: 1.2em;
    color: #333;
    font-weight: 600;
}

/* 메트릭 카드 스타일 개선 */
.metric-card {
    background-color: white;
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    padding: 15px;
    text-align: center;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

# --- 제목 ---
st.title("🎬 유튜브 인플루언서 검색 엔진 v4.0")
st.markdown("""
<div class="highlight-box-blue">
<strong>✨ v4.0 주요 개선사항:</strong><br>
• 참여 질 보정 (댓글/좋아요 비율 분석)<span class="new-badge">NEW</span><br>
• 콘텐츠 포맷별 차등 가격<span class="new-badge">NEW</span><br>
• 최근 90일 활동 반영<span class="new-badge">NEW</span><br>
• 흰색 배경 및 보고서 인쇄 기능<span class="new-badge">NEW</span>
</div>
""", unsafe_allow_html=True)

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

    # 유튜브 URL 입력
    youtube_url = st.text_input(
        "🔗 유튜브 채널 URL을 입력하세요",
        placeholder="예: https://www.youtube.com/@channelname",
        key="youtube_url_input"
    )

    if youtube_url:
        with st.spinner("채널 정보를 가져오는 중..."):
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
                    # --- 채널 기본 정보 표시 ---
                    st.success("✅ 채널 정보를 성공적으로 가져왔습니다!")

                    stats = channel_info['statistics']
                    snippet = channel_info['snippet']

                    subscriber_count = int(stats.get('subscriberCount', 0))
                    video_count = int(stats.get('videoCount', 0))
                    total_view_count = int(stats.get('viewCount', 0))

                    tier_name, tier_range = cost_calculator.get_influencer_tier(subscriber_count)

                    col1, col2 = st.columns([1, 2])

                    with col1:
                        if 'thumbnails' in snippet:
                            st.image(snippet['thumbnails']['high']['url'], width=200)

                    with col2:
                        st.subheader(snippet['title'])
                        st.markdown(f"**등급:** {tier_name} ({tier_range} 구독자)")
                        st.write(f"**설명:** {snippet.get('description', 'N/A')[:200]}...")
                        st.write(f"**채널 생성일:** {snippet['publishedAt'][:10]}")

                    # --- 채널 통계 ---
                    st.markdown("---")
                    st.subheader("📊 채널 통계")

                    col1, col2, col3 = st.columns(3)
                    col1.metric("구독자 수", format_number(subscriber_count))
                    col2.metric("총 동영상 수", format_number(video_count))
                    col3.metric("총 조회수", format_number(total_view_count))

                    # --- 최근 영상 분석 ---
                    st.markdown("---")
                    st.subheader("🎥 최근 영상 분석 (최근 10개)")

                    with st.spinner("최근 영상 정보를 분석하는 중..."):
                        recent_videos = get_recent_videos(
                            channel_info['id'],
                            api_key,
                            max_results=10
                        )

                        if recent_videos:
                            # 평균 조회수/참여율/좋아요/댓글 계산
                            avg_views = calculate_average_views(recent_videos)
                            avg_likes, avg_comments = calculate_average_stats(recent_videos)

                            engagement_rates = [
                                calculate_engagement_rate(video['statistics'])
                                for video in recent_videos
                            ]
                            avg_engagement_rate = sum(engagement_rates) / len(engagement_rates)

                            # 댓글/좋아요 비율 계산 (v4.0)
                            comment_like_ratio = (avg_comments / avg_likes * 100) if avg_likes > 0 else 0

                            # 지표 표시
                            col1, col2, col3, col4 = st.columns(4)
                            col1.metric("평균 조회수", format_number(avg_views))
                            col2.metric("평균 참여율", f"{avg_engagement_rate:.2f}%")
                            col3.metric("평균 좋아요", format_number(avg_likes))
                            col4.metric("평균 댓글", format_number(avg_comments))

                            # v4.0 참여 질 분석 표시
                            st.markdown(f"""
                            <div class="highlight-box-green">
                            <strong>🎯 참여 질 분석 (v4.0 신규)</strong><br>
                            댓글/좋아요 비율: <strong>{comment_like_ratio:.2f}%</strong>
                            {' → 대화형 커뮤니티 (우수) ✅' if comment_like_ratio >= 15
                             else ' → 이벤트형 (저품질) ⚠️' if comment_like_ratio < 5
                             else ' → 정상 범위 ✓'}
                            </div>
                            """, unsafe_allow_html=True)

                            # --- 최근 영상 데이터 차트 ---
                            video_data = []
                            for i, video in enumerate(recent_videos, 1):
                                video_stats = video['statistics']
                                video_snippet = video['snippet']

                                title = f"{i}. {video_snippet['title'][:25]}..."
                                views = int(video_stats.get('viewCount', 0))
                                engagement = calculate_engagement_rate(video_stats)

                                video_data.append({
                                    '영상 (최신순)': title,
                                    '조회수': views,
                                    '참여율 (%)': engagement
                                })

                            if video_data:
                                df_videos = pd.DataFrame(video_data)

                                st.write("")
                                st.write("##### 최근 10개 영상 조회수")
                                st.bar_chart(df_videos.set_index('영상 (최신순)')['조회수'])

                                st.write("##### 최근 10개 영상 참여율 (%)")
                                st.line_chart(df_videos.set_index('영상 (최신순)')['참여율 (%)'])

                                with st.expander("최근 영상 상세 데이터 보기"):
                                    st.dataframe(df_videos)

                            # --- 콘텐츠 포맷 선택 (v4.0) ---
                            st.markdown("---")
                            st.subheader("💰 광고 비용 산출 (v4.0)")

                            st.markdown("""
                            <div class="highlight-box">
                            <strong>📝 콘텐츠 포맷을 선택하세요</strong><br>
                            콘텐츠 유형에 따라 광고 비용이 차등 적용됩니다.
                            </div>
                            """, unsafe_allow_html=True)

                            content_format = st.selectbox(
                                "광고 콘텐츠 유형",
                                ["기본", "단순 노출형", "제품 리뷰", "비교/추천", "사용후기", "장기 캠페인"],
                                help="• 단순 노출형: 브이로그 중 제품 삽입\n• 제품 리뷰: 단독 리뷰 영상\n• 비교/추천: 여러 제품 비교 또는 추천\n• 사용후기: 장기 사용 리뷰\n• 장기 캠페인: 3회 이상 연재형"
                            )

                            # 포맷별 계수 설명
                            format_multipliers_display = {
                                "기본": "1.0x (기본값)",
                                "단순 노출형": "1.0x",
                                "제품 리뷰": "1.2x (+20%)",
                                "비교/추천": "1.35x (+35%)",
                                "사용후기": "1.35x (+35%)",
                                "장기 캠페인": "1.5x (+50%)"
                            }

                            st.info(f"**선택한 포맷:** {content_format} → **가격 계수:** {format_multipliers_display[content_format]}")

                            # --- 광고 비용 산출 (v4.0) ---
                            cost_data = cost_calculator.estimate_ad_cost_korea(
                                subscriber_count=subscriber_count,
                                avg_views=avg_views,
                                engagement_rate=avg_engagement_rate,
                                avg_likes=avg_likes,
                                avg_comments=avg_comments,
                                recent_90day_avg_views=None,  # TODO: 최근 90일 데이터 수집 가능 시 구현
                                content_format=content_format
                            )

                            final_cost = cost_data['final_cost']
                            min_cost = cost_data['min_cost']
                            max_cost = cost_data['max_cost']

                            # --- 최종 비용 추천 범위 ---
                            st.markdown("---")
                            st.markdown(f"""
                            <div class="cost-range-bar">
                                <div class="cost-label">💰 추천 광고 비용 범위 (한국 시장 기준)</div>
                                <div class="cost-range-line">
                                    <div class="cost-avg">평균 {format_number(final_cost)}원</div>
                                </div>
                                <div class="cost-minmax">
                                    <span>최소 {format_number(min_cost)}원</span>
                                    <span>최대 {format_number(max_cost)}원</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # --- 계산 상세 단계 (시각적 강조) ---
                            st.write("")
                            st.write("### 📊 비용 산출 상세 단계")

                            step_col1, step_col2 = st.columns(2)

                            with step_col1:
                                st.markdown(f"""
                                <div class="calc-step">
                                    <div class="calc-step-title">STEP 1: CPM 기반 비용</div>
                                    <div class="calc-step-value">{format_number(cost_data['base_cost_cpm'])}원</div>
                                    <small>(평균 조회수 {format_number(avg_views)} × CPM {format_number(cost_data['cpm_used'])}원/1,000뷰)</small>
                                </div>
                                """, unsafe_allow_html=True)

                                st.markdown(f"""
                                <div class="calc-step">
                                    <div class="calc-step-title">STEP 2: 티어 최소 보장액</div>
                                    <div class="calc-step-value">{format_number(cost_data['tier_base'])}원</div>
                                    <small>({tier_name} 기준)</small>
                                </div>
                                """, unsafe_allow_html=True)

                                st.markdown(f"""
                                <div class="calc-step">
                                    <div class="calc-step-title">STEP 3: 기본 비용 (최댓값)</div>
                                    <div class="calc-step-value">{format_number(cost_data['base_cost'])}원</div>
                                    <small>(CPM vs 티어 중 높은 값)</small>
                                </div>
                                """, unsafe_allow_html=True)

                            with step_col2:
                                st.markdown(f"""
                                <div class="calc-step">
                                    <div class="calc-step-title">STEP 4: 참여율 보정</div>
                                    <div class="calc-step-value">×{cost_data['engagement_multiplier']}</div>
                                    <small>{cost_data['engagement_level']}</small>
                                </div>
                                """, unsafe_allow_html=True)

                                st.markdown(f"""
                                <div class="calc-step">
                                    <div class="calc-step-title">STEP 5: 참여 질 보정 <span class="new-badge">NEW</span></div>
                                    <div class="calc-step-value">×{cost_data['quality_multiplier']}</div>
                                    <small>{cost_data['quality_level']} (댓글/좋아요 비율: {cost_data['comment_like_ratio']:.3f})</small>
                                </div>
                                """, unsafe_allow_html=True)

                                st.markdown(f"""
                                <div class="calc-step">
                                    <div class="calc-step-title">STEP 6: 콘텐츠 포맷 <span class="new-badge">NEW</span></div>
                                    <div class="calc-step-value">×{cost_data['format_multiplier']}</div>
                                    <small>{cost_data['content_format']}</small>
                                </div>
                                """, unsafe_allow_html=True)

                            st.markdown(f"""
                            <div class="calc-step">
                                <div class="calc-step-title">STEP 7: 한국 시장 조정</div>
                                <div class="calc-step-value">×{cost_data['korea_adjustment']}</div>
                                <small>(글로벌 비용: {format_number(cost_data['global_final_cost'])}원)</small>
                            </div>
                            """, unsafe_allow_html=True)

                            # --- 비용 구성 요소 차트 ---
                            st.write("")
                            st.write("### 📈 비용 구성 분석")

                            base_val = cost_data['base_cost']
                            multiplier_val = max(0, final_cost - base_val)

                            cost_comp_data = {
                                '구성 요소': ['기본 비용 (CPM/티어)', '보정/조정액 (참여율, 질, 포맷, 시장)'],
                                '금액 (원)': [base_val, multiplier_val]
                            }

                            if base_val > 0 or multiplier_val > 0:
                                df_cost_comp = pd.DataFrame(cost_comp_data)
                                st.bar_chart(df_cost_comp.set_index('구성 요소'), use_container_width=True)

                            # --- 인쇄 버튼 ---
                            st.markdown("---")
                            col_print1, col_print2, col_print3 = st.columns([2, 1, 2])
                            with col_print2:
                                if st.button("🖨️ 보고서 인쇄", use_container_width=True):
                                    st.markdown("""
                                    <div class="highlight-box-blue">
                                    <strong>인쇄 안내:</strong><br>
                                    브라우저의 인쇄 기능(Ctrl+P 또는 Cmd+P)을 사용하여 이 페이지를 인쇄할 수 있습니다.<br>
                                    인쇄 시 입력 필드와 버튼은 자동으로 제외됩니다.
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.code("window.print()", language="javascript")

                            # --- 참고사항 ---
                            st.markdown("---")
                            with st.expander("📝 참고사항"):
                                st.write("#### 💡 비용 산정 기준")
                                st.write("- 위 비용은 **1회 전용 광고 영상**(Dedicated Video) 기준입니다.")
                                st.write("- 단순 언급(Mention)이나 짧은 소개는 30-50% 정도 저렴합니다.")
                                st.write("- 콘텐츠 재사용권(Usage Rights) 포함 시 20-50% 추가 비용 발생")
                                st.write("- 독점 계약(Exclusivity) 시 30-100% 추가 비용 발생 가능")
                                st.write("")
                                st.write("#### 🆕 v4.0 개선사항")
                                st.write("- **참여 질 보정**: 댓글/좋아요 비율로 커뮤니티 질 평가 (0.9x ~ 1.1x)")
                                st.write("- **콘텐츠 포맷 프리미엄**: 광고 유형별 차등 가격 (1.0x ~ 1.5x)")
                                st.write("- **최근 90일 CPM**: 죽은 채널 방지 (향후 구현)")
                                st.write("")
                                st.write("#### ⚠️ 유의사항")
                                st.write("- 최종 금액은 인플루언서와 직접 협의하여 결정하시기 바랍니다.")
                                st.write("- 이 툴은 참고용 가이드라인을 제공하며, 법적 구속력이 없습니다.")
                                st.caption("**데이터 출처**: PageOne Formula, Shopify, Descript, ADOPTER Media (2024-2025)")

                        else:
                            st.warning("⚠️ 최근 영상 정보를 가져올 수 없습니다.")

else:
    st.info("⚠️ 서비스 설정이 완료되지 않았습니다. 관리자에게 문의하세요.")

# 푸터
st.markdown("---")
st.caption("Made with ❤️ | 유튜브 인플루언서 검색 엔진 v4.0 (2025)")
