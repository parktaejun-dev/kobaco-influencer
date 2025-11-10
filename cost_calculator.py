"""
유튜브 인플루언서 광고 비용 산출 모듈 (v4.3)
2024-2025년 글로벌 벤치마크(PageOne Formula, Shopify, Descript 등) 기준 적용

v4.3 개선사항 (2025-11):
- 스마트 티어 시스템 도입 (채널 건강도 평가)
  * 조회수/구독자 비율 기반 건강도 계산
  * 8단계 세분화된 건강도 기준
  * 건강도에 따른 티어 조정 계수 적용 (0.3x ~ 1.2x)
  * "구독자 뻥튀기" 문제 해결

v4.2 개선사항 (2025-11):
- 티어별 최소 보장 금액 합리화
  * Micro: 250만→200만 (-20%)
  * Mid-tier: 520만→400만 (-23%)
  * Macro: 1,950만→1,000만 (-49%)
  * Mega: 4,750만→1,500만 (-68%)
- CPM 우선 작동, 티어는 보조 역할로 조정

v4.1 개선사항:
- 콘텐츠 포맷 프리미엄 제거 (PPL 단일 기준)
- 최근 90일 CPM 계산 추가 (죽은 채널 방지)
- 참여 질 보정 추가 (댓글/좋아요 비율)
- CPM 기본값 30,000원으로 조정 (시장 반영)
"""

def calculate_channel_health(subscriber_count, avg_views):
    """
    채널 건강도 계산 (조회수/구독자 비율 기반)

    Parameters:
    -----------
    subscriber_count : int
        구독자 수
    avg_views : int
        평균 조회수

    Returns:
    --------
    dict : {
        'ratio': 조회수/구독자 비율 (%),
        'level': 건강도 등급,
        'emoji': 이모지,
        'multiplier': 티어 조정 계수,
        'description': 설명
    }
    """
    if subscriber_count == 0:
        ratio = 0
    else:
        ratio = (avg_views / subscriber_count) * 100

    # 8단계 세분화된 건강도 기준
    if ratio >= 30:
        return {
            'ratio': ratio,
            'level': '초건강',
            'emoji': '🔥',
            'multiplier': 1.2,
            'description': '매우 활발한 채널! 구독자 참여도가 탁월합니다.',
            'color': '#ff6b35'
        }
    elif ratio >= 20:
        return {
            'ratio': ratio,
            'level': '매우 건강',
            'emoji': '✅',
            'multiplier': 1.1,
            'description': '매우 건강한 채널입니다. 높은 구독자 참여도를 보입니다.',
            'color': '#4caf50'
        }
    elif ratio >= 15:
        return {
            'ratio': ratio,
            'level': '건강',
            'emoji': '✅',
            'multiplier': 1.0,
            'description': '건강한 채널입니다. 양호한 구독자 참여도를 보입니다.',
            'color': '#8bc34a'
        }
    elif ratio >= 10:
        return {
            'ratio': ratio,
            'level': '정상',
            'emoji': '⚖️',
            'multiplier': 1.0,
            'description': '정상 범위의 채널입니다. 평균적인 구독자 참여도입니다.',
            'color': '#9e9e9e'
        }
    elif ratio >= 7:
        return {
            'ratio': ratio,
            'level': '약간 약화',
            'emoji': '⚠️',
            'multiplier': 0.8,
            'description': '구독자 대비 조회수가 약간 낮습니다.',
            'color': '#ff9800'
        }
    elif ratio >= 5:
        return {
            'ratio': ratio,
            'level': '약화',
            'emoji': '⚠️',
            'multiplier': 0.7,
            'description': '구독자 대비 조회수가 낮습니다. 채널 활성화가 필요합니다.',
            'color': '#ff9800'
        }
    elif ratio >= 3:
        return {
            'ratio': ratio,
            'level': '죽어감',
            'emoji': '🟡',
            'multiplier': 0.5,
            'description': '채널 활동이 크게 저하되었습니다. 구독자 이탈이 심각합니다.',
            'color': '#f44336'
        }
    else:
        return {
            'ratio': ratio,
            'level': '죽음',
            'emoji': '🔴',
            'multiplier': 0.3,
            'description': '채널이 거의 활동하지 않습니다. 구독자 수만 남은 상태입니다.',
            'color': '#d32f2f'
        }


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
                            cpm_krw=30000):
    """
    글로벌 표준 광고 비용 산출 로직 (CPM 기반) - v4.2

    브랜디드 PPL 기준 (제품 1개당 30초~1분 내외 단순 노출)
    v4.2: 티어별 최소 보장 금액 합리화 (Mega 4,750만→1,500만)

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
    cpm_krw : int, optional
        1,000뷰당 비용 (기본값: 30,000원)

    Returns:
    --------
    dict : 계산 결과 및 세부 정보
    """

    # STEP 1: CPM 기반 기본 비용 계산
    base_cost_cpm = (avg_views / 1000) * cpm_krw

    # STEP 2: 최근 90일 CPM 계산 (선택적)
    recent_cpm_cost = 0
    if recent_90day_avg_views and recent_90day_avg_views > 0:
        recent_cpm_cost = (recent_90day_avg_views / 1000) * cpm_krw

    # STEP 3: 티어별 최소 보장 금액 (v4.2 - 합리화)
    if subscriber_count < 10000:
        tier_base = 350000      # Nano: 1K-10K (유지)
    elif subscriber_count < 100000:
        tier_base = 2000000     # Micro: 10K-100K (250만→200만)
    elif subscriber_count < 500000:
        tier_base = 4000000     # Mid-tier: 100K-500K (520만→400만)
    elif subscriber_count < 1000000:
        tier_base = 10000000    # Macro: 500K-1M (1,950만→1,000만)
    else:
        tier_base = 15000000    # Mega: 1M+ (4,750만→1,500만)

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

    # STEP 8: 글로벌 최종 비용 (PPL 기준)
    final_cost = int(base_cost * final_engagement_multiplier)

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

        'final_cost': final_cost,
        'cpm_used': cpm_krw
    }

def estimate_ad_cost_korea(subscriber_count, avg_views, engagement_rate,
                          avg_likes, avg_comments,
                          recent_90day_avg_views=None,
                          cpm_krw=30000):
    """
    한국 시장 기준 광고 비용 산출 로직 - v4.3

    브랜디드 PPL 기준 (제품 1개당 30초~1분 내외 단순 노출)
    v4.3: 스마트 티어 시스템 (채널 건강도 반영)
    v4.2: 티어별 최소 보장 금액 합리화

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
    cpm_krw : int, optional
        1,000뷰당 비용 (기본값: 30,000원)

    Returns:
    --------
    dict : 계산 결과 및 세부 정보
    """

    # 글로벌 기준 먼저 계산
    global_cost = estimate_ad_cost_global(
        subscriber_count, avg_views, engagement_rate,
        avg_likes, avg_comments,
        recent_90day_avg_views, cpm_krw
    )

    # STEP 10: 채널 건강도 계산 (v4.3 신규)
    channel_health = calculate_channel_health(subscriber_count, avg_views)

    # STEP 11: 한국 시장 조정 계수
    korea_adjustment = 0.75
    if subscriber_count < 100000:
        korea_adjustment = 0.85

    # STEP 12: 한국 최종 비용 (채널 건강도 조정 반영)
    # 건강도 조정: 티어 최소 보장 금액에만 적용 (CPM은 실제 조회수 반영이므로 제외)
    adjusted_tier_base = int(global_cost['tier_base'] * korea_adjustment * channel_health['multiplier'])
    adjusted_base_cost = int(global_cost['base_cost'] * korea_adjustment)

    # 최종 비용: 조정된 기본 비용 사용
    if global_cost['base_cost'] == global_cost['tier_base']:
        # 티어 최소값이 적용된 경우: 건강도 조정 반영
        final_cost = int(global_cost['final_cost'] * korea_adjustment * channel_health['multiplier'])
    else:
        # CPM이 적용된 경우: 건강도 조정 미반영 (실제 조회수 이미 반영됨)
        final_cost = int(global_cost['final_cost'] * korea_adjustment)

    # STEP 13: 비용 범위 산정
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

        # 채널 건강도 정보 (v4.3 신규)
        'channel_health': channel_health,
        'health_adjusted_tier_base': adjusted_tier_base,

        'global_final_cost': global_cost['final_cost'],
        'korea_adjustment': korea_adjustment,
        'final_cost': final_cost,

        'min_cost': min_cost,
        'max_cost': max_cost,

        'cpm_used': int(global_cost['cpm_used'] * korea_adjustment)
    }
