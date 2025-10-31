"""
유튜브 인플루언서 검색 엔진
사용자가 유튜브 링크를 입력하면 채널 정보를 분석하고 광고 비용을 산출합니다.
"""

import streamlit as st
import requests
import re
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="유튜브 인플루언서 검색 엔진",
    page_icon="🎬",
    layout="wide"
)

# 제목
st.title("🎬 유튜브 인플루언서 검색 엔진")
st.write("유튜브 채널 링크를 입력하면 광고 비용을 산출해드립니다!")

# API 키 입력 (사이드바에 배치)
st.sidebar.header("⚙️ 설정")
api_key = st.sidebar.text_input(
    "YouTube API 키를 입력하세요", 
    type="password",
    help="Google Cloud Console에서 발급받은 API 키를 입력하세요"
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

def estimate_ad_cost(subscriber_count, avg_views, engagement_rate):
    """
    광고 비용 산출 로직
    
    기준:
    1. 기본 비용: 평균 조회수 기준
       - 조회수당 10원 (예: 10만 조회수 = 100만원)
    
    2. 구독자 보정
       - 10만 이하: 0.8배
       - 10만~50만: 1.0배
       - 50만~100만: 1.2배
       - 100만 이상: 1.5배
    
    3. 참여율 보정
       - 3% 이하: 0.9배
       - 3~5%: 1.0배
       - 5~7%: 1.1배
       - 7% 이상: 1.2배
    """
    # 기본 비용 (조회수당 10원)
    base_cost = avg_views * 10
    
    # 구독자 수 보정
    if subscriber_count < 100000:
        subscriber_multiplier = 0.8
    elif subscriber_count < 500000:
        subscriber_multiplier = 1.0
    elif subscriber_count < 1000000:
        subscriber_multiplier = 1.2
    else:
        subscriber_multiplier = 1.5
    
    # 참여율 보정
    if engagement_rate < 3:
        engagement_multiplier = 0.9
    elif engagement_rate < 5:
        engagement_multiplier = 1.0
    elif engagement_rate < 7:
        engagement_multiplier = 1.1
    else:
        engagement_multiplier = 1.2
    
    # 최종 비용 계산
    final_cost = base_cost * subscriber_multiplier * engagement_multiplier
    
    return {
        'base_cost': int(base_cost),
        'subscriber_multiplier': subscriber_multiplier,
        'engagement_multiplier': engagement_multiplier,
        'final_cost': int(final_cost)
    }

def format_number(num):
    """
    숫자를 읽기 쉬운 형식으로 변환 (예: 1234567 -> 1,234,567)
    """
    return f"{num:,}"

# 메인 로직
if api_key:
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
                            
                            cost_data = estimate_ad_cost(
                                subscriber_count, 
                                avg_views, 
                                avg_engagement_rate
                            )
                            
                            # 비용 계산 과정 설명
                            st.write("**비용 산출 방식:**")
                            st.write(f"1️⃣ **기본 비용**: {format_number(cost_data['base_cost'])}원 (평균 조회수 × 10원)")
                            st.write(f"2️⃣ **구독자 수 보정**: ×{cost_data['subscriber_multiplier']}")
                            st.write(f"3️⃣ **참여율 보정**: ×{cost_data['engagement_multiplier']}")
                            
                            # 최종 비용
                            st.markdown("---")
                            final_cost = cost_data['final_cost']
                            min_cost = int(final_cost * 0.8)
                            max_cost = int(final_cost * 1.2)
                            
                            st.success(f"### 💵 추천 광고 비용: {format_number(min_cost)}원 ~ {format_number(max_cost)}원")
                            st.info(f"**평균 예상 비용: {format_number(final_cost)}원**")
                            
                            # 추가 정보
                            st.markdown("---")
                            st.write("**📝 참고사항:**")
                            st.write("- 위 비용은 채널의 데이터를 바탕으로 산출된 **참고 금액**입니다.")
                            st.write("- 실제 광고 비용은 콘텐츠 유형, 광고 형태, 계약 조건 등에 따라 달라질 수 있습니다.")
                            st.write("- 인플루언서와 직접 협의하여 최종 금액을 결정하시기 바랍니다.")
                        
                        else:
                            st.warning("⚠️ 최근 영상 정보를 가져올 수 없습니다.")

else:
    st.info("👈 왼쪽 사이드바에 YouTube API 키를 입력해주세요!")
    
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

# 푸터
st.markdown("---")
st.caption("Made with ❤️ | 유튜브 인플루언서 검색 엔진 v1.0")
