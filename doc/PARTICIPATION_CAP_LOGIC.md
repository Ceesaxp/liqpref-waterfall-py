# Participation Cap Logic

## Overview

Participating preferred shares with caps present a unique challenge in liquidation waterfalls. They receive:

1. Their liquidation preference first (e.g., 1x invested amount)
2. Pro-rata participation in remaining proceeds
3. But total payout is capped at a multiple of investment (e.g., 2x cap)

## Example: Series E at $170M Exit

### Setup
- Series E: $13.5M invested, 1x participating with 2x cap
- Maximum payout: $13.5M × 2 = $27M
- Ownership: 31.8% (1.5M shares out of 4.724M total)

### What Happens

1. **Liquidation Preferences Paid**:
   - Series E gets $13.5M (their 1x preference)
   - Other non-participating shares take their preferences based on priority

2. **Pro-Rata Distribution**:
   - Remaining funds distributed among:
     - Common shares
     - Converting preferred shares  
     - Participating preferred shares (including Series E)
   - Series E would get 31.8% of this pool

3. **Cap Applied**:
   - Series E's total (preference + participation) hits $27M cap
   - Excess redistributed to other uncapped participants

## Key Implementation Details

### Participating Shares Don't Convert
```python
# Only non-participating shares can convert
if share_class.preference_type == PreferenceType.NON_PARTICIPATING:
    # Check conversion logic
```

### Cap Enforcement in All Scenarios
The cap must be enforced in both:
- `_calculate_with_all_liquidation_preferences()` 
- `_calculate_with_conversions()`

### Iterative Cap Application
```python
while uncapped_classes and remaining_to_distribute > 0:
    # Calculate pro-rata for uncapped classes
    # Apply caps
    # Remove capped classes
    # Redistribute excess
```

## Results at Different Exit Values

| Exit Value | Series E Payout | Explanation |
|------------|-----------------|-------------|
| $50M       | $13.5M          | Only gets liquidation preference |
| $100M      | $27.0M          | Hits 2x cap |
| $170M      | $27.0M          | Still capped at 2x |
| $250M      | $27.0M          | Still capped at 2x |

## Common Pitfalls

1. **Forgetting to enforce caps** when other shares convert
2. **Allowing participating shares to convert** (they shouldn't)
3. **Not redistributing excess** when a share hits its cap
4. **Misreporting conversions** for participating shares (they don't convert, they just hit caps)