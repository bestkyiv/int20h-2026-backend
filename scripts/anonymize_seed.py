#!/usr/bin/env python3
"""
Anonymize PII data in seed.sql file for int20h2026-backend project.

This script replaces personally identifiable information (PII) in participant records
while preserving database constraints, foreign keys, and non-PII data.

Anonymized fields:
- full_name: Ukrainian/Cyrillic names using Faker uk_UA locale
- email: Unique generated emails
- telegram: Unique generated handles with @ prefix
- phone: Ukrainian format (+380XXXXXXXXX)
- job_description, comment: Fake Ukrainian text
- cv_url, linkedin: Empty strings
- telegram_chat_id: Would be NULL (not in current seed data)

Preserved fields:
- All IDs, foreign keys (university_id, category_id, team_id)
- Boolean flags, enums, skills_text, timestamps
- Categories, universities, teams tables (no PII)
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple

from faker import Faker

# Initialize Faker with Ukrainian locale
fake = Faker("uk_UA")
Faker.seed(42)  # For reproducibility


class ParticipantAnonymizer:
    """Handles anonymization of participant PII data."""

    def __init__(self):
        self.used_emails: Set[str] = set()
        self.used_telegram: Set[str] = set()
        self.used_phones: Set[str] = set()
        self.used_team_names: Set[str] = set()

    def anonymize_full_name(self) -> str:
        """Generate Ukrainian full name."""
        return fake.name()

    def anonymize_email(self) -> str:
        """Generate unique email address."""
        attempts = 0
        while attempts < 1000:
            # Generate email in format: firstname.lastname{num}@example.com
            first = fake.first_name_nonbinary().lower()
            last = fake.last_name().lower()

            # Transliterate Cyrillic to Latin
            first = self._transliterate(first)
            last = self._transliterate(last)

            num = fake.random_int(min=1, max=999)
            email = f"{first}.{last}{num}@example.com"

            if email not in self.used_emails:
                self.used_emails.add(email)
                return email
            attempts += 1

        # Fallback with timestamp
        email = f"user{len(self.used_emails)}_{fake.random_int(min=1000, max=9999)}@example.com"
        self.used_emails.add(email)
        return email

    def anonymize_telegram(self) -> str:
        """Generate unique Telegram handle with @ prefix."""
        attempts = 0
        while attempts < 1000:
            # Generate handle like: @user_word123
            word = fake.word().lower()
            word = self._transliterate(word)
            num = fake.random_int(min=1, max=999)
            handle = f"@{word}{num}"

            if handle not in self.used_telegram:
                self.used_telegram.add(handle)
                return handle
            attempts += 1

        # Fallback
        handle = f"@user{len(self.used_telegram)}_{fake.random_int(min=1000, max=9999)}"
        self.used_telegram.add(handle)
        return handle

    def anonymize_phone(self) -> str:
        """Generate Ukrainian phone number (+380XXXXXXXXX)."""
        attempts = 0
        while attempts < 1000:
            # Ukrainian format: +380 + 9 digits
            digits = fake.numerify("#########")
            phone = f"+380{digits}"

            if phone not in self.used_phones:
                self.used_phones.add(phone)
                return phone
            attempts += 1

        # Fallback
        phone = f"+380{len(self.used_phones):09d}"
        self.used_phones.add(phone)
        return phone

    def anonymize_text(self, field_type: str = "comment") -> str:
        """Generate fake Ukrainian text for bio, comment, job_description."""
        if field_type == "comment":
            # Short comment
            return fake.sentence(nb_words=5)
        elif field_type == "job_description":
            # Medium text
            return fake.text(max_nb_chars=200)
        else:
            # Bio or other
            return fake.text(max_nb_chars=150)

    def anonymize_team_name(self) -> str:
        """Generate unique team name."""
        attempts = 0
        while attempts < 1000:
            # Generate team name from word combinations
            prefix_options = ["Team", "Squad", "Crew", "Group", "Alliance", "United"]
            suffix_options = fake.words(nb=2)

            prefix = fake.random_element(prefix_options)
            suffix = "".join(
                [self._transliterate(w).capitalize() for w in suffix_options]
            )

            team_name = f"{prefix}{suffix}"

            if team_name not in self.used_team_names:
                self.used_team_names.add(team_name)
                return team_name
            attempts += 1

        # Fallback
        team_name = (
            f"Team{len(self.used_team_names)}_{fake.random_int(min=100, max=999)}"
        )
        self.used_team_names.add(team_name)
        return team_name

    @staticmethod
    def _transliterate(text: str) -> str:
        """Simple Cyrillic to Latin transliteration."""
        # Ukrainian to Latin mapping
        trans_map = {
            "а": "a",
            "б": "b",
            "в": "v",
            "г": "h",
            "ґ": "g",
            "д": "d",
            "е": "e",
            "є": "ie",
            "ж": "zh",
            "з": "z",
            "и": "y",
            "і": "i",
            "ї": "i",
            "й": "i",
            "к": "k",
            "л": "l",
            "м": "m",
            "н": "n",
            "о": "o",
            "п": "p",
            "р": "r",
            "с": "s",
            "т": "t",
            "у": "u",
            "ф": "f",
            "х": "kh",
            "ц": "ts",
            "ч": "ch",
            "ш": "sh",
            "щ": "shch",
            "ь": "",
            "ю": "iu",
            "я": "ia",
            "А": "A",
            "Б": "B",
            "В": "V",
            "Г": "H",
            "Ґ": "G",
            "Д": "D",
            "Е": "E",
            "Є": "Ie",
            "Ж": "Zh",
            "З": "Z",
            "И": "Y",
            "І": "I",
            "Ї": "I",
            "Й": "I",
            "К": "K",
            "Л": "L",
            "М": "M",
            "Н": "N",
            "О": "O",
            "П": "P",
            "Р": "R",
            "С": "S",
            "Т": "T",
            "У": "U",
            "Ф": "F",
            "Х": "Kh",
            "Ц": "Ts",
            "Ч": "Ch",
            "Ш": "Sh",
            "Щ": "Shch",
            "Ь": "",
            "Ю": "Iu",
            "Я": "Ia",
        }

        result = []
        for char in text:
            if char in trans_map:
                result.append(trans_map[char])
            else:
                result.append(char)

        # Join and remove non-word characters
        result_str = "".join(result)
        result_str = re.sub(r"[^\w]", "", result_str)
        return result_str


class SQLAnonymizer:
    """Main class for anonymizing seed.sql file."""

    def __init__(self, input_file: Path, output_file: Path):
        self.input_file = input_file
        self.output_file = output_file
        self.anonymizer = ParticipantAnonymizer()
        self.participants_start_line = None
        self.participants_end_line = None
        self.teams_start_line = None
        self.teams_end_line = None

    def run(self) -> None:
        """Main execution method."""
        print(f"Reading SQL file: {self.input_file}")

        with open(self.input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        print(f"Total lines: {len(lines)}")

        # Find participants and teams INSERT blocks
        self._find_participants_block(lines)
        self._find_teams_block(lines)

        if self.participants_start_line is None:
            print("ERROR: Could not find participants INSERT block")
            sys.exit(1)

        if self.teams_start_line is None:
            print("ERROR: Could not find teams INSERT block")
            sys.exit(1)

        print(
            f"Found participants block: lines {self.participants_start_line}-{self.participants_end_line}"
        )
        print(f"Found teams block: lines {self.teams_start_line}-{self.teams_end_line}")

        # Extract and parse teams records
        teams_block = "".join(lines[self.teams_start_line : self.teams_end_line + 1])
        teams = self._parse_teams(teams_block)

        print(f"Parsed {len(teams)} team records")

        # Extract and parse participant records
        participants_block = "".join(
            lines[self.participants_start_line : self.participants_end_line + 1]
        )
        participants = self._parse_participants(participants_block)

        print(f"Parsed {len(participants)} participant records")

        # Anonymize teams
        anonymized_teams_block = self._anonymize_teams(teams)

        # Anonymize participants
        anonymized_participants_block = self._anonymize_participants(participants)

        # Reconstruct SQL file
        output_lines = (
            lines[: self.teams_start_line]
            + [anonymized_teams_block]
            + lines[self.teams_end_line + 1 : self.participants_start_line]
            + [anonymized_participants_block]
            + lines[self.participants_end_line + 1 :]
        )

        # Write output
        print(f"Writing anonymized SQL to: {self.output_file}")
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.writelines(output_lines)

        # Print summary
        print("\n=== Anonymization Summary ===")
        print(f"Anonymized {len(teams)} teams")
        print(f"  - {len(self.anonymizer.used_team_names)} unique team names")
        print(f"Anonymized {len(participants)} participants")
        print(f"  - {len(self.anonymizer.used_emails)} unique emails")
        print(f"  - {len(self.anonymizer.used_telegram)} unique telegram handles")
        print(f"  - {len(self.anonymizer.used_phones)} unique phone numbers")
        print(f"\nOutput written to: {self.output_file}")

    def _find_teams_block(self, lines: List[str]) -> None:
        """Find start and end lines of teams INSERT block."""
        for i, line in enumerate(lines):
            if self.teams_start_line is None:
                if "INSERT INTO" in line:
                    for j in range(i, min(i + 5, len(lines))):
                        if '"public"."teams"' in lines[j]:
                            self.teams_start_line = i
                            break
            elif (
                self.teams_start_line is not None
                and "ON CONFLICT (id) DO NOTHING;" in line
            ):
                self.teams_end_line = i
                break

    def _find_participants_block(self, lines: List[str]) -> None:
        """Find start and end lines of participants INSERT block."""
        for i, line in enumerate(lines):
            # Check for INSERT INTO participants (may span multiple lines)
            if self.participants_start_line is None:
                if "INSERT INTO" in line:
                    # Check next few lines for participants table
                    for j in range(i, min(i + 5, len(lines))):
                        if '"public"."participants"' in lines[j]:
                            self.participants_start_line = i
                            break
            elif "ON CONFLICT (id) DO NOTHING;" in line:
                self.participants_end_line = i
                break

    def _parse_participants(self, block: str) -> List[dict]:
        """Parse SQL INSERT block into list of participant dictionaries."""
        # Extract column names
        columns_match = re.search(
            r'INSERT INTO\s+"public"\."participants"\s*\((.*?)\)\s*VALUES',
            block,
            re.DOTALL,
        )

        if not columns_match:
            print("ERROR: Could not parse column names")
            sys.exit(1)

        columns_text = columns_match.group(1)
        columns = [col.strip().strip('"') for col in columns_text.split(",")]

        print(f"Columns: {columns}")

        # Extract VALUES section
        values_match = re.search(r"VALUES\s*(.*?)\s*ON CONFLICT", block, re.DOTALL)
        if not values_match:
            print("ERROR: Could not parse VALUES section")
            sys.exit(1)

        values_text = values_match.group(1).strip()

        # Parse individual records - handle multi-line VALUES
        participants = []
        current_record = []
        paren_depth = 0
        in_string = False
        escape_next = False
        current_token = []

        for char in values_text:
            if escape_next:
                current_token.append(char)
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                current_token.append(char)
                continue

            if char == "'" and not in_string:
                in_string = True
                current_token.append(char)
            elif char == "'" and in_string:
                in_string = False
                current_token.append(char)
            elif char == "(" and not in_string:
                paren_depth += 1
                if paren_depth == 1:
                    current_record = []
                    current_token = []
                else:
                    current_token.append(char)
            elif char == ")" and not in_string:
                paren_depth -= 1
                if paren_depth == 0:
                    # End of record
                    if current_token:
                        token_str = "".join(current_token).strip()
                        if token_str and token_str != ",":
                            current_record.append(token_str)

                    if current_record and len(current_record) == len(columns):
                        participant = dict(zip(columns, current_record))
                        participants.append(participant)
                    current_token = []
                else:
                    current_token.append(char)
            elif char == "," and not in_string:
                if paren_depth == 1:
                    # Field separator
                    token_str = "".join(current_token).strip()
                    current_record.append(token_str)
                    current_token = []
                else:
                    current_token.append(char)
            else:
                if paren_depth > 0:
                    current_token.append(char)

        return participants

    def _parse_teams(self, block: str) -> List[dict]:
        """Parse SQL INSERT block into list of team dictionaries."""
        # Extract column names
        columns_match = re.search(
            r'INSERT INTO\s+"public"\."teams"\s*\((.*?)\)\s*VALUES', block, re.DOTALL
        )

        if not columns_match:
            print("ERROR: Could not parse team column names")
            sys.exit(1)

        columns_text = columns_match.group(1)
        columns = [col.strip().strip('"') for col in columns_text.split(",")]

        # Extract VALUES section
        values_match = re.search(r"VALUES\s*(.*?)\s*ON CONFLICT", block, re.DOTALL)
        if not values_match:
            print("ERROR: Could not parse team VALUES section")
            sys.exit(1)

        values_text = values_match.group(1).strip()

        # Parse individual team records
        teams = []
        current_record = []
        paren_depth = 0
        in_string = False
        escape_next = False
        current_token = []

        for char in values_text:
            if escape_next:
                current_token.append(char)
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                current_token.append(char)
                continue

            if char == "'" and not in_string:
                in_string = True
                current_token.append(char)
            elif char == "'" and in_string:
                in_string = False
                current_token.append(char)
            elif char == "(" and not in_string:
                paren_depth += 1
                if paren_depth == 1:
                    current_record = []
                    current_token = []
                else:
                    current_token.append(char)
            elif char == ")" and not in_string:
                paren_depth -= 1
                if paren_depth == 0:
                    if current_token:
                        token_str = "".join(current_token).strip()
                        if token_str and token_str != ",":
                            current_record.append(token_str)

                    if current_record and len(current_record) == len(columns):
                        team = dict(zip(columns, current_record))
                        teams.append(team)
                    current_token = []
                else:
                    current_token.append(char)
            elif char == "," and not in_string:
                if paren_depth == 1:
                    token_str = "".join(current_token).strip()
                    current_record.append(token_str)
                    current_token = []
                else:
                    current_token.append(char)
            else:
                if paren_depth > 0:
                    current_token.append(char)

        return teams

    def _anonymize_teams(self, teams: List[dict]) -> str:
        """Anonymize team records and rebuild SQL INSERT block."""
        if not teams:
            return ""

        columns = list(teams[0].keys())
        columns_sql = ", ".join(f'"{col}"' for col in columns)

        # Build VALUES
        values_parts = []

        for team in teams:
            anonymized = self._anonymize_team_record(team)
            values = [anonymized[col] for col in columns]
            values_str = ", ".join(values)
            values_parts.append(f"\t({values_str})")

        values_sql = ",\n".join(values_parts)

        # Build complete INSERT statement
        sql = f"""INSERT INTO
\t"public"."teams" ({columns_sql})
VALUES
{values_sql} ON CONFLICT (id) DO NOTHING;
"""

        return sql

    def _anonymize_team_record(self, record: dict) -> dict:
        """Anonymize a single team record."""
        anonymized = record.copy()

        # Anonymize team_name field
        if "team_name" in anonymized:
            team_name = self.anonymizer.anonymize_team_name()
            anonymized["team_name"] = f"'{team_name}'"

        return anonymized

    def _anonymize_participants(self, participants: List[dict]) -> str:
        """Anonymize participant records and rebuild SQL INSERT block."""
        # Build column list
        if not participants:
            return ""

        columns = list(participants[0].keys())
        columns_sql = ",\n\t\t".join(f'"{col}"' for col in columns)

        # Build VALUES
        values_parts = []

        for participant in participants:
            anonymized = self._anonymize_record(participant)

            # Build values tuple
            values = []
            for col in columns:
                val = anonymized[col]
                values.append(val)

            values_str = ",\n\t\t".join(values)
            values_parts.append(f"\t(\n\t\t{values_str}\n\t)")

        values_sql = ",\n".join(values_parts)

        # Build complete INSERT statement
        sql = f"""INSERT INTO
\t"public"."participants" (
\t\t{columns_sql}
\t)
VALUES
{values_sql} ON CONFLICT (id) DO NOTHING;
"""

        return sql

    def _anonymize_record(self, record: dict) -> dict:
        """Anonymize a single participant record."""
        anonymized = record.copy()

        # Anonymize PII fields
        if "full_name" in anonymized:
            name = self.anonymizer.anonymize_full_name()
            anonymized["full_name"] = f"'{name}'"

        if "email" in anonymized:
            email = self.anonymizer.anonymize_email()
            anonymized["email"] = f"'{email}'"

        if "telegram" in anonymized:
            telegram = self.anonymizer.anonymize_telegram()
            anonymized["telegram"] = f"'{telegram}'"

        if "phone" in anonymized:
            phone = self.anonymizer.anonymize_phone()
            anonymized["phone"] = f"'{phone}'"

        # Clear URLs
        if "cv_url" in anonymized:
            anonymized["cv_url"] = "''"

        if "linkedin" in anonymized:
            anonymized["linkedin"] = "''"

        # Anonymize text fields
        if "job_description" in anonymized:
            if record["job_description"].strip() not in ("NULL", "''", ""):
                text = self.anonymizer.anonymize_text("job_description")
                # Escape single quotes
                text = text.replace("'", "''")
                anonymized["job_description"] = f"'{text}'"
            else:
                anonymized["job_description"] = "''"

        if "comment" in anonymized:
            if record["comment"].strip() == "NULL":
                anonymized["comment"] = "NULL"
            else:
                text = self.anonymizer.anonymize_text("comment")
                text = text.replace("'", "''")
                anonymized["comment"] = f"'{text}'"

        return anonymized


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Anonymize PII data in seed.sql file")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("docker/seed/seed.sql"),
        help="Input SQL file path (default: docker/seed/seed.sql)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docker/seed/seed_anonymized.sql"),
        help="Output SQL file path (default: docker/seed/seed_anonymized.sql)",
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    anonymizer = SQLAnonymizer(args.input, args.output)
    anonymizer.run()


if __name__ == "__main__":
    main()
