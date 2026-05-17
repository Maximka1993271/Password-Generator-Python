"""
Password generator and strength calculator
"""
import secrets
import math
import string
from typing import List, Optional


class PasswordGenerator:
    """Cryptographically secure password generator"""
    
    DEFAULT_SPECIAL = "!@#$%^&*()_+-=[]{}|;:,.<>?/~"
    AMBIGUOUS_CHARS = "il1Lo0O"
    UNAMBIGUOUS_CHARS = "{}[]()/\\'\"`~,;:.<>"
    
    def __init__(self):
        self.use_upper = True
        self.use_lower = True
        self.use_digits = True
        self.use_special = False
        self.exclude_ambiguous = False
        self.exclude_unambiguous = False
        self.min_each = False
        self.no_repeat = False
        self.length = 20
    
    def _get_pool(self) -> str:
        """Get character pool based on current settings"""
        pool = ""
        if self.use_lower:
            pool += string.ascii_lowercase
        if self.use_upper:
            pool += string.ascii_uppercase
        if self.use_digits:
            pool += string.digits
        if self.use_special:
            pool += self.DEFAULT_SPECIAL
        
        if self.exclude_ambiguous:
            for ch in self.AMBIGUOUS_CHARS:
                pool = pool.replace(ch, '')
        
        if self.exclude_unambiguous:
            for ch in self.UNAMBIGUOUS_CHARS:
                pool = pool.replace(ch, '')
        
        return pool
    
    def _get_categories(self) -> List[str]:
        """Get list of character categories for 'min each' mode"""
        categories = []
        if self.use_lower:
            categories.append(string.ascii_lowercase)
        if self.use_upper:
            categories.append(string.ascii_uppercase)
        if self.use_digits:
            categories.append(string.digits)
        if self.use_special:
            categories.append(self.DEFAULT_SPECIAL)
        
        # Apply exclusions to each category
        if self.exclude_ambiguous:
            categories = [''.join(c for c in cat if c not in self.AMBIGUOUS_CHARS) for cat in categories]
        if self.exclude_unambiguous:
            categories = [''.join(c for c in cat if c not in self.UNAMBIGUOUS_CHARS) for cat in categories]
        
        return [cat for cat in categories if cat]
    
    def _fix_no_repeats(self, chars: List[str], pool: str) -> Optional[str]:
        """Ensure no consecutive repeated characters"""
        result = list(chars)
        unique_pool = list(set(pool))
        max_attempts = 500
        
        def _secure_shuffle(lst: list) -> None:
            for i in range(len(lst) - 1, 0, -1):
                j = secrets.randbelow(i + 1)
                lst[i], lst[j] = lst[j], lst[i]
        
        for _ in range(max_attempts):
            _secure_shuffle(result)
            has_repeat = any(result[i] == result[i + 1] for i in range(len(result) - 1))
            if not has_repeat:
                return "".join(result)
        
        # Fallback: try to fix repeats
        result = list(chars)
        _secure_shuffle(result)
        for attempt in range(max_attempts):
            fixed = False
            for i in range(len(result) - 1):
                if result[i] == result[i + 1]:
                    candidates = [c for c in unique_pool if c != result[i] and (i == 0 or c != result[i - 1])]
                    if candidates:
                        result[i + 1] = secrets.choice(candidates)
                        fixed = True
            if not fixed:
                break
            if not any(result[i] == result[i + 1] for i in range(len(result) - 1)):
                return "".join(result)
        return None
    
    def generate(self) -> Optional[str]:
        """Generate a password based on current settings"""
        try:
            length = int(self.length)
        except (TypeError, ValueError):
            return None
        if length <= 0:
            return None

        pool = self._get_pool()
        
        if not pool:
            return None
        
        if self.min_each:
            categories = self._get_categories()
            if not categories or len(categories) < 1:
                categories = [pool]
            if length < len(categories):
                return None

            password_chars = []
            
            # Take one from each category
            for cat in categories:
                if cat:
                    password_chars.append(secrets.choice(cat))
            
            # Fill the rest from the full pool
            remaining = length - len(password_chars)
            for _ in range(remaining):
                password_chars.append(secrets.choice(pool))
            
            # Shuffle
            for i in range(len(password_chars) - 1, 0, -1):
                j = secrets.randbelow(i + 1)
                password_chars[i], password_chars[j] = password_chars[j], password_chars[i]
            
            result = "".join(password_chars)
        else:
            # Simple generation
            result = ''.join(secrets.choice(pool) for _ in range(length))
        
        # Apply no-repeat constraint if needed
        if self.no_repeat:
            fixed = self._fix_no_repeats(list(result), pool)
            if not fixed:
                return None
            result = fixed
        
        return result


class StrengthCalculator:
    """Calculate password strength metrics"""
    
    @staticmethod
    def calculate(password: str) -> dict:
        """
        Calculate password strength
        Returns dict with: pool_size, combinations, entropy_bits, strength_level, crack_time_label
        """
        if not password:
            return {
                'pool_size': 0,
                'combinations': 0,
                'entropy_bits': 0,
                'strength_level': 'empty',
                'crack_time_label': ''
            }
        
        pool_size = 0
        if any(c.islower() for c in password):
            pool_size += 26
        if any(c.isupper() for c in password):
            pool_size += 26
        if any(c.isdigit() for c in password):
            pool_size += 10
        if any(c in string.punctuation for c in password):
            pool_size += 32
        
        combinations = pool_size ** len(password) if pool_size > 0 else 0
        entropy_bits = len(password) * math.log2(pool_size) if pool_size > 0 else 0
        
        if entropy_bits < 40:
            strength_level = 'weak'
            crack_time_label = 'time_sec'
        elif entropy_bits < 60:
            strength_level = 'medium'
            crack_time_label = 'time_day'
        elif entropy_bits < 80:
            strength_level = 'medium'
            crack_time_label = 'time_year'
        else:
            strength_level = 'strong'
            crack_time_label = 'time_cent'
        
        return {
            'pool_size': pool_size,
            'combinations': f"{combinations:.1e}" if combinations > 0 else "0",
            'entropy_bits': entropy_bits,
            'strength_level': strength_level,
            'crack_time_label': crack_time_label
        }
