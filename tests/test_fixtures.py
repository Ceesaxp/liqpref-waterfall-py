"""
Test fixtures and utilities for liquidation waterfall tests.

Provides reusable cap table configurations and custom assertions
following TDD and Tidy First principles.
"""

from liquidation_waterfall import WaterfallCalculator, ShareClass, PreferenceType, AntiDilutionType


def create_simple_cap_table():
    """
    Standard test cap table for basic scenarios.
    
    Returns:
        WaterfallCalculator with:
        - Series A: 100K shares, $1M invested, 1x non-participating
        - Common: 900K shares, no investment
    """
    calc = WaterfallCalculator()
    
    series_a = ShareClass(
        name="Series A",
        shares=100000,
        invested=1000000,
        preference_type=PreferenceType.NON_PARTICIPATING,
        preference_multiple=1.0,
        priority=1
    )
    
    common = ShareClass(
        name="Common",
        shares=900000,
        invested=0,
        preference_type=PreferenceType.COMMON,
        priority=0
    )
    
    calc.add_share_class(series_a)
    calc.add_share_class(common)
    
    return calc


def create_priority_groups_cap_table():
    """
    Cap table with multiple shareholders at same priority level.
    
    Returns:
        WaterfallCalculator with different multiples within Series B:
        - B1: 1M shares, $10M invested, 2.0x multiple
        - B2: 500K shares, $5M invested, 1.5x multiple  
        - B3: 500K shares, $5M invested, 1.25x multiple
        - Common: 1M shares, no investment
    """
    calc = WaterfallCalculator()
    
    b1 = ShareClass(
        name="B: Shareholder 1",
        shares=1000000,
        invested=10000000,
        preference_type=PreferenceType.NON_PARTICIPATING,
        preference_multiple=2.0,
        priority=2
    )
    
    b2 = ShareClass(
        name="B: Shareholder 2", 
        shares=500000,
        invested=5000000,
        preference_type=PreferenceType.NON_PARTICIPATING,
        preference_multiple=1.5,
        priority=2
    )
    
    b3 = ShareClass(
        name="B: Shareholder 3",
        shares=500000,
        invested=5000000,
        preference_type=PreferenceType.NON_PARTICIPATING,
        preference_multiple=1.25,
        priority=2
    )
    
    common = ShareClass(
        name="Common",
        shares=1000000,
        invested=0,
        preference_type=PreferenceType.COMMON,
        priority=0
    )
    
    calc.add_share_class(b1)
    calc.add_share_class(b2)
    calc.add_share_class(b3)
    calc.add_share_class(common)
    
    return calc


def create_participation_cap_table():
    """
    Cap table with participating preferences and caps.
    
    Returns:
        WaterfallCalculator with:
        - Series A: 200K shares, $2M invested, 1x participating with 2x cap
        - Series B: 100K shares, $1M invested, 1x participating uncapped
        - Common: 700K shares, no investment
    """
    calc = WaterfallCalculator()
    
    series_a = ShareClass(
        name="Series A",
        shares=200000,
        invested=2000000,
        preference_type=PreferenceType.PARTICIPATING,
        preference_multiple=1.0,
        participation_cap=2.0,  # 2x cap
        priority=2
    )
    
    series_b = ShareClass(
        name="Series B",
        shares=100000,
        invested=1000000,
        preference_type=PreferenceType.PARTICIPATING,
        preference_multiple=1.0,
        participation_cap=None,  # Uncapped
        priority=1
    )
    
    common = ShareClass(
        name="Common",
        shares=700000,
        invested=0,
        preference_type=PreferenceType.COMMON,
        priority=0
    )
    
    calc.add_share_class(series_a)
    calc.add_share_class(series_b)
    calc.add_share_class(common)
    
    return calc


def create_mixed_preferences_cap_table():
    """
    Cap table with mix of all preference types.
    
    Returns:
        WaterfallCalculator with all preference types for comprehensive testing.
    """
    calc = WaterfallCalculator()
    
    # Non-participating preferred
    series_c = ShareClass(
        name="Series C",
        shares=100000,
        invested=3000000,
        preference_type=PreferenceType.NON_PARTICIPATING,
        preference_multiple=1.5,
        priority=3
    )
    
    # Participating with cap
    series_b = ShareClass(
        name="Series B", 
        shares=150000,
        invested=2000000,
        preference_type=PreferenceType.PARTICIPATING,
        preference_multiple=1.0,
        participation_cap=3.0,
        priority=2
    )
    
    # Participating uncapped
    series_a = ShareClass(
        name="Series A",
        shares=200000,
        invested=1000000,
        preference_type=PreferenceType.PARTICIPATING,
        preference_multiple=1.0,
        participation_cap=None,
        priority=1
    )
    
    # Common shares
    common = ShareClass(
        name="Common",
        shares=550000,
        invested=0,
        preference_type=PreferenceType.COMMON,
        priority=0
    )
    
    calc.add_share_class(series_c)
    calc.add_share_class(series_b)
    calc.add_share_class(series_a)
    calc.add_share_class(common)
    
    return calc


# Custom Assertions

def assert_distribution_totals_exit_value(distribution, exit_value, delta=1000):
    """
    Assert that total distribution equals exit value within tolerance.
    
    Args:
        distribution: Dict mapping share class names to amounts
        exit_value: Expected total exit value
        delta: Tolerance for floating point comparison
        
    Raises:
        AssertionError: If totals don't match within delta
    """
    total_distributed = sum(distribution.values())
    if abs(total_distributed - exit_value) > delta:
        raise AssertionError(
            f"Distribution total ${total_distributed:,.2f} does not equal "
            f"exit value ${exit_value:,.2f} (delta: ${abs(total_distributed - exit_value):,.2f})"
        )


def assert_no_negative_distributions(distribution):
    """
    Assert that no share class receives negative distribution.
    
    Args:
        distribution: Dict mapping share class names to amounts
        
    Raises:
        AssertionError: If any distribution is negative
    """
    for name, amount in distribution.items():
        if amount < 0:
            raise AssertionError(f"Share class '{name}' has negative distribution: ${amount:,.2f}")


def assert_liquidation_preference_not_exceeded(calculator, distribution, share_class_name):
    """
    Assert that non-participating preferred doesn't exceed liquidation preference unless converting.
    
    Args:
        calculator: WaterfallCalculator instance
        distribution: Distribution result
        share_class_name: Name of share class to check
        
    Raises:
        AssertionError: If liquidation preference exceeded inappropriately
    """
    share_class = next(sc for sc in calculator.share_classes if sc.name == share_class_name)
    
    if share_class.preference_type == PreferenceType.NON_PARTICIPATING:
        amount_received = distribution.get(share_class_name, 0)
        liquidation_preference = share_class.invested * share_class.preference_multiple
        
        # If they got more than LP, they must have converted (which means pro-rata was better)
        if amount_received > liquidation_preference * 1.01:  # Small tolerance
            total_shares = sum(sc.shares for sc in calculator.share_classes)
            expected_pro_rata = sum(distribution.values()) * (share_class.shares / total_shares)
            
            if abs(amount_received - expected_pro_rata) > 1000:  # $1K tolerance
                raise AssertionError(
                    f"{share_class_name} got ${amount_received:,.2f} which exceeds LP "
                    f"${liquidation_preference:,.2f} but doesn't match pro-rata ${expected_pro_rata:,.2f}"
                )


def assert_participation_cap_respected(calculator, distribution, share_class_name):
    """
    Assert that participating preferred respects participation cap.
    
    Args:
        calculator: WaterfallCalculator instance
        distribution: Distribution result
        share_class_name: Name of share class to check
        
    Raises:
        AssertionError: If participation cap exceeded
    """
    share_class = next(sc for sc in calculator.share_classes if sc.name == share_class_name)
    
    if (share_class.preference_type == PreferenceType.PARTICIPATING and 
        share_class.participation_cap is not None and 
        share_class.participation_cap > 0):
        
        amount_received = distribution.get(share_class_name, 0)
        max_allowed = share_class.invested * share_class.participation_cap
        
        if amount_received > max_allowed * 1.01:  # Small tolerance
            raise AssertionError(
                f"{share_class_name} got ${amount_received:,.2f} which exceeds "
                f"participation cap ${max_allowed:,.2f}"
            )