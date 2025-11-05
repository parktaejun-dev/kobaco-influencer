"""
유튜브 인플루언서 검색 엔진 v3.1 (시각화 강화)
사용자가 유튜브 링크를 입력하면 채널 정보를 분석하고 광고 비용을 산출합니다.
- 사이드바 제거 (단일 화면)
- '한국 시장 기준' 로직만 사용
- 최근 영상 분석 및 비용 산출 로직 시각화 (차트 추가)
"""

import streamlit as st
import requests
import re
from datetime import datetime
import os  # 환경변수 사용을 위해 추가
import cost_calculator # 광고비 계산 모듈 import
import pandas as pd # 시각화를 위한 pandas import

# 페이지 설정
st.set_page_config(
    page_title="유튜브 인플루언서 검색 엔진",
    page_icon="🎬",
    layout="wide"
)

# --- (시각적 요소를 위한 스타일) ---
st.markdown("""
<style>
.cost-range-bar {
    width: 100%;
    background-color: #f0f2f6;
    border-radius: 10px;
    padding: 15px;
    text-align: center;
    border: 1px solid #ddd;
}
.cost-range-line {
    width: 100%;
    height: 10px;
    background: linear-gradient(90deg, #b0c4de 0%, #4682b4 50%, #b0c4de 100%);
    border-radius: 5px;
    margin: 10px 0;
    position: relative;
}
.cost-label {
    font-size: 1.1em;
    font-weight: bold;
    color: #333;
}
.cost-minmax {
    display: flex;
    justify-content: space-between;
    font-size: 0.9em;
    color: #555;
    padding: 0 5px;
}
.cost-avg {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    top: -25px;
    font-weight: bold;
    font-size: 1.2em;
    color: #000;
    background-color: white;
    padding: 2px 8px;
    border-radius: 5px;
    border: 1px solid #4682b4;
}
</style>
""", unsafe_allow_html=True)


# --- (제목) ---
st.title("🎬 유튜브 인플루언서 검색 엔진 (v3.1)")
st.write("유튜브 채널 링크를 입력하면 광고 비용을 산출해드립니다! (한국 시장 기준)")

# --- (API 키 로드) ---
try:
    # 방법 1: Streamlit secrets에서 가져오기 (Streamlit Cloud)
    api_key = st.secrets["YOUTUBE_API_KEY"]
    api_key_loaded = True
except:
    try:
        # 방법 2: 환경변수에서 가져오기 (Hugging Face Spaces)
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
    st.info("💡 관리자: API_KEY_SETUP_GUIDE.md 파일을 참고하여 API 키를 설정하세요.")

# --- (함수 정의: API 호출 및 데이터 처리) ---

def extract_channel_id(url):
    """
    유튜브 URL에서 채널 ID를 추출하는 함수
    한글 등 유니코드 문자를 포함한 여러 형식의 URL을 지원합니다
    """
    # 채널 ID 패턴 (UC... 형식)
    channel_id_pattern = r'youtube\.com/channel/([a-zA-Z0-9_-]+)'
    
    # 핸들(@), /c/, /user/ 패턴 (한글 등 유니코드 문자 지원)
    # [^/?&]+ : URL 구분자인 슬래시(/), 물음표(?), 앰퍼샌드(&)가 아닌 모든 문자를 의미
    unicode_patterns = [
        r'youtube\.com/@([^/?&]+)',          # /@username 형식 (한글 핸들 지원)
        r'youtube\.com/c/([^/?&]+)',         # /c/name 형식 (한글 이름 지원)
        r'youtube\.com/user/([^/?&]+)',      # /user/name 형식 (한글 이름 지원)
    ]
    
    # 먼저 채널 ID 패턴 검사
    match = re.search(channel_id_pattern, url)
    if match:
        return match.group(1), channel_id_pattern
    
    # 다음으로 유니코드 지원 패턴 검사
    for pattern in unicode_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), pattern
    
    return None, None

def get_channel_info_by_id(channel_id, api_key):
    """
    채널 ID로 채널 정보를 가져오는 함수
    """
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
    """
    사용자 이름으로 채널 정보를 가져오는 함수
    """
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        'part': 'snippet,statistics,contentDetails',
        'forHandle': username,  # 새로운 핸들 방식
        'key': api_key
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if 'items' in data and len(data['items']) > 0:
        return data['items'][0]
    return None

def get_recent_videos(channel_id, api_key, max_results=10):
    """
    최근 업로드된 비디오 정보를 가져오는 함수
    """
    # 먼저 채널의 업로드 재생목록 ID를 가져옵니다
    channel_info = get_channel_info_by_id(channel_id, api_key)
    if not channel_info:
        return []
    
    uploads_playlist_id = channel_info['contentDetails']['relatedPlaylists']['uploads']
    
    # 업로드 재생목록에서 최근 동영상 가져오기
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
    
    # 각 비디오의 상세 정보 가져오기
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
    """
    참여율(Engagement Rate) 계산
    참여율 = (좋아요 + 댓글) / 조회수 * 100
    """
    views = int(video_stats.get('viewCount', 0))
    likes = int(video_stats.get('likeCount', 0))
    comments = int(video_stats.get('commentCount', 0))
    
    if views == 0:
        return 0
    
    engagement_rate = ((likes + comments) / views) * 100
    return round(engagement_rate, 2)

def calculate_average_views(videos):
    """
    최근 영상들의 평균 조회수 계산
    """
    if not videos:
        return 0
    
    total_views = sum(int(video['statistics'].get('viewCount', 0)) for video in videos)
    return total_views // len(videos)

def format_number(num):
    """
    숫자를 읽기 쉬운 형식으로 변환 (예: 1234567 -> 1,234,567)
    """
    return f"{num:,}"

# --- (메인 로직) ---
if api_key_loaded and api_key:
    
    # 유튜브 URL 입력
    youtube_url = st.text_input(
        "🔗 유튜브 채널 URL을 입력하세요",
        placeholder="예: https://www.youtube.com/@channelname 또는 https://www.youtube.com/channel/UC..."
    )
    
    if youtube_url:
        with st.spinner("채널 정보를 가져오는 중..."):
            # URL에서 채널 ID 추출
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
                    # --- (채널 기본 정보 표시) ---
                    st.success("✅ 채널 정보를 성공적으로 가져왔습니다!")
                    
                    stats = channel_info['statistics']
                    snippet = channel_info['snippet']
                    
                    subscriber_count = int(stats.get('subscriberCount', 0))
                    video_count = int(stats.get('videoCount', 0))
                    total_view_count = int(stats.get('viewCount', 0))
                    
                    # cost_calculator 모듈 사용
                    tier_name, tier_range = cost_calculator.get_influencer_tier(subscriber_count)
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        # 채널 썸네일
                        if 'thumbnails' in snippet:
                            st.image(snippet['thumbnails']['high']['url'], width=200)
                    
                    with col2:
                        st.subheader(snippet['title'])
                        st.markdown(f"**등급:** {tier_name} ({tier_range} 구독자)")
                        st.write(f"**설명:** {snippet.get('description', 'N/A')[:200]}...")
                        st.write(f"**채널 생성일:** {snippet['publishedAt'][:10]}")
                    
                    # --- (채널 통계) ---
                    st.markdown("---")
                    st.subheader("📊 채널 통계")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("구독자 수", format_number(subscriber_count))
                    col2.metric("총 동영상 수", format_number(video_count))
                    col3.metric("총 조회수", format_number(total_view_count))
                    
                    # --- (최근 영상 분석) ---
                    st.markdown("---")
                    st.subheader("🎥 최근 영상 분석 (최근 10개)")
                    
                    with st.spinner("최근 영상 정보를 분석하는 중..."):
                        recent_videos = get_recent_videos(
                            channel_info['id'], 
                            api_key, 
                            max_results=10
                        )
                        
                        if recent_videos:
                            # 평균 조회수/참여율 계산
                            avg_views = calculate_average_views(recent_videos)
                            engagement_rates = [
                                calculate_engagement_rate(video['statistics']) 
                                for video in recent_videos
                            ]
                            avg_engagement_rate = sum(engagement_rates) / len(engagement_rates)
                            
                            # 지표 표시
                            col1, col2 = st.columns(2)
                            col1.metric("평균 조회수", format_number(avg_views))
                            col2.metric("평균 참여율", f"{avg_engagement_rate:.2f}%", help="참여율 = (좋아요 + 댓글) / 조회수 * 100")
                            
                            # --- (시각화 1: 최근 영상 데이터 차트) ---
                            video_data = []
                            for i, video in enumerate(recent_videos, 1):
                                video_stats = video['statistics']
                                video_snippet = video['snippet']
                                
                                title = f"{i}. {video_snippet['title'][:25]}..." # 제목 25자로 자르기
                                views = int(video_stats.get('viewCount', 0))
                                engagement = calculate_engagement_rate(video_stats)
                                
                                video_data.append({'영상 (최신순)': title, '조회수': views, '참여율 (%)': engagement})
                            
                            # 데이터가 있을 경우에만 차트 생성
                            if video_data:
                                df_videos = pd.DataFrame(video_data)
                                
                                st.write("")
                                st.write("##### 최근 10개 영상 조회수")
                                st.bar_chart(df_videos.set_index('영상 (최신순)')['조회수'])
                                
                                st.write("##### 최근 10개 영상 참여율 (%)")
                                st.line_chart(df_videos.set_index('영상 (최신순)')['참여율 (%)'])

                                with st.expander("최근 영상 상세 데이터 보기"):
                                    st.dataframe(df_videos)
                            
                            # --- (광고 비용 산출 - 한국 기준) ---
                            st.markdown("---")
                            st.subheader("💰 1회 광고 의뢰 적정 비용 (한국 시장 기준)")
                            
                            # cost_calculator 모듈 사용
                            cost_data = cost_calculator.estimate_ad_cost_korea(
                                subscriber_count, 
                                avg_views, 
                                avg_engagement_rate
                            )
                            
                            final_cost = cost_data['final_cost']
                            min_cost = int(final_cost * 0.85)
                            max_cost = int(final_cost * 1.15)
                            
                            # --- (시각화 2: 최종 비용 추천 범위) ---
                            st.markdown(f"""
                            <div class="cost-range-bar">
                                <div class="cost-label">추천 광고 비용 범위</div>
                                <div class="cost-range-line">
                                    <div class="cost-avg">평균 {format_number(final_cost)}원</div>
                                </div>
                                <div class="cost-minmax">
                                    <span>최소 {format_number(min_cost)}원</span>
                                    <span>최대 {format_number(max_cost)}원</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.write("")
                            st.info(f"""
                            **[비용 산출 상세]**\n
                            - **CPM 기반 비용**: {format_number(cost_data['base_cost_cpm'])}원 (한국 시장 CPM {format_number(cost_data['cpm_used'])}원/1,000뷰)\n
                            - **티어 최소 금액**: {format_number(cost_data['tier_base'])}원 ({tier_name} 기준)\n
                            - **기본 비용 (Max)**: {format_number(cost_data['base_cost'])}원\n
                            - **참여율 보정**: ×{cost_data['engagement_multiplier']} ({cost_data['engagement_level']})\n
                            - **한국 시장 조정**: ×{cost_data['korea_adjustment']}
                            """)

                            # --- (시각화 3: 비용 구성 요소 차트) ---
                            st.write("##### 비용 구성 분석 (참고)")
                            base_val = cost_data['base_cost']
                            # 보정/조정액이 음수가 되지 않도록 min(0, ...) 처리
                            multiplier_val = max(0, final_cost - base_val) 
                            
                            cost_comp_data = {
                                '구성 요소': ['기본 비용 (CPM/티어)', '보정/조정액 (참여율, 시장)'],
                                '금액 (원)': [base_val, multiplier_val]
                            }
                            
                            # 데이터가 있을 경우에만 차트 생성
                            if base_val > 0 or multiplier_val > 0:
                                df_cost_comp = pd.DataFrame(cost_comp_data)
                                st.bar_chart(df_cost_comp.set_index('구성 요소'), use_container_width=True)

                            # --- (참고사항) ---
                            st.markdown("---")
                            with st.expander("📝 참고사항"):
                                st.write("- 위 비용은 **1회 전용 광고 영상**(Dedicated Video) 기준입니다.")
                                st.write("- 단순 언급(Mention)이나 짧은 소개는 30-50% 정도 저렴합니다.")
                                st.write("- 콘텐츠 재사용권(Usage Rights)이 포함되면 20-50% 추가 비용이 발생합니다.")
                                st.write("- 독점 계약(Exclusivity) 시 30-100% 추가 비용이 발생할 수 있습니다.")
                                st.write("- 최종 금액은 인플루언서와 직접 협의하여 결정하시기 바랍니다.")
                                st.caption("**데이터 출처**: PageOne Formula, Shopify, Descript, ADOPTER Media (2024-2025)")
                        
                        else:
                            st.warning("⚠️ 최근 영상 정보를 가져올 수 없습니다.")

else:
    st.info("⚠️ 서비스 설정이 완료되지 않았습니다. 관리자에게 문의하세요.")
    
    # 관리자용 안내
    with st.expander("🔧 관리자용: API 키 설정 및 로직 안내"):
        st.write("#### API 키 설정 방법")
        st.write("Streamlit Cloud 또는 Hugging Face Spaces의 'Secrets'에 `YOUTUBE_API_KEY`로 본인의 API 키를 입력하세요.")
        
        st.write("#### 단가 산정 로직 (v3.1 한국 기준)")
        st.write("수정된 글로벌 벤치마크(2025)를 기반으로 한국 시장 특성(75-85%)을 반영하여 계산합니다.")
        st.write("- **CPM**: 1,000뷰당 약 39,000원 (글로벌 기준)")
        st.write("- **티어별 최소 금액**: 나노(35만) ~ 메가(4,750만)")
        st.write("- **조정**: 참여율(0.85~1.5배), 한국 시장(0.75~0.85배) 적용")

# 푸터
st.markdown("---")
st.caption("Made with ❤️ | 유튜브 인플루언서 검색 엔진 v3.1 (2025 벤치마크 & 시각화 강화)")

