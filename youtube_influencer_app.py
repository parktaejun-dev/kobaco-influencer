"""
유튜브 인플루언서 검색 엔진 v2.0
사용자가 유튜브 링크를 입력하면 채널 정보를 분석하고 광고 비용을 산출합니다.
글로벌 표준 CPM 기반 단가 산정 로직 적용 (2024-2025 기준)
"""

import streamlit as st
import requests
import re
from datetime import datetime
import os  # 환경변수 사용을 위해 추가

# 페이지 설정
st.set_page_config(
    page_title="유튜브 인플루언서 검색 엔진",
    page_icon="🎬",
    layout="wide"
)

# 제목
st.title("🎬 유튜브 인플루언서 검색 엔진")
st.write("유튜브 채널 링크를 입력하면 광고 비용을 산출해드립니다!")

# API 키 가져오기 
# Streamlit Cloud와 Hugging Face Spaces 모두 지원
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

# API 키 로딩 실패 시 오류 메시지 표시
if not api_key_loaded:
    st.error("⚠️ API 키가 설정되지 않았습니다. 관리자에게 문의하세요.")
    st.info("💡 관리자: API_KEY_SETUP_GUIDE.md 파일을 참고하여 API 키를 설정하세요.")

# 설정 옵션 (사이드바에 배치)
st.sidebar.header("⚙️ 설정")
st.sidebar.subheader("💰 비용 산정 방식")
pricing_method = st.sidebar.radio(
    "선택하세요",
    ["글로벌 표준 (CPM 기반)", "한국 시장 기준"],
    help="글로벌 표준은 해외 서비스들의 평균 단가를, 한국 시장은 국내 특성을 반영합니다"
)

def extract_channel_id(url):
    """
    유튜브 URL에서 채널 ID를 추출하는 함수
    여러 형식의 URL을 지원합니다
    """
    # 채널 ID 패턴들
    patterns = [
        r'youtube\.com/channel/([a-zA-Z0-9_-]+)',  # /channel/ID 형식
        r'youtube\.com/@([a-zA-Z0-9_-]+)',          # /@username 형식
        r'youtube\.com/c/([a-zA-Z0-9_-]+)',         # /c/name 형식
        r'youtube\.com/user/([a-zA-Z0-9_-]+)',      # /user/name 형식
    ]
    
    for pattern in patterns:
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

def get_influencer_tier(subscriber_count):
    """
    구독자 수에 따른 인플루언서 등급 분류
    글로벌 표준 기준
    """
    if subscriber_count < 10000:
        return "나노 (Nano)", "1K-10K"
    elif subscriber_count < 100000:
        return "마이크로 (Micro)", "10K-100K"
    elif subscriber_count < 500000:
        return "미드티어 (Mid-tier)", "100K-500K"
    elif subscriber_count < 1000000:
        return "매크로 (Macro)", "500K-1M"
    else:
        return "메가 (Mega)", "1M+"

def estimate_ad_cost_global(subscriber_count, avg_views, engagement_rate):
    """
    글로벌 표준 광고 비용 산출 로직 (CPM 기반)
    
    기준: 2024-2025 해외 인플루언서 마케팅 시장 데이터
    출처: Influencer Marketing Hub, Business of Apps, HypeAuditor 등
    
    1. CPM (Cost Per Mille = 1,000뷰당 비용)
       - YouTube 인플루언서 평균 CPM: $50-$100 (65,000-130,000원)
       - 일반 광고 CPM의 약 2배 (신뢰도 프리미엄)
    
    2. 구독자 규모별 기본 단가
       - 나노 (1K-10K): $200-$500
       - 마이크로 (10K-100K): $800-$1,500
       - 미드티어 (100K-500K): $3,000-$5,000
       - 매크로 (500K-1M): $5,000-$10,000
       - 메가 (1M+): $8,000-$20,000+
    
    3. 참여율 보정
       - 참여율이 높을수록 실제 전환율이 높아 가치 상승
    """
    
    # 1. CPM 기반 기본 비용 계산
    # 평균 CPM: $75 (약 97,500원) - 중간값 사용
    cpm_krw = 97500  # 1,000뷰당 비용 (원화)
    base_cost_cpm = (avg_views / 1000) * cpm_krw
    
    # 2. 구독자 규모별 최소 보장 금액 (티어별 기준가)
    if subscriber_count < 10000:
        tier_base = 350000  # $200-500의 중간값 약 $350 = 455,000원
    elif subscriber_count < 100000:
        tier_base = 1500000  # $800-1,500의 중간값 약 $1,150 = 1,495,000원
    elif subscriber_count < 500000:
        tier_base = 5200000  # $3,000-5,000의 중간값 약 $4,000 = 5,200,000원
    elif subscriber_count < 1000000:
        tier_base = 9750000  # $5,000-10,000의 중간값 약 $7,500 = 9,750,000원
    else:
        tier_base = 18200000  # $8,000-20,000의 중간값 약 $14,000 = 18,200,000원
    
    # 3. CPM 기반 금액과 티어 기본 금액 중 높은 값 선택
    base_cost = max(base_cost_cpm, tier_base)
    
    # 4. 참여율 보정 (인플루언서의 실제 영향력 반영)
    # 참여율 1% 이하: 매우 낮음 (0.85배)
    # 참여율 1-2%: 낮음 (0.9배)
    # 참여율 2-3%: 보통 (1.0배)
    # 참여율 3-5%: 양호 (1.1배)
    # 참여율 5-7%: 높음 (1.2배)
    # 참여율 7% 이상: 매우 높음 (1.3배)
    if engagement_rate < 1:
        engagement_multiplier = 0.85
        engagement_level = "매우 낮음"
    elif engagement_rate < 2:
        engagement_multiplier = 0.9
        engagement_level = "낮음"
    elif engagement_rate < 3:
        engagement_multiplier = 1.0
        engagement_level = "보통"
    elif engagement_rate < 5:
        engagement_multiplier = 1.1
        engagement_level = "양호"
    elif engagement_rate < 7:
        engagement_multiplier = 1.2
        engagement_level = "높음"
    else:
        engagement_multiplier = 1.3
        engagement_level = "매우 높음"
    
    # 5. 최종 비용 계산
    final_cost = int(base_cost * engagement_multiplier)
    
    return {
        'base_cost_cpm': int(base_cost_cpm),
        'tier_base': tier_base,
        'base_cost': int(base_cost),
        'engagement_multiplier': engagement_multiplier,
        'engagement_level': engagement_level,
        'final_cost': final_cost,
        'cpm_used': cpm_krw
    }

def estimate_ad_cost_korea(subscriber_count, avg_views, engagement_rate):
    """
    한국 시장 기준 광고 비용 산출 로직
    
    한국 시장 특성:
    - 소셜미디어 침투율 93.4% (세계 3위)
    - 2025년 인플루언서 마케팅 지출: $489M
    - K-뷰티, K-푸드, K-팝 등 한류의 영향
    - 글로벌 대비 약간 낮은 단가 (약 70-80% 수준)
    
    기본 로직: 글로벌 표준에서 한국 시장 특성 반영
    """
    
    # 글로벌 기준 먼저 계산
    global_cost = estimate_ad_cost_global(subscriber_count, avg_views, engagement_rate)
    
    # 한국 시장 조정 계수 (0.75 = 글로벌의 75% 수준)
    # 이유: 한국은 시장 규모가 작고, 인플루언서 공급이 많아 가격 경쟁이 심함
    korea_adjustment = 0.75
    
    # 나노/마이크로 인플루언서는 한국에서 더 활발하므로 85% 적용
    if subscriber_count < 100000:
        korea_adjustment = 0.85
    
    # 최종 비용 계산
    final_cost = int(global_cost['final_cost'] * korea_adjustment)
    
    return {
        'base_cost_cpm': int(global_cost['base_cost_cpm'] * korea_adjustment),
        'tier_base': int(global_cost['tier_base'] * korea_adjustment),
        'base_cost': int(global_cost['base_cost'] * korea_adjustment),
        'engagement_multiplier': global_cost['engagement_multiplier'],
        'engagement_level': global_cost['engagement_level'],
        'final_cost': final_cost,
        'cpm_used': int(global_cost['cpm_used'] * korea_adjustment),
        'korea_adjustment': korea_adjustment
    }

def format_number(num):
    """
    숫자를 읽기 쉬운 형식으로 변환 (예: 1234567 -> 1,234,567)
    """
    return f"{num:,}"

# 메인 로직
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
                if 'channel/' in pattern:
                    channel_info = get_channel_info_by_id(channel_identifier, api_key)
                else:
                    channel_info = get_channel_info_by_username(channel_identifier, api_key)
                
                if not channel_info:
                    st.error("❌ 채널 정보를 가져올 수 없습니다. URL을 확인해주세요.")
                else:
                    # 채널 통계 추출
                    stats = channel_info['statistics']
                    snippet = channel_info['snippet']
                    
                    subscriber_count = int(stats.get('subscriberCount', 0))
                    video_count = int(stats.get('videoCount', 0))
                    total_view_count = int(stats.get('viewCount', 0))
                    
                    # 인플루언서 등급
                    tier_name, tier_range = get_influencer_tier(subscriber_count)
                    
                    # 채널 기본 정보 표시
                    st.success("✅ 채널 정보를 성공적으로 가져왔습니다!")
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        # 채널 썸네일
                        if 'thumbnails' in snippet:
                            thumbnail_url = snippet['thumbnails']['high']['url']
                            st.image(thumbnail_url, width=200)
                    
                    with col2:
                        st.subheader(snippet['title'])
                        st.markdown(f"**등급:** {tier_name} ({tier_range} 구독자)")
                        st.write(f"**설명:** {snippet.get('description', 'N/A')[:200]}...")
                        st.write(f"**채널 생성일:** {snippet['publishedAt'][:10]}")
                    
                    # 채널 통계
                    st.markdown("---")
                    st.subheader("📊 채널 통계")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            label="구독자 수",
                            value=format_number(subscriber_count)
                        )
                    
                    with col2:
                        st.metric(
                            label="총 동영상 수",
                            value=format_number(video_count)
                        )
                    
                    with col3:
                        st.metric(
                            label="총 조회수",
                            value=format_number(total_view_count)
                        )
                    
                    # 최근 영상 분석
                    st.markdown("---")
                    st.subheader("🎥 최근 영상 분석 (최근 10개)")
                    
                    with st.spinner("최근 영상 정보를 분석하는 중..."):
                        recent_videos = get_recent_videos(
                            channel_info['id'], 
                            api_key, 
                            max_results=10
                        )
                        
                        if recent_videos:
                            # 평균 조회수 계산
                            avg_views = calculate_average_views(recent_videos)
                            
                            # 평균 참여율 계산
                            engagement_rates = [
                                calculate_engagement_rate(video['statistics']) 
                                for video in recent_videos
                            ]
                            avg_engagement_rate = sum(engagement_rates) / len(engagement_rates)
                            
                            # 지표 표시
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric(
                                    label="평균 조회수",
                                    value=format_number(avg_views)
                                )
                            
                            with col2:
                                st.metric(
                                    label="평균 참여율",
                                    value=f"{avg_engagement_rate:.2f}%",
                                    help="참여율 = (좋아요 + 댓글) / 조회수 * 100"
                                )
                            
                            # 최근 영상 목록
                            with st.expander("최근 영상 상세 보기"):
                                for i, video in enumerate(recent_videos, 1):
                                    video_stats = video['statistics']
                                    video_snippet = video['snippet']
                                    
                                    views = int(video_stats.get('viewCount', 0))
                                    likes = int(video_stats.get('likeCount', 0))
                                    comments = int(video_stats.get('commentCount', 0))
                                    engagement = calculate_engagement_rate(video_stats)
                                    
                                    st.write(f"**{i}. {video_snippet['title']}**")
                                    st.write(f"   - 조회수: {format_number(views)} | 좋아요: {format_number(likes)} | 댓글: {format_number(comments)} | 참여율: {engagement}%")
                                    st.write("")
                            
                            # 광고 비용 산출
                            st.markdown("---")
                            st.subheader("💰 1회 광고 의뢰 적정 비용")
                            
                            # 선택한 방식에 따라 비용 계산
                            if pricing_method == "글로벌 표준 (CPM 기반)":
                                cost_data = estimate_ad_cost_global(
                                    subscriber_count, 
                                    avg_views, 
                                    avg_engagement_rate
                                )
                                
                                st.info("📌 **글로벌 표준 방식 (CPM 기반)**")
                                st.write("해외 주요 인플루언서 마케팅 플랫폼들의 평균 단가를 기준으로 산정합니다.")
                                st.write("출처: Influencer Marketing Hub, Business of Apps, HypeAuditor (2024-2025)")
                                
                                # 비용 계산 과정 설명
                                st.write("")
                                st.write("**📊 비용 산출 방식:**")
                                st.write(f"1️⃣ **CPM 기반 비용**: {format_number(cost_data['base_cost_cpm'])}원")
                                st.write(f"   └ 평균 조회수 {format_number(avg_views)} × CPM {format_number(cost_data['cpm_used'])}원/1,000뷰")
                                st.write(f"2️⃣ **티어 최소 금액**: {format_number(cost_data['tier_base'])}원 ({tier_name} 기준)")
                                st.write(f"3️⃣ **기본 비용**: {format_number(cost_data['base_cost'])}원 (위 두 값 중 높은 값)")
                                st.write(f"4️⃣ **참여율 보정**: ×{cost_data['engagement_multiplier']} ({cost_data['engagement_level']})")
                                
                            else:  # 한국 시장 기준
                                cost_data = estimate_ad_cost_korea(
                                    subscriber_count, 
                                    avg_views, 
                                    avg_engagement_rate
                                )
                                
                                st.info("📌 **한국 시장 기준 방식**")
                                st.write("글로벌 표준을 기반으로 한국 시장 특성을 반영합니다.")
                                st.write("한국은 인플루언서 공급이 풍부하고 시장 규모가 작아 글로벌 대비 75-85% 수준")
                                
                                # 비용 계산 과정 설명
                                st.write("")
                                st.write("**📊 비용 산출 방식:**")
                                st.write(f"1️⃣ **CPM 기반 비용**: {format_number(cost_data['base_cost_cpm'])}원")
                                st.write(f"   └ 한국 시장 CPM {format_number(cost_data['cpm_used'])}원/1,000뷰")
                                st.write(f"2️⃣ **티어 최소 금액**: {format_number(cost_data['tier_base'])}원 ({tier_name} 기준)")
                                st.write(f"3️⃣ **기본 비용**: {format_number(cost_data['base_cost'])}원")
                                st.write(f"4️⃣ **참여율 보정**: ×{cost_data['engagement_multiplier']} ({cost_data['engagement_level']})")
                                st.write(f"5️⃣ **한국 시장 조정**: ×{cost_data['korea_adjustment']}")
                            
                            # 최종 비용
                            st.markdown("---")
                            final_cost = cost_data['final_cost']
                            min_cost = int(final_cost * 0.85)
                            max_cost = int(final_cost * 1.15)
                            
                            st.success(f"### 💵 추천 광고 비용: {format_number(min_cost)}원 ~ {format_number(max_cost)}원")
                            st.info(f"**평균 예상 비용: {format_number(final_cost)}원**")
                            
                            # 비교 정보 (글로벌 vs 한국)
                            if pricing_method == "한국 시장 기준":
                                global_cost_data = estimate_ad_cost_global(subscriber_count, avg_views, avg_engagement_rate)
                                st.write("")
                                st.write(f"💡 **참고**: 글로벌 표준 기준으로는 약 {format_number(global_cost_data['final_cost'])}원")
                            
                            # 추가 정보
                            st.markdown("---")
                            st.write("**📝 참고사항:**")
                            st.write("- 위 비용은 **1회 전용 광고 영상**(Dedicated Video) 기준입니다.")
                            st.write("- 단순 언급(Mention)이나 짧은 소개는 30-50% 정도 저렴합니다.")
                            st.write("- 콘텐츠 재사용권(Usage Rights)이 포함되면 20-50% 추가 비용이 발생합니다.")
                            st.write("- 독점 계약(Exclusivity) 시 30-100% 추가 비용이 발생할 수 있습니다.")
                            st.write("- 최종 금액은 인플루언서와 직접 협의하여 결정하시기 바랍니다.")
                            
                            # 데이터 출처
                            st.markdown("---")
                            st.caption("**데이터 출처**: Influencer Marketing Hub, Business of Apps, HypeAuditor, Collabstr (2024-2025)")
                        
                        else:
                            st.warning("⚠️ 최근 영상 정보를 가져올 수 없습니다.")

else:
    st.info("⚠️ 서비스 설정이 완료되지 않았습니다. 관리자에게 문의하세요.")
    
    # 관리자용 API 키 설정 안내
    with st.expander("🔧 관리자용: API 키 설정 방법"):
        st.write("""
        ### 로컬 개발 환경
        
        1. 프로젝트 폴더에 `.streamlit` 폴더 생성
        2. `.streamlit/secrets.toml` 파일 생성
        3. 아래 내용 입력:
        
        ```toml
        YOUTUBE_API_KEY = "여기에_API_키_입력"
        ```
        
        ### Streamlit Cloud 배포 시
        
        1. Streamlit Cloud 대시보드에서 앱 선택
        2. Settings → Secrets 클릭
        3. 아래 내용 입력:
        
        ```toml
        YOUTUBE_API_KEY = "여기에_API_키_입력"
        ```
        
        ### Hugging Face Spaces 배포 시
        
        1. Space Settings로 이동
        2. Repository secrets 섹션 찾기
        3. New secret 클릭
        4. Name: `YOUTUBE_API_KEY`
        5. Value: 본인의 API 키 입력
        """)
    
    # API 키 발급 안내
    with st.expander("📚 YouTube API 키 발급 방법"):
        st.write("""
        1. **Google Cloud Console 접속**
           - https://console.cloud.google.com 방문
        
        2. **새 프로젝트 만들기**
           - 상단의 프로젝트 선택 → '새 프로젝트' 클릭
           - 프로젝트 이름 입력 후 만들기
        
        3. **YouTube Data API v3 활성화**
           - 왼쪽 메뉴에서 'API 및 서비스' → '라이브러리' 선택
           - 'YouTube Data API v3' 검색
           - 'YouTube Data API v3' 클릭 후 '사용' 버튼 클릭
        
        4. **API 키 만들기**
           - 왼쪽 메뉴에서 'API 및 서비스' → '사용자 인증 정보' 선택
           - 상단의 '+ 사용자 인증 정보 만들기' → 'API 키' 선택
           - 생성된 API 키를 복사
        
        5. **API 키 입력**
           - 복사한 API 키를 왼쪽 사이드바의 입력창에 붙여넣기
        """)
    
    # 단가 산정 로직 설명
    with st.expander("💡 단가 산정 로직 비교"):
        st.write("""
        ### 글로벌 표준 (CPM 기반)
        
        **기준**: 해외 주요 인플루언서 마케팅 플랫폼의 2024-2025 평균 단가
        
        - **CPM**: 1,000뷰당 65,000-130,000원 (평균 97,500원)
        - **티어별 최소 금액**:
          - 나노 (1K-10K): 약 35만원
          - 마이크로 (10K-100K): 약 150만원
          - 미드티어 (100K-500K): 약 520만원
          - 매크로 (500K-1M): 약 975만원
          - 메가 (1M+): 약 1,820만원 이상
        
        **장점**: 국제 표준에 맞춰 해외 브랜드나 글로벌 캠페인에 적합
        
        ---
        
        ### 한국 시장 기준
        
        **기준**: 글로벌 표준을 한국 시장 특성에 맞게 조정
        
        - **조정 계수**: 글로벌 대비 75-85% (구독자 규모에 따라 다름)
        - **이유**: 
          - 한국은 인플루언서 공급이 풍부
          - 시장 규모가 작아 가격 경쟁이 심함
          - 마이크로 인플루언서는 더 활발 (85% 적용)
        
        **장점**: 한국 시장 현실을 반영한 현실적인 가격
        
        ---
        
        **추천**: 
        - 국내 브랜드 → **한국 시장 기준** 선택
        - 해외 브랜드 → **글로벌 표준** 선택
        """)

# 푸터
st.markdown("---")
st.caption("Made with ❤️ | 유튜브 인플루언서 검색 엔진 v2.0 (글로벌 표준 CPM 로직 적용)")
