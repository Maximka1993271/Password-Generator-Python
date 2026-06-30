"""
Passphrase generator using EFF Diceware word list
Генератор парольных фраз с использованием словаря Diceware
Генератор парольних фраз з використанням словника Diceware

FIXED: Uses the full EFF Diceware word list from resources/diceware_words.json
"""
from __future__ import annotations

import os
import json
import secrets
import re
from typing import List, Optional, Tuple
from utils.logger import get_logger

logger = get_logger("passphrase_generator")

# Default settings / Настройки по умолчанию / Налаштування за замовчуванням
DEFAULT_WORD_COUNT = 6
DEFAULT_SEPARATOR = " "
DEFAULT_CAPITALIZE = False
DEFAULT_ADD_NUMBER = False
DEFAULT_NUMBER_POSITION = "end"  # "start", "end", "random"

# Minimum and maximum word count limits
MIN_WORD_COUNT = 3
MAX_WORD_COUNT = 12


class PassphraseGenerator:
    """
    Cryptographically secure passphrase generator using Diceware word list.
    
    Криптографически безопасный генератор парольных фраз.
    Криптографічно безпечний генератор парольних фраз.
    """
    
    _wordlist: Optional[List[str]] = None
    _wordlist_paths: List[str] = []
    
    @classmethod
    def _get_wordlist_paths(cls) -> List[str]:
        """Get possible paths for diceware wordlist file."""
        if cls._wordlist_paths:
            return cls._wordlist_paths
        
        # Get base directory
        if hasattr(os, 'getcwd'):
            base_dir = os.getcwd()
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Try to get base dir from various sources
        try:
            from utils.paths import get_base_dir
            base_dir = get_base_dir()
        except ImportError:
            pass
        
        paths = [
            os.path.join(base_dir, "resources", "diceware_words.json"),
            os.path.join(base_dir, "diceware_words.json"),
            os.path.join(os.path.dirname(base_dir), "resources", "diceware_words.json"),
            os.path.join(os.path.dirname(__file__), "..", "resources", "diceware_words.json"),
            os.path.join(os.path.dirname(__file__), "..", "diceware_words.json"),
        ]
        
        # For frozen applications (PyInstaller)
        if hasattr(os, 'sys') and hasattr(os.sys, '_MEIPASS'):
            meipass = os.sys._MEIPASS
            paths.extend([
                os.path.join(meipass, "resources", "diceware_words.json"),
                os.path.join(meipass, "diceware_words.json"),
            ])
        
        cls._wordlist_paths = paths
        return paths
    
    @classmethod
    def _load_wordlist(cls) -> List[str]:
        """Load Diceware wordlist from JSON file."""
        if cls._wordlist is not None:
            return cls._wordlist
        
        for path in cls._get_wordlist_paths():
            try:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        wordlist = data
                    elif isinstance(data, dict) and 'words' in data:
                        wordlist = data['words']
                    elif isinstance(data, dict) and 'diceware' in data:
                        wordlist = data['diceware']
                    else:
                        continue
                    
                    if len(wordlist) >= 7776:
                        logger.info(f"Loaded {len(wordlist)} Diceware words from {path}")
                        cls._wordlist = wordlist
                        return wordlist
                    elif len(wordlist) >= 1000:
                        logger.info(f"Using partial wordlist from {path} ({len(wordlist)} words)")
                        cls._wordlist = wordlist
                        return wordlist
            except (OSError, IOError, json.JSONDecodeError) as e:
                logger.debug(f"Failed to load diceware words from {path}: {e}")
                continue
        
        # Fallback to built-in mini wordlist
        logger.warning("Full Diceware wordlist not found! Using fallback mini wordlist.")
        cls._wordlist = cls._create_fallback_wordlist()
        return cls._wordlist
    
    @classmethod
    def _create_fallback_wordlist(cls) -> List[str]:
        """Create a basic fallback wordlist when no file is found."""
        return [
            "abacus", "abdicate", "abduct", "abhor", "abide", "abject", "abjure", "ablate", "ablaze",
            "abnegate", "abode", "abort", "abound", "abrade", "abridge", "abrupt", "absent", "absorb",
            "absurd", "abut", "abysmal", "accent", "accept", "access", "accord", "accost", "accrete",
            "accrue", "accuse", "acerbic", "acetate", "achieve", "acidic", "acme", "acorn", "acquire",
            "acrid", "acumen", "acute", "adage", "adapt", "addict", "addle", "address", "adhere",
            "adieu", "adjacent", "adjure", "adjust", "adman", "admire", "admit", "adobe", "adopt",
            "adore", "adorn", "adrift", "adroit", "adult", "advent", "adverb", "adverse", "advise",
            "advocate", "aegis", "aerate", "aerial", "aerobic", "affable", "affect", "affine", "affirm",
            "affix", "afflict", "affluent", "afford", "affront", "afield", "afire", "afloat", "afoot",
            "afraid", "afresh", "after", "agape", "agate", "agave", "agency", "agenda", "agent",
        ]
    
    @classmethod
    def get_word_count(cls) -> int:
        """Get the size of the loaded wordlist."""
        return len(cls._load_wordlist())
    
    @classmethod
    def generate(cls, word_count: int = DEFAULT_WORD_COUNT,
                 separator: str = DEFAULT_SEPARATOR,
                 capitalize: bool = DEFAULT_CAPITALIZE,
                 add_number: bool = DEFAULT_ADD_NUMBER,
                 number_position: str = DEFAULT_NUMBER_POSITION) -> str:
        """
        Generate a cryptographically secure passphrase.
        
        Args:
            word_count: Number of words to use (3-12)
            separator: Character to separate words
            capitalize: Whether to capitalize each word
            add_number: Whether to add a number
            number_position: Where to add the number ('start', 'end', 'random')
        
        Returns:
            Generated passphrase
        """
        wordlist = cls._load_wordlist()
        
        # Validate word_count
        if word_count < MIN_WORD_COUNT:
            word_count = MIN_WORD_COUNT
        if word_count > MAX_WORD_COUNT:
            word_count = MAX_WORD_COUNT
        
        # Select random words using secrets (cryptographically secure)
        words = []
        for _ in range(word_count):
            word = secrets.choice(wordlist)
            if capitalize:
                word = word.capitalize()
            words.append(word)
        
        # Join with separator
        passphrase = separator.join(words)
        
        # Add number if requested
        if add_number:
            number = str(secrets.randbelow(1000)).zfill(3)
            
            if number_position == "start":
                passphrase = number + separator + passphrase
            elif number_position == "end":
                passphrase = passphrase + separator + number
            else:  # random
                if secrets.randbelow(2) == 0:
                    passphrase = number + separator + passphrase
                else:
                    passphrase = passphrase + separator + number
        
        logger.debug(f"Generated passphrase with {word_count} words")
        return passphrase
    
    @classmethod
    def generate_multiple(cls, count: int = 5, **kwargs) -> List[str]:
        """
        Generate multiple passphrases.
        
        Args:
            count: Number of passphrases to generate
            **kwargs: Same arguments as generate()
        
        Returns:
            List of generated passphrases
        """
        results = []
        for _ in range(count):
            results.append(cls.generate(**kwargs))
        return results
    
    @classmethod
    def get_entropy_bits(cls, word_count: int, wordlist_size: int = None) -> float:
        """
        Calculate entropy bits of a passphrase.
        
        Args:
            word_count: Number of words in the passphrase
            wordlist_size: Size of the wordlist (auto-detected if None)
        
        Returns:
            Entropy in bits
        """
        import math
        
        if wordlist_size is None:
            wordlist_size = cls.get_word_count()
        
        if wordlist_size <= 0:
            return 0.0
        
        # Entropy = log2(wordlist_size ^ word_count)
        entropy = word_count * math.log2(wordlist_size)
        return entropy
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if the wordlist is available."""
        try:
            cls._load_wordlist()
            return True
        except (OSError, IOError, ValueError, KeyError, TypeError):
            return False


# ==================== CONVENIENCE FUNCTIONS ====================

def generate_passphrase(word_count: int = DEFAULT_WORD_COUNT,
                        separator: str = DEFAULT_SEPARATOR,
                        capitalize: bool = DEFAULT_CAPITALIZE,
                        add_number: bool = DEFAULT_ADD_NUMBER) -> str:
    """Generate a single passphrase (convenience function)."""
    return PassphraseGenerator.generate(word_count, separator, capitalize, add_number)


def generate_passphrases(count: int = 5, **kwargs) -> List[str]:
    """Generate multiple passphrases (convenience function)."""
    return PassphraseGenerator.generate_multiple(count, **kwargs)


def get_passphrase_entropy(word_count: int) -> float:
    """Get entropy bits for a passphrase with given word count."""
    return PassphraseGenerator.get_entropy_bits(word_count)


__all__ = [
    'PassphraseGenerator',
    'generate_passphrase',
    'generate_passphrases',
    'get_passphrase_entropy',
    'DEFAULT_WORD_COUNT',
    'DEFAULT_SEPARATOR',
    'DEFAULT_CAPITALIZE',
    'DEFAULT_ADD_NUMBER',
    'MIN_WORD_COUNT',
    'MAX_WORD_COUNT',
]