# Priority Groups and Pro-Rata Within Stack Order

## Overview

Sometimes within the same financing round or stack order, different investors may have different liquidation preference multiples. This creates a situation where multiple shareholders at the same priority level have different claims, requiring pro-rata distribution when funds are insufficient.

## Example Scenario

**Series B Round (Stack Order 2)**:
- Shareholder 1: 1M shares, $10M invested, 2.0x multiple → $20M liquidation preference
- Shareholder 2: 500K shares, $5M invested, 1.5x multiple → $7.5M liquidation preference  
- Shareholder 3: 500K shares, $5M invested, 1.25x multiple → $6.25M liquidation preference

**Total Series B liquidation preferences**: $33.75M

## Algorithm

### Step 1: Group by Priority Level
```python
priority_groups = {}
for share_class in preferred_classes:
    if share_class.priority not in priority_groups:
        priority_groups[share_class.priority] = []
    priority_groups[share_class.priority].append(share_class)
```

### Step 2: Process Each Priority Level
For each priority level (highest first):

1. **Calculate total liquidation preferences** for that level
2. **Check if sufficient funds** exist
3. **Distribute accordingly**:
   - If sufficient: Pay all liquidation preferences in full
   - If insufficient: Pro-rate based on liquidation preference amounts

### Step 3: Pro-Rata Calculation (When Insufficient)
```python
for share_class in group:
    liquidation_amount = share_class.invested * share_class.preference_multiple
    pro_rata_share = liquidation_amount / total_lp_amount
    payout = remaining_value * pro_rata_share
```

## Example Calculation: $20M Exit

**Series B Total LPs**: $33.75M
**Available**: $20M (insufficient)

**Pro-rata distribution**:
- Shareholder 1: $20M × ($20M / $33.75M) = $11.85M
- Shareholder 2: $20M × ($7.5M / $33.75M) = $4.44M  
- Shareholder 3: $20M × ($6.25M / $33.75M) = $3.70M

**Total**: $20M ✓

## Real-World Example: sbda.csv

The sbda.csv file demonstrates this scenario with Series B having different multiples:

```csv
B: Aksenov,2,2737508,137,1.25,TRUE,FALSE,0
B: FS - Old,2,610311,137,1.25,TRUE,FALSE,0  
B: FS - New,2,41210069,164,1.5,TRUE,FALSE,0
B: DSV - New,2,11774306,164,1.5,TRUE,FALSE,0
```

At a $20M exit:
- All Series B shareholders get pro-rated amounts based on their liquidation preferences
- Series A and Common get $0 (insufficient funds)

## Key Implementation Points

1. **Grouping**: Shareholders are grouped by `priority` (stack order)
2. **Sequential Processing**: Higher priority groups are processed first
3. **Pro-rata Within Group**: When insufficient funds, distribution is proportional to liquidation preference amounts
4. **No Remainder**: If a priority level consumes all remaining funds, lower priorities get $0

## Benefits

- **Handles complex cap tables** with varying terms within same round
- **Maintains fairness** through proportional distribution
- **Preserves priority ordering** between different rounds
- **Accurate modeling** of real-world liquidation scenarios