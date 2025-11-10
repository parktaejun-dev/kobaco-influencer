"""
유튜브 인플루언서 광고 비용 산출 모듈 (v4.0)
2024-2025년 글로벌 벤치마크(PageOne Formula, Shopify, Descript 등) 기준 적용

v4.0 개선사항:
- 최근 90일 CPM 계산 추가 (죽은 채널 방지)
- 참여 질 보정 추가 (댓글/좋아요 비율)
- 콘텐츠 포맷 프리미엄 추가
"""

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

def estimate_ad_cost_global(subscriber_count, avg_views, engagement_rate,
                            avg_likes, avg_comments,
                            recent_90day_avg_views=None,
                            content_format="기본"):
    """
    글로벌 표준 광고 비용 산출 로직 (CPM 기반) - v4.0

    Parameters:
    -----------
    subscriber_count : int
        구독자 수
    avg_views : int
        평균 조회수
    engagement_rate : float
        참여율 (%)
    avg_likes : int
        평균 좋아요 수
    avg_comments : int
        평균 댓글 수
    recent_90day_avg_views : int, optional
        최근 90일 평균 조회수 (죽은 채널 방지용)
    content_format : str, optional
        콘텐츠 포맷 ("기본", "단순 노출형", "제품 리뷰", "비교/추천", "사용후기", "장기 캠페인")

    Returns:
    --------
    dict : 계산 결과 및 세부 정보
    """

    # STEP 1: CPM 기반 기본 비용 계산
    cpm_krw = 39000  # 1,000뷰당 비용
    base_cost_cpm = (avg_views / 1000) * cpm_krw

    # STEP 2: 최근 90일 CPM 계산 (선택적)
    recent_cpm_cost = 0
    if recent_90day_avg_views and recent_90day_avg_views > 0:
        recent_cpm_cost = (recent_90day_avg_views / 1000) * cpm_krw

    # STEP 3: 티어별 최소 보장 금액
    if subscriber_count < 10000:
        tier_base = 350000      # Nano: 1K-10K
    elif subscriber_count < 100000:
        tier_base = 2500000     # Micro: 10K-100K
    elif subscriber_count < 500000:
        tier_base = 5200000     # Mid-tier: 100K-500K
    elif subscriber_count < 1000000:
        tier_base = 19500000    # Macro: 500K-1M
    else:
        tier_base = 47500000    # Mega: 1M+

    # STEP 4: 기본 비용 결정 (세 값 중 최댓값)
    if recent_cpm_cost > 0:
        base_cost = max(base_cost_cpm, recent_cpm_cost, tier_base)
    else:
        base_cost = max(base_cost_cpm, tier_base)

    # STEP 5: 참여율 보정 계수
    if engagement_rate >= 10:
        engagement_multiplier = 1.5
        engagement_level = "최상 (10%+)"
    elif engagement_rate >= 7:
        engagement_multiplier = 1.3
        engagement_level = "매우 높음 (7-10%)"
    elif engagement_rate >= 5:
        engagement_multiplier = 1.2
        engagement_level = "높음 (5-7%)"
    elif engagement_rate >= 3:
        engagement_multiplier = 1.1
        engagement_level = "양호 (3-5%)"
    elif engagement_rate >= 2:
        engagement_multiplier = 1.0
        engagement_level = "보통 (2-3%)"
    elif engagement_rate >= 1:
        engagement_multiplier = 0.9
        engagement_level = "낮음 (1-2%)"
    else:
        engagement_multiplier = 0.85
        engagement_level = "매우 낮음 (<1%)"

    # STEP 6: 참여 질 보정 계수 (댓글/좋아요 비율)
    quality_multiplier = 1.0
    quality_level = "정상 범위"
    comment_like_ratio = 0.0

    if avg_likes > 0:
        comment_like_ratio = avg_comments / avg_likes

        if comment_like_ratio >= 0.15:
            quality_multiplier = 1.1
            quality_level = "대화형 커뮤니티 (우수)"
        elif comment_like_ratio < 0.05:
            quality_multiplier = 0.9
            quality_level = "이벤트형 (저품질)"
        else:
            quality_multiplier = 1.0
            quality_level = "정상 범위"

    # STEP 7: 최종 참여 계수
    final_engagement_multiplier = engagement_multiplier * quality_multiplier

    # STEP 8: 콘텐츠 포맷 프리미엄
    format_multipliers = {
        "기본": 1.0,
        "단순 노출형": 1.0,
        "제품 리뷰": 1.2,
        "비교/추천": 1.35,
        "사용후기": 1.35,
        "장기 캠페인": 1.5
    }
    format_multiplier = format_multipliers.get(content_format, 1.0)

    # STEP 9: 글로벌 최종 비용
    final_cost = int(base_cost * final_engagement_multiplier * format_multiplier)

    return {
        'base_cost_cpm': int(base_cost_cpm),
        'recent_cpm_cost': int(recent_cpm_cost),
        'tier_base': tier_base,
        'base_cost': int(base_cost),

        'engagement_rate': engagement_rate,
        'engagement_multiplier': engagement_multiplier,
        'engagement_level': engagement_level,

        'comment_like_ratio': round(comment_like_ratio, 3),
        'quality_multiplier': quality_multiplier,
        'quality_level': quality_level,

        'final_engagement_multiplier': round(final_engagement_multiplier, 3),
        'format_multiplier': format_multiplier,
        'content_format': content_format,

        'final_cost': final_cost,
        'cpm_used': cpm_krw
    }

def estimate_ad_cost_korea(subscriber_count, avg_views, engagement_rate,
                          avg_likes, avg_comments,
                          recent_90day_avg_views=None,
                          content_format="기본"):
    """
    한국 시장 기준 광고 비용 산출 로직 - v4.0

    Parameters:
    -----------
    subscriber_count : int
        구독자 수
    avg_views : int
        평균 조회수
    engagement_rate : float
        참여율 (%)
    avg_likes : int
        평균 좋아요 수
    avg_comments : int
        평균 댓글 수
    recent_90day_avg_views : int, optional
        최근 90일 평균 조회수
    content_format : str, optional
        콘텐츠 포맷

    Returns:
    --------
    dict : 계산 결과 및 세부 정보
    """

    # 글로벌 기준 먼저 계산
    global_cost = estimate_ad_cost_global(
        subscriber_count, avg_views, engagement_rate,
        avg_likes, avg_comments,
        recent_90day_avg_views, content_format
    )

    # STEP 10: 한국 시장 조정 계수
    korea_adjustment = 0.75
    if subscriber_count < 100000:
        korea_adjustment = 0.85

    # STEP 11: 한국 최종 비용
    final_cost = int(global_cost['final_cost'] * korea_adjustment)

    # STEP 12: 비용 범위 산정
    min_cost = int(final_cost * 0.85)
    max_cost = int(final_cost * 1.15)

    return {
        'base_cost_cpm': int(global_cost['base_cost_cpm'] * korea_adjustment),
        'recent_cpm_cost': int(global_cost['recent_cpm_cost'] * korea_adjustment),
        'tier_base': int(global_cost['tier_base'] * korea_adjustment),
        'base_cost': int(global_cost['base_cost'] * korea_adjustment),

        'engagement_rate': global_cost['engagement_rate'],
        'engagement_multiplier': global_cost['engagement_multiplier'],
        'engagement_level': global_cost['engagement_level'],

        'comment_like_ratio': global_cost['comment_like_ratio'],
        'quality_multiplier': global_cost['quality_multiplier'],
        'quality_level': global_cost['quality_level'],

        'final_engagement_multiplier': global_cost['final_engagement_multiplier'],
        'format_multiplier': global_cost['format_multiplier'],
        'content_format': global_cost['content_format'],

        'global_final_cost': global_cost['final_cost'],
        'korea_adjustment': korea_adjustment,
        'final_cost': final_cost,

        'min_cost': min_cost,
        'max_cost': max_cost,

        'cpm_used': int(global_cost['cpm_used'] * korea_adjustment)
    }
