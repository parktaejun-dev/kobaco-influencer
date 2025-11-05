"""
유튜브 인플루언서 광고 비용 산출 모듈 (v3.0)
2024-2025년 글로벌 벤치마크(PageOne Formula, Shopify, Descript 등) 기준 적용

- CPM 기준액 하향 조정 (97,500원 -> 39,000원)
- 티어별 최소 보장 금액 수정 (마이크로, 매크로, 메가 티어 상향)
- 참여율 보정 세분화 (10%+ 구간 추가)
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

def estimate_ad_cost_global(subscriber_count, avg_views, engagement_rate):
    """
    글로벌 표준 광고 비용 산출 로직 (CPM 기반) - v3.0 (2025 벤치마크 수정)
    
    [근거]
    - CPM: PageOne Formula ($10-30), Descript ($30-70)
    - Tiers: Shopify, ADOPTER Media
    """
    
    # 1. CPM 기반 기본 비용 계산
    # 2024-2025 벤치마크 평균 $30 (약 39,000원) 기준으로 하향 조정
    cpm_krw = 39000  # 1,000뷰당 비용 (기존 97,500원에서 대폭 하향)
    base_cost_cpm = (avg_views / 1000) * cpm_krw
    
    # 2. 구독자 규모별 최소 보장 금액 (티어별 기준가)
    # 2025 벤치마크(Shopify, Descript, ADOPTER) 기준으로 수정
    if subscriber_count < 10000:
        tier_base = 350000  # (나노) $20-200 범위 내, 기존 유지
    elif subscriber_count < 100000:
        tier_base = 2500000  # (마이크로) $200-2,500 -> 중간값 상향 (기존 150만)
    elif subscriber_count < 500000:
        tier_base = 5200000  # (미드티어) $1,000-10,000 -> 기존 유지 (적절)
    elif subscriber_count < 1000000:
        tier_base = 19500000 # (매크로) $10,000-20,000 -> 중간값 상향 (기존 975만)
    else:
        tier_base = 47500000 # (메가) $20,000-100,000+ -> 중간값 대폭 상향 (기존 1820만)
    
    # 3. CPM 기반 금액과 티어 기본 금액 중 높은 값 선택
    base_cost = max(base_cost_cpm, tier_base)
    
    # 4. 참여율 보정 (인플루언서의 실제 영향력 반영)
    # 10%+ 구간 추가하여 세분화
    if engagement_rate >= 10:
        engagement_multiplier = 1.5
        engagement_level = "최상 (10%+)"
    elif engagement_rate >= 7: # 7.0 - 9.99
        engagement_multiplier = 1.3
        engagement_level = "매우 높음 (7-10%)"
    elif engagement_rate >= 5: # 5.0 - 6.99
        engagement_multiplier = 1.2
        engagement_level = "높음 (5-7%)"
    elif engagement_rate >= 3: # 3.0 - 4.99
        engagement_multiplier = 1.1
        engagement_level = "양호 (3-5%)"
    elif engagement_rate >= 2: # 2.0 - 2.99
        engagement_multiplier = 1.0
        engagement_level = "보통 (2-3%)"
    elif engagement_rate >= 1: # 1.0 - 1.99
        engagement_multiplier = 0.9
        engagement_level = "낮음 (1-2%)"
    else: # < 1.0
        engagement_multiplier = 0.85
        engagement_level = "매우 낮음 (<1%)"
    
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
    - 글로벌 벤치마크(수정됨)를 기반으로 한국 시장 조정 계수(기존 유지) 적용
    """
    
    # 수정된 글로벌 기준 먼저 계산
    global_cost = estimate_ad_cost_global(subscriber_count, avg_views, engagement_rate)
    
    # 한국 시장 조정 계수 (0.75 = 글로벌의 75% 수준)
    # 검증 결과 "합리적임"으로 판단되어 기존 로직 유지
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
