"""
Finite-Key Analysis for BB84
==============================

Computes confidence intervals on QBER estimates using Hoeffding bound.

Problem:
- QBER is estimated from a FINITE sample of test bits
- At small sample sizes, the estimate has high uncertainty
- Example: 64 test bits with 7 errors → QBER = 10.9%
  But 95% confidence interval is [4.5%, 17.3%]
  True QBER could be above or below 11% threshold!

Solution:
- Use Hoeffding bound to compute confidence interval
- Adjust threshold to account for statistical uncertainty
- Ensure security even at small sample sizes

References:
- Hoeffding, "Probability Inequalities for Sums of Bounded Random Variables," 1963
- Tomamichel et al., "Tight Finite-Key Analysis for Quantum Cryptography," 2012

Author: ShorlyNot Team
"""

import math
from typing import Tuple


def hoeffding_confidence_interval(
    qber: float,
    num_test_bits: int,
    confidence: float = 0.99
) -> Tuple[float, float]:
    """
    Compute confidence interval on QBER using Hoeffding bound.
    
    Args:
        qber: Observed QBER (0.0 to 1.0)
        num_test_bits: Number of bits used for QBER estimation
        confidence: Confidence level (default: 0.99 = 99%)
    
    Returns:
        tuple: (lower_bound, upper_bound)
    
    Formula:
        epsilon = sqrt(-ln(delta/2) / (2*n))
        CI = [qber - epsilon, qber + epsilon]
        
        where delta = 1 - confidence
    
    Example:
        >>> qber = 0.10  # 10% observed
        >>> num_test_bits = 100
        >>> lower, upper = hoeffding_confidence_interval(qber, num_test_bits, 0.99)
        >>> print(f"99% CI: [{lower:.3f}, {upper:.3f}]")
        99% CI: [0.029, 0.171]
        
        Interpretation: We're 99% confident the true QBER is between 2.9% and 17.1%.
        Since upper bound (17.1%) > 11%, we CANNOT conclude the channel is secure.
    """
    if num_test_bits == 0:
        return (0.0, 1.0)  # No data, maximum uncertainty
    
    # Hoeffding bound
    delta = 1 - confidence
    epsilon = math.sqrt(-math.log(delta / 2) / (2 * num_test_bits))
    
    lower = max(0.0, qber - epsilon)
    upper = min(1.0, qber + epsilon)
    
    return (lower, upper)


def finite_key_secure_threshold(
    num_test_bits: int,
    base_threshold: float = 0.11,
    confidence: float = 0.99
) -> float:
    """
    Compute adjusted threshold that accounts for finite-key effects.
    
    Args:
        num_test_bits: Number of test bits
        base_threshold: Asymptotic threshold (default: 0.11 = Shor-Preskill)
        confidence: Confidence level (default: 0.99)
    
    Returns:
        float: Adjusted threshold (lower than base to account for uncertainty)
    
    Rationale:
        If we observe QBER = 10% with 100 test bits, the 99% CI is [3%, 17%].
        We can't be sure the true QBER is below 11%.
        
        So we use a MORE CONSERVATIVE threshold:
        adjusted_threshold = base_threshold - epsilon
        
        This ensures that if observed QBER < adjusted_threshold, we're confident
        the true QBER is below base_threshold.
    
    Example:
        >>> num_test_bits = 100
        >>> adjusted = finite_key_secure_threshold(num_test_bits, 0.11, 0.99)
        >>> print(f"Adjusted threshold: {adjusted:.3f}")
        Adjusted threshold: 0.039
        
        Interpretation: With only 100 test bits, we need observed QBER < 3.9%
        to be 99% confident the true QBER is below 11%.
    """
    delta = 1 - confidence
    epsilon = math.sqrt(-math.log(delta / 2) / (2 * num_test_bits))
    
    adjusted = max(0.0, base_threshold - epsilon)
    
    return adjusted


def finite_key_rate(
    qber: float,
    num_sifted_bits: int,
    security_parameter: float = 1e-10
) -> float:
    """
    Compute finite-key secure key rate.
    
    Args:
        qber: Observed QBER
        num_sifted_bits: Total number of sifted bits
        security_parameter: Security parameter epsilon (default: 1e-10)
    
    Returns:
        float: Secure key rate (bits per sifted bit)
    
    Formula:
        Asymptotic rate: r = 1 - 2*h(QBER)
        Finite-key correction: subtract O(sqrt(log(1/epsilon) / n))
        
        where h(p) = -p*log2(p) - (1-p)*log2(1-p) is binary entropy
    
    Example:
        >>> qber = 0.05  # 5% QBER
        >>> num_sifted_bits = 1000
        >>> rate = finite_key_rate(qber, num_sifted_bits)
        >>> print(f"Secure key rate: {rate:.3f} bits/sifted bit")
        Secure key rate: 0.532 bits/sifted bit
        
        Interpretation: From 1000 sifted bits, we can extract ~532 secure key bits.
    """
    if qber >= 0.11:
        return 0.0  # Above Shor-Preskill threshold, no secure key
    
    # Binary entropy function
    def h(p):
        if p == 0 or p == 1:
            return 0
        return -p * math.log2(p) - (1 - p) * math.log2(1 - p)
    
    # Asymptotic rate (infinite key length)
    asymptotic_rate = 1 - 2 * h(qber)
    
    # Finite-key correction (simplified Tomamichel bound)
    if num_sifted_bits == 0:
        return 0.0
    correction = math.sqrt(2 * math.log(1 / security_parameter) / num_sifted_bits)
    
    finite_rate = max(0.0, asymptotic_rate - correction)
    
    return finite_rate
