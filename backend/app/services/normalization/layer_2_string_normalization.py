"""
Layer 2: String Normalization

Cleans and normalizes string fields:
- Trim whitespace
- Remove control characters
- Normalize line endings
- Handle encoding issues
"""

from typing import Any
import re
from loguru import logger


class StringNormalizationLayer:
    """
    Layer 2: String Normalization
    Cleans and normalizes string values
    """

    # Control characters pattern (except tab, newline, carriage return)
    CONTROL_CHARS_PATTERN = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')

    # Multiple whitespace pattern
    MULTIPLE_WHITESPACE_PATTERN = re.compile(r'\s+')

    @staticmethod
    def normalize_string(value: str | None) -> str | None:
        """
        Normalize a string value

        Args:
            value: String to normalize

        Returns:
            Normalized string or None
        """
        if value is None:
            return None

        if not isinstance(value, str):
            value = str(value)

        try:
            # 1. Strip leading/trailing whitespace
            value = value.strip()

            # 2. Empty string → None
            if not value:
                return None

            # 3. Remove control characters (keep tab/newline)
            value = StringNormalizationLayer.CONTROL_CHARS_PATTERN.sub('', value)

            # 4. Normalize line endings (CRLF → LF, CR → LF)
            value = value.replace('\r\n', '\n').replace('\r', '\n')

            # 5. Replace multiple whitespace with single space (except in multiline)
            # Only collapse spaces within a line, not across lines
            lines = value.split('\n')
            normalized_lines = []
            for line in lines:
                # Collapse multiple spaces/tabs within line
                normalized_line = StringNormalizationLayer.MULTIPLE_WHITESPACE_PATTERN.sub(' ', line).strip()
                if normalized_line:  # Skip empty lines
                    normalized_lines.append(normalized_line)

            value = '\n'.join(normalized_lines) if normalized_lines else None

            # 6. Final check: empty after normalization?
            if value and not value.strip():
                return None

            return value

        except Exception as e:
            logger.error(f"String normalization failed for value: {e}")
            # Return trimmed original as fallback
            return value.strip() if value else None

    def normalize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize all string fields in a row

        Args:
            row: Row with mixed types

        Returns:
            Row with normalized strings
        """
        normalized = {}

        for field_name, field_value in row.items():
            if isinstance(field_value, str):
                normalized[field_name] = self.normalize_string(field_value)
            else:
                normalized[field_name] = field_value

        return normalized

    def normalize_batch(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Normalize a batch of rows

        Args:
            rows: List of rows

        Returns:
            List of normalized rows
        """
        return [self.normalize_row(row) for row in rows]
