# Liquidation Waterfall Logic Explanation

## The Key Insight

When determining whether a preferred shareholder should convert to common, they must consider not just their pro-rata share of the total exit value, but what they would **actually receive** after all other liquidation preferences are paid.

## Example: $50M Exit with captable-3.csv

### Cap Table Summary
- Series E: 31.8% ownership, $13.5M liquidation preference
- Series D: 18.4% ownership, $30.45M liquidation preference  
- Series C: 12.7% ownership, $18.6M liquidation preference
- Others: Various smaller preferred shares
- Common + ESOP: 24.4% combined

### Naive (Incorrect) Analysis
Series E might think: "I own 31.8%, so at $50M I'd get $15.88M if I convert. That's more than my $13.5M liquidation preference, so I should convert!"

### Correct Analysis

**Scenario 1: Series E takes liquidation preference**
1. Series E (priority 7): Takes $13.5M → Remaining: $36.5M
2. Series D (priority 6): Takes $30.45M → Remaining: $6.05M
3. Series C (priority 5): Takes $6.05M (less than their $18.6M preference) → Remaining: $0
4. Everyone else: $0

Result: Series E gets $13.5M

**Scenario 2: Series E converts to common**
1. Series D (priority 6): Takes $30.45M → Remaining: $19.55M
2. Series C (priority 5): Takes $18.6M → Remaining: $0.95M
3. Other preferred: Take what they can from $0.95M
4. Pro-rata distribution of remaining (<$1M) among Common + Series E
   - Series E's share: ~31.8% of <$1M = **much less than $13.5M**

Result: Series E gets much less by converting!

## The Algorithm

```python
def should_convert(share_class, exit_value):
    # Calculate what they get with liquidation preference
    lp_scenario = calculate_waterfall_with_all_lps(exit_value)
    lp_amount = lp_scenario[share_class]
    
    # Calculate what they get if they convert
    # This requires simulating the waterfall with them as common
    convert_scenario = calculate_waterfall_with_conversion(exit_value, [share_class])
    convert_amount = convert_scenario[share_class]
    
    return convert_amount > lp_amount
```

## Key Principles

1. **Liquidation preferences are paid in order of priority** (highest to lowest)
2. **Conversion decisions must consider the full waterfall**, not just pro-rata of exit value
3. **Higher priority preferred shares can "block" lower priority shares** from receiving their full preference
4. **Conversion is rarely optimal at lower exit values** due to preference stacking

## When Conversion Makes Sense

Conversion typically only makes sense when:
1. The exit value is high enough that all liquidation preferences can be paid
2. There's significant value remaining for pro-rata distribution
3. The converting shareholder's pro-rata ownership exceeds their preference/invested ratio

In the captable-3.csv example, Series E would need the exit value to be much higher (likely >$100M) before conversion becomes attractive.