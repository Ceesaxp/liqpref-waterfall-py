"""
Core liquidation preference waterfall calculation logic.

This module contains the main WaterfallCalculator class and supporting data structures
for modeling startup liquidation preferences, including stacked liquidation preferences,
participation rights, caps, and conversion scenarios.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class PreferenceType(Enum):
    """Types of liquidation preferences."""
    COMMON = "common"
    NON_PARTICIPATING = "non_participating"
    PARTICIPATING = "participating"


class AntiDilutionType(Enum):
    """Types of anti-dilution provisions."""
    NONE = "None"
    FULL_RATCHET = "FR"
    WEIGHTED_AVERAGE = "WA"


@dataclass
class ShareClass:
    """
    Represents a class of shares with liquidation preferences.
    
    Attributes:
        name: Name of the share class (e.g., "Series A", "Common")
        shares: Number of shares outstanding
        invested: Total amount invested in this share class
        preference_type: Type of liquidation preference
        preference_multiple: Liquidation preference multiple (e.g., 1.0 for 1x)
        participation_cap: Cap on participating preference (None = uncapped)
        priority: Priority level for liquidation (higher = paid first)
        stack_order: Original stack order from cap table
        convertible: Whether shares can convert to common
        anti_dilution_type: Type of anti-dilution protection
    """
    name: str
    shares: int
    invested: float
    preference_type: PreferenceType = PreferenceType.COMMON
    preference_multiple: float = 1.0
    participation_cap: Optional[float] = None  # None means uncapped, 0 means no cap
    priority: int = 0  # Higher number = higher priority
    stack_order: int = 0  # Stack order from CSV
    convertible: bool = True  # Whether the shares can convert to common
    anti_dilution_type: AntiDilutionType = AntiDilutionType.NONE


class WaterfallCalculator:
    """
    Calculates liquidation preference waterfalls for startup cap tables.
    
    This calculator models the distribution of proceeds from a company sale
    among different classes of shareholders based on their liquidation
    preferences, participation rights, and conversion options.
    
    The waterfall algorithm:
    1. Pay liquidation preferences in priority order
    2. Distribute remaining proceeds to participating preferred and common
    3. Apply participation caps iteratively
    4. Consider conversion to common for non-participating preferred
    
    Example:
        >>> calc = WaterfallCalculator()
        >>> common = ShareClass("Common", 1000000, 0, PreferenceType.COMMON)
        >>> preferred = ShareClass("Series A", 200000, 900000, PreferenceType.PARTICIPATING, 1.0, 2.0, 1)
        >>> calc.add_share_class(common)
        >>> calc.add_share_class(preferred)
        >>> distribution = calc.calculate_distribution(5000000)
    """
    
    def __init__(self):
        self.share_classes: List[ShareClass] = []

    def add_share_class(self, share_class: ShareClass):
        """Add a share class to the cap table."""
        self.share_classes.append(share_class)

    def calculate_distribution(self, exit_value: float) -> Dict[str, float]:
        """
        Calculate the distribution of exit proceeds among all share classes.
        
        Args:
            exit_value: Total proceeds from the company sale
            
        Returns:
            Dictionary mapping share class names to their payout amounts
        """
        if not self.share_classes:
            return {}

        # For non-participating preferred shares, we need to determine the optimal strategy:
        # take liquidation preference or convert to common
        # This requires calculating what they would get in each scenario
        
        # First, calculate the "all take liquidation preference" scenario
        distribution_with_lp = self._calculate_with_all_liquidation_preferences(exit_value)
        
        # Then check if any preferred shares would be better off converting
        total_shares = sum(sc.shares for sc in self.share_classes)
        distribution = {}
        
        # Check each share class to see if they should convert
        # We need to check what they would actually get if they converted
        converting_classes = []
        
        # Check each non-participating preferred share class to see if they should convert
        # Participating preferred typically don't convert as they already get both
        # liquidation preference AND participation
        for share_class in self.share_classes:
            if (share_class.preference_type == PreferenceType.NON_PARTICIPATING and 
                share_class.convertible):
                # What would they get with liquidation preference?
                lp_amount = distribution_with_lp.get(share_class.name, 0)
                
                # What would they get if they alone converted?
                # Calculate distribution with just this class converting
                test_distribution = self._calculate_with_conversions(exit_value, [share_class.name])
                convert_amount = test_distribution.get(share_class.name, 0)
                
                # Only convert if converting gives more
                if convert_amount > lp_amount:
                    converting_classes.append(share_class.name)
        
        # If anyone is converting, recalculate with those shares as common
        if converting_classes:
            distribution = self._calculate_with_conversions(exit_value, converting_classes)
        else:
            distribution = distribution_with_lp
            
        return distribution

    def _calculate_with_all_liquidation_preferences(self, exit_value: float) -> Dict[str, float]:
        """Calculate distribution assuming all preferred shares take liquidation preferences"""
        distribution = {}
        remaining_value = exit_value

        # Group preferred shares by priority/stack order
        preferred_classes = [sc for sc in self.share_classes
                           if sc.preference_type != PreferenceType.COMMON]
        
        # Group by priority
        priority_groups = {}
        for sc in preferred_classes:
            if sc.priority not in priority_groups:
                priority_groups[sc.priority] = []
            priority_groups[sc.priority].append(sc)
        
        # Process each priority level in order (highest first)
        for priority in sorted(priority_groups.keys(), reverse=True):
            group = priority_groups[priority]
            
            # Calculate total liquidation preference for this priority level
            total_lp_amount = sum(sc.invested * sc.preference_multiple for sc in group)
            
            if total_lp_amount <= remaining_value:
                # Enough money to pay all at this level
                for share_class in group:
                    liquidation_amount = share_class.invested * share_class.preference_multiple
                    distribution[share_class.name] = liquidation_amount
                    remaining_value -= liquidation_amount
            else:
                # Not enough money - pro-rate within this priority level
                for share_class in group:
                    liquidation_amount = share_class.invested * share_class.preference_multiple
                    pro_rata_share = liquidation_amount / total_lp_amount
                    payout = remaining_value * pro_rata_share
                    distribution[share_class.name] = payout
                
                remaining_value = 0
                break

        # For participating preferred, they also get pro-rata share of remaining
        if remaining_value > 0:
            participating_classes = [sc for sc in self.share_classes
                                   if sc.preference_type in [PreferenceType.COMMON, PreferenceType.PARTICIPATING]]
            
            if participating_classes:
                # Apply caps iteratively for participating preferred
                remaining_to_distribute = remaining_value
                uncapped_classes = participating_classes.copy()

                while uncapped_classes and remaining_to_distribute > 0:
                    total_uncapped_shares = sum(sc.shares for sc in uncapped_classes)
                    classes_to_remove = []
                    total_distributed_this_round = 0

                    for share_class in uncapped_classes:
                        ownership_percentage = share_class.shares / total_uncapped_shares
                        additional_payout = remaining_to_distribute * ownership_percentage

                        # Check if this would exceed the cap for participating preferred
                        if (share_class.preference_type == PreferenceType.PARTICIPATING and
                            share_class.participation_cap is not None and
                            share_class.participation_cap > 0):

                            max_total = share_class.invested * share_class.participation_cap
                            current_total = distribution.get(share_class.name, 0)

                            if current_total + additional_payout > max_total:
                                # Cap this class
                                capped_payout = max_total - current_total
                                distribution[share_class.name] = max_total
                                total_distributed_this_round += capped_payout
                                classes_to_remove.append(share_class)
                            else:
                                # No cap hit, add the payout
                                distribution[share_class.name] = current_total + additional_payout
                                total_distributed_this_round += additional_payout
                        else:
                            # Common shares or uncapped participating
                            if share_class.name in distribution:
                                distribution[share_class.name] += additional_payout
                            else:
                                distribution[share_class.name] = additional_payout
                            total_distributed_this_round += additional_payout

                    remaining_to_distribute -= total_distributed_this_round

                    # Remove capped classes and recalculate
                    for cls in classes_to_remove:
                        uncapped_classes.remove(cls)

                    if not classes_to_remove:
                        # No caps hit, we're done
                        break
        
        # Ensure all share classes have an entry (even if 0)
        for share_class in self.share_classes:
            if share_class.name not in distribution:
                distribution[share_class.name] = 0
                
        return distribution

    def _calculate_with_conversions(self, exit_value: float, converting_classes: List[str]) -> Dict[str, float]:
        """Calculate distribution with some preferred shares converting to common"""
        distribution = {}
        remaining_value = exit_value

        # First, pay liquidation preferences to non-converting preferred
        preferred_classes = [sc for sc in self.share_classes
                           if sc.preference_type != PreferenceType.COMMON 
                           and sc.name not in converting_classes]
        
        # Group by priority
        priority_groups = {}
        for sc in preferred_classes:
            if sc.priority not in priority_groups:
                priority_groups[sc.priority] = []
            priority_groups[sc.priority].append(sc)
        
        # Process each priority level
        for priority in sorted(priority_groups.keys(), reverse=True):
            group = priority_groups[priority]
            
            # Calculate total liquidation preference for non-converting shares at this level
            total_lp_amount = sum(sc.invested * sc.preference_multiple for sc in group)
            
            if total_lp_amount <= remaining_value:
                # Enough money to pay all at this level
                for share_class in group:
                    liquidation_amount = share_class.invested * share_class.preference_multiple
                    distribution[share_class.name] = liquidation_amount
                    remaining_value -= liquidation_amount
            else:
                # Not enough money - pro-rate within this priority level
                for share_class in group:
                    liquidation_amount = share_class.invested * share_class.preference_multiple
                    pro_rata_share = liquidation_amount / total_lp_amount
                    payout = remaining_value * pro_rata_share
                    distribution[share_class.name] = payout
                
                remaining_value = 0
                break

        # Then distribute remaining pro-rata among common + converting preferred + participating
        if remaining_value > 0:
            eligible_classes = [sc for sc in self.share_classes
                              if (sc.preference_type == PreferenceType.COMMON or 
                                  sc.name in converting_classes or
                                  (sc.preference_type == PreferenceType.PARTICIPATING and 
                                   sc.name not in converting_classes))]
            
            if eligible_classes:
                # Apply caps iteratively for participating preferred
                remaining_to_distribute = remaining_value
                uncapped_classes = eligible_classes.copy()
                
                while uncapped_classes and remaining_to_distribute > 0:
                    total_uncapped_shares = sum(sc.shares for sc in uncapped_classes)
                    classes_to_remove = []
                    total_distributed_this_round = 0
                    
                    for share_class in uncapped_classes:
                        ownership_percentage = share_class.shares / total_uncapped_shares
                        additional_payout = remaining_to_distribute * ownership_percentage
                        
                        # Check cap for participating preferred
                        if (share_class.preference_type == PreferenceType.PARTICIPATING and
                            share_class.participation_cap is not None and
                            share_class.participation_cap > 0 and
                            share_class.name not in converting_classes):
                            
                            max_total = share_class.invested * share_class.participation_cap
                            current_total = distribution.get(share_class.name, 0)
                            
                            if current_total + additional_payout > max_total:
                                # Cap this class
                                capped_payout = max_total - current_total
                                distribution[share_class.name] = max_total
                                total_distributed_this_round += capped_payout
                                classes_to_remove.append(share_class)
                            else:
                                # No cap hit
                                distribution[share_class.name] = current_total + additional_payout
                                total_distributed_this_round += additional_payout
                        else:
                            # Common, converting preferred, or uncapped
                            if share_class.name in distribution:
                                distribution[share_class.name] += additional_payout
                            else:
                                distribution[share_class.name] = additional_payout
                            total_distributed_this_round += additional_payout
                    
                    remaining_to_distribute -= total_distributed_this_round
                    
                    # Remove capped classes
                    for cls in classes_to_remove:
                        uncapped_classes.remove(cls)
                    
                    if not classes_to_remove:
                        break
        
        # Ensure all share classes have an entry
        for share_class in self.share_classes:
            if share_class.name not in distribution:
                distribution[share_class.name] = 0
                
        return distribution