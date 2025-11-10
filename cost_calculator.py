"""
유튜브 인플루언서 광고 비용 산출 모듈 (v4.4)
2024-2025년 글로벌 벤치마크(PageOne Formula, Shopify, Descript 등) 기준 적용

v4.4 개선사항 (2025-11):
- 채널 프리미엄 할증 시스템 추가
  * 성장세 프리미엄 (최근 90일 vs 전체)
  * 업로드 일관성 프리미엄
  * 팬덤 충성도 프리미엄
  * 모든 프리미엄 계수 통합 적용

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


# ============================================
# 채널 프리미엄 할증 시스템 (v4.4)
# ============================================

def calculate_growth_multiplier(avg_views, recent_90day_avg_views):
    """
    채널 성장세 프리미엄/할인 계수 계산

    최근 90일 평균 조회수와 전체 평균 비교
    - 증가 추세 = 프리미엄 (떠오르는 채널)
    - 감소 추세 = 할인 (하락하는 채널)

    Parameters:
    -----------
    avg_views : int
        전체 평균 조회수
    recent_90day_avg_views : int
        최근 90일 평균 조회수

    Returns:
    --------
    dict : {
        'multiplier': 성장세 계수,
        'growth_rate': 성장률 (%),
        'status': 성장 상태,
        'description': 설명
    }
    """

    # 최근 데이터가 없으면 중립
    if not recent_90day_avg_views or avg_views == 0:
        return {
            'multiplier': 1.0,
            'growth_rate': 0,
            'status': '데이터 부족',
            'description': '최근 90일 데이터 없음'
        }

    # 성장률 계산 (%)
    growth_rate = ((recent_90day_avg_views - avg_views) / avg_views) * 100

    # 성장률에 따른 평가 및 계수 결정
    if growth_rate >= 50:
        # 급성장
        multiplier = 1.15
        status = "🚀 급성장"
        description = f"최근 3개월 조회수가 {growth_rate:+.1f}% 증가한 떠오르는 채널입니다."

    elif growth_rate >= 20:
        # 고성장
        multiplier = 1.10
        status = "📈 고성장"
        description = f"최근 3개월 조회수가 {growth_rate:+.1f}% 증가한 성장 채널입니다."

    elif growth_rate >= 10:
        # 성장
        multiplier = 1.05
        status = "📊 성장"
        description = f"최근 3개월 조회수가 {growth_rate:+.1f}% 완만하게 증가하고 있습니다."

    elif growth_rate >= -10:
        # 안정 (기준점)
        multiplier = 1.0
        status = "➡️ 안정"
        description = f"최근 3개월 조회수가 안정적입니다 ({growth_rate:+.1f}%)."

    elif growth_rate >= -20:
        # 감소
        multiplier = 0.95
        status = "📉 감소"
        description = f"최근 3개월 조회수가 {growth_rate:.1f}% 감소하고 있습니다."

    else:
        # 급감
        multiplier = 0.90
        status = "⬇️ 급감"
        description = f"최근 3개월 조회수가 {growth_rate:.1f}% 급감하고 있습니다. 주의가 필요합니다."

    return {
        'multiplier': multiplier,
        'growth_rate': round(growth_rate, 1),
        'status': status,
        'description': description
    }


def calculate_consistency_multiplier(video_count, channel_age_days=None):
    """
    업로드 일관성 프리미엄/할인 계수 계산

    규칙적인 업로드 = 신뢰도 높음 = 프리미엄
    불규칙한 업로드 = 예측 어려움 = 할인

    Parameters:
    -----------
    video_count : int
        총 영상 개수
    channel_age_days : int, optional
        채널 개설 일수

    Returns:
    --------
    dict : {
        'multiplier': 일관성 계수,
        'upload_frequency': 업로드 빈도,
        'status': 일관성 상태,
        'description': 설명
    }
    """

    # 채널 나이 정보가 있으면 더 정확한 계산 가능
    if channel_age_days and channel_age_days > 0:
        # 주당 업로드 횟수 계산
        weeks = channel_age_days / 7
        uploads_per_week = video_count / weeks if weeks > 0 else 0

        if uploads_per_week >= 2:
            # 매우 규칙적 (주 2회 이상)
            multiplier = 1.05
            status = "🎯 매우 규칙적"
            upload_frequency = f"주 {uploads_per_week:.1f}회"
            description = "업로드가 매우 규칙적입니다. 광고 영상도 안정적으로 노출될 것으로 예상됩니다."

        elif uploads_per_week >= 1:
            # 규칙적 (주 1회) - 기준점
            multiplier = 1.0
            status = "✅ 규칙적"
            upload_frequency = f"주 {uploads_per_week:.1f}회"
            description = "업로드가 규칙적입니다. 광고 효과가 안정적으로 예상됩니다."

        elif uploads_per_week >= 0.5:
            # 불규칙 (월 2-3회)
            multiplier = 0.95
            status = "⚠️ 불규칙"
            upload_frequency = f"월 {uploads_per_week * 4:.1f}회"
            description = "업로드가 다소 불규칙합니다. 광고 타이밍 조율이 필요할 수 있습니다."

        else:
            # 비활성 (월 1회 미만)
            multiplier = 0.90
            status = "🔴 비활성"
            upload_frequency = f"월 {uploads_per_week * 4:.1f}회"
            description = "업로드 빈도가 낮습니다. 광고 효과가 제한적일 수 있습니다."

    else:
        # 채널 나이 정보 없으면 영상 개수만으로 단순 평가
        if video_count >= 200:
            multiplier = 1.05
            status = "🎯 활발"
            upload_frequency = f"총 {video_count}개"
            description = "영상이 풍부한 활발한 채널입니다."
        elif video_count >= 50:
            multiplier = 1.0
            status = "✅ 정상"
            upload_frequency = f"총 {video_count}개"
            description = "적절한 콘텐츠 양을 보유한 채널입니다."
        else:
            multiplier = 0.95
            status = "⚠️ 제한적"
            upload_frequency = f"총 {video_count}개"
            description = "영상 개수가 다소 적은 채널입니다."

    return {
        'multiplier': multiplier,
        'upload_frequency': upload_frequency,
        'status': status,
        'description': description
    }


def calculate_loyalty_multiplier(avg_views, avg_comments, subscriber_count):
    """
    팬덤 충성도 프리미엄 계수 계산

    활발한 댓글 = 충성도 높은 팬덤 = 프리미엄

    Parameters:
    -----------
    avg_views : int
        평균 조회수
    avg_comments : int
        평균 댓글 수
    subscriber_count : int
        구독자 수

    Returns:
    --------
    dict : {
        'multiplier': 팬덤 계수,
        'comment_view_ratio': 댓글/조회수 비율 (%),
        'status': 팬덤 상태,
        'description': 설명
    }
    """

    # 조회수가 0이면 계산 불가
    if avg_views == 0:
        return {
            'multiplier': 1.0,
            'comment_view_ratio': 0,
            'status': '데이터 부족',
            'description': '조회수 데이터 없음'
        }

    # 댓글/조회수 비율 계산 (%)
    comment_view_ratio = (avg_comments / avg_views) * 100

    # 비율에 따른 팬덤 충성도 평가
    if comment_view_ratio >= 0.5:
        # 매우 활발한 팬덤
        multiplier = 1.10
        status = "💬 매우 활발"
        description = "댓글이 매우 활발한 채널입니다. 충성도 높은 팬덤을 보유하고 있습니다."

    elif comment_view_ratio >= 0.3:
        # 활발한 팬덤
        multiplier = 1.05
        status = "💬 활발"
        description = "댓글이 활발한 채널입니다. 팬덤의 반응이 좋습니다."

    elif comment_view_ratio >= 0.1:
        # 정상 팬덤 (기준점)
        multiplier = 1.0
        status = "✅ 정상"
        description = "정상적인 수준의 댓글 활동이 있습니다."

    else:
        # 저조한 팬덤
        multiplier = 0.97
        status = "📉 저조"
        description = "댓글 활동이 다소 적습니다. 팬덤 참여도가 낮은 편입니다."

    return {
        'multiplier': multiplier,
        'comment_view_ratio': round(comment_view_ratio, 3),
        'status': status,
        'description': description
    }


def calculate_total_premium(subscriber_count, avg_views,
                           recent_90day_avg_views, video_count,
                           avg_comments, channel_age_days=None):
    """
    모든 프리미엄 요소를 종합하여 최종 프리미엄 계수 계산

    Parameters:
    -----------
    subscriber_count : int
        구독자 수
    avg_views : int
        평균 조회수
    recent_90day_avg_views : int
        최근 90일 평균 조회수
    video_count : int
        총 영상 개수
    avg_comments : int
        평균 댓글 수
    channel_age_days : int, optional
        채널 개설 일수

    Returns:
    --------
    dict : {
        'total_multiplier': 총 프리미엄 계수,
        'health': 건강도 상세,
        'growth': 성장세 상세,
        'consistency': 일관성 상세,
        'loyalty': 팬덤 상세,
        'summary': 종합 요약
    }
    """

    # 각 요소별 계수 계산
    health = calculate_channel_health(subscriber_count, avg_views)
    growth = calculate_growth_multiplier(avg_views, recent_90day_avg_views)
    consistency = calculate_consistency_multiplier(video_count, channel_age_days)
    loyalty = calculate_loyalty_multiplier(avg_views, avg_comments, subscriber_count)

    # 총 프리미엄 계수 계산 (곱셈)
    total_multiplier = (
        health['multiplier'] *
        growth['multiplier'] *
        consistency['multiplier'] *
        loyalty['multiplier']
    )

    # 종합 요약 생성
    premium_pct = (total_multiplier - 1.0) * 100

    if premium_pct > 10:
        summary = f"🔥 우수 채널 (프리미엄 +{premium_pct:.1f}%)"
    elif premium_pct > 0:
        summary = f"✅ 양호 채널 (프리미엄 +{premium_pct:.1f}%)"
    elif premium_pct > -10:
        summary = f"➡️ 보통 채널 (조정 {premium_pct:+.1f}%)"
    else:
        summary = f"⚠️ 주의 채널 (할인 {premium_pct:.1f}%)"

    return {
        'total_multiplier': round(total_multiplier, 3),
        'health': health,
        'growth': growth,
        'consistency': consistency,
        'loyalty': loyalty,
        'summary': summary
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
                          video_count=10,
                          channel_age_days=None,
                          cpm_krw=30000):
    """
    한국 시장 기준 광고 비용 산출 로직 - v4.4

    브랜디드 PPL 기준 (제품 1개당 30초~1분 내외 단순 노출)
    v4.4: 채널 프리미엄 할증 시스템 통합
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
    video_count : int, optional
        총 영상 개수
    channel_age_days : int, optional
        채널 개설 일수
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

    # STEP 10: 채널 프리미엄 계수 (v4.4 신규)
    premium_data = calculate_total_premium(
        subscriber_count=subscriber_count,
        avg_views=avg_views,
        recent_90day_avg_views=recent_90day_avg_views,
        video_count=video_count,
        avg_comments=avg_comments,
        channel_age_days=channel_age_days
    )

    channel_premium_multiplier = premium_data['total_multiplier']

    # STEP 11: 한국 시장 조정 계수
    korea_adjustment = 0.75
    if subscriber_count < 100000:
        korea_adjustment = 0.85

    # STEP 12: 한국 최종 비용 (채널 프리미엄 반영)
    global_final_cost = int(
        global_cost['final_cost'] *
        channel_premium_multiplier
    )

    final_cost = int(global_final_cost * korea_adjustment)

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

        # 채널 프리미엄 정보 (v4.4 신규)
        'channel_premium_multiplier': channel_premium_multiplier,
        'premium_details': premium_data,

        'global_final_cost': global_final_cost,
        'korea_adjustment': korea_adjustment,
        'final_cost': final_cost,

        'min_cost': min_cost,
        'max_cost': max_cost,

        'cpm_used': int(global_cost['cpm_used'] * korea_adjustment)
    }
