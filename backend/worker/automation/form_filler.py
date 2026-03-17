"""
Intelligent form filling.

Maps user profile fields to form inputs based on label text analysis.
Handles text, select, radio, and checkbox input types.
"""

import logging
import re
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class FormFiller:
    """
    Intelligently fills form fields by matching labels to user profile data.
    Uses fuzzy matching and common field name patterns.
    """

    # Mapping of label patterns to user profile field paths
    FIELD_MAPPINGS = {
        # Personal info
        r"(first\s*name|given\s*name)": "first_name",
        r"(last\s*name|surname|family\s*name)": "last_name",
        r"(full\s*name|your\s*name|name)": "full_name",
        r"(email|e-mail)": "email",
        r"(phone|mobile|contact\s*number|telephone)": "phone",
        r"(city|current\s*city)": "city",
        r"(state|province)": "state",
        r"(country)": "country",
        r"(zip|postal\s*code|pin\s*code)": "zip_code",
        r"(address|street)": "address",
        r"(linkedin|linkedin\s*url|linkedin\s*profile)": "linkedin_url",
        r"(github|github\s*url|github\s*profile)": "github_url",
        r"(portfolio|website|personal\s*website)": "portfolio_url",

        # Professional info
        r"(current\s*company|company\s*name|employer)": "current_company",
        r"(current\s*title|job\s*title|designation|current\s*role)": "current_title",
        r"(years?\s*of\s*experience|total\s*experience|work\s*experience)": "experience_years",
        r"(salary|current\s*salary|expected\s*salary|ctc|current\s*ctc)": "current_salary",
        r"(expected\s*salary|expected\s*ctc|desired\s*salary)": "expected_salary",
        r"(notice\s*period|availability|when\s*can\s*you\s*(?:start|join))": "notice_period",
        r"(start\s*date|earliest\s*start|join\s*date)": "start_date",

        # Education
        r"(highest\s*education|degree|qualification|education)": "highest_degree",
        r"(university|college|school|institution)": "university",
        r"(major|field\s*of\s*study|specialization)": "major",
        r"(gpa|cgpa|grade|percentage)": "gpa",
        r"(graduation\s*year|year\s*of\s*(?:graduation|passing))": "graduation_year",

        # Skills
        r"(skills|technical\s*skills|key\s*skills)": "skills",
        r"(programming\s*languages?|languages?\s*known)": "programming_languages",
        r"(certifications?|certificates?)": "certifications",

        # Work authorization
        r"(authorized|work\s*authorization|legally\s*authorized|visa\s*status)": "work_authorized",
        r"(sponsorship|visa\s*sponsorship|require\s*sponsorship)": "needs_sponsorship",
        r"(relocat|willing\s*to\s*relocate)": "willing_to_relocate",
        r"(remote|work\s*remotely|open\s*to\s*remote)": "open_to_remote",

        # Diversity (optional)
        r"(gender|sex)": "gender",
        r"(race|ethnicity)": "ethnicity",
        r"(veteran|military)": "veteran_status",
        r"(disability|disabled)": "disability_status",
    }

    # Common select field option mappings
    SELECT_MAPPINGS = {
        "experience_years": {
            r"0|fresher|no\s*experience": "0",
            r"1|1\s*year|0-1": "1",
            r"2|2\s*years|1-2": "2",
            r"3|3\s*years|2-3": "3",
            r"4|4\s*years|3-4": "4",
            r"5|5\s*years|4-5": "5",
            r"6|6\+|5-7|6-8": "6",
            r"8|8\+|7-10": "8",
            r"10|10\+|10-15": "10",
            r"15|15\+": "15",
        },
        "notice_period": {
            r"immediate|0|currently\s*serving": "Immediate",
            r"15\s*days?|2\s*weeks?": "15 Days",
            r"1\s*month|30\s*days?|4\s*weeks?": "1 Month",
            r"2\s*months?|60\s*days?": "2 Months",
            r"3\s*months?|90\s*days?": "3 Months",
        },
        "highest_degree": {
            r"b\.?tech|bachelor.*tech|be\b": "B.Tech/B.E.",
            r"b\.?sc|bachelor.*science": "B.Sc",
            r"bca|bachelor.*computer": "BCA",
            r"bba|bachelor.*business": "BBA",
            r"m\.?tech|master.*tech|me\b": "M.Tech/M.E.",
            r"m\.?sc|master.*science": "M.Sc",
            r"mca|master.*computer": "MCA",
            r"mba|master.*business": "MBA",
            r"phd|doctor": "PhD",
            r"diploma": "Diploma",
            r"12th|high\s*school|hsc": "12th",
        },
    }

    def get_field_value(
        self, label: str, user_profile: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get the appropriate value for a form field based on its label.

        Args:
            label: The field label text
            user_profile: User profile dictionary

        Returns:
            The value to fill or None if no match
        """
        if not label:
            return None

        label_lower = label.lower().strip()

        # Try each pattern
        for pattern, field_name in self.FIELD_MAPPINGS.items():
            if re.search(pattern, label_lower, re.IGNORECASE):
                value = self._resolve_field(field_name, user_profile)
                if value:
                    return str(value)

        return None

    def get_select_value(
        self, label: str, user_profile: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get the appropriate select option value for a dropdown.

        Args:
            label: The field label text
            user_profile: User profile dictionary

        Returns:
            The option value to select or None
        """
        if not label:
            return None

        label_lower = label.lower().strip()

        # Determine which field this maps to
        field_name = None
        for pattern, fname in self.FIELD_MAPPINGS.items():
            if re.search(pattern, label_lower, re.IGNORECASE):
                field_name = fname
                break

        if not field_name:
            return None

        # Get the user's value
        user_value = self._resolve_field(field_name, user_profile)
        if user_value is None:
            return None

        user_value_str = str(user_value).lower()

        # Check if we have specific select mappings
        if field_name in self.SELECT_MAPPINGS:
            for pattern, select_value in self.SELECT_MAPPINGS[field_name].items():
                if re.search(pattern, user_value_str, re.IGNORECASE):
                    return select_value

        return str(user_value)

    def get_radio_value(
        self, label: str, user_profile: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get the appropriate radio button value.

        Args:
            label: The question/field label text
            user_profile: User profile dictionary

        Returns:
            The radio option text to select or None
        """
        if not label:
            return None

        label_lower = label.lower().strip()

        # Yes/No questions based on profile
        yes_no_mappings = {
            r"authorized.*work|legally.*authorized": ("work_authorized", True),
            r"require.*sponsor|need.*sponsor|visa.*sponsor": ("needs_sponsorship", False),
            r"willing.*relocat|open.*relocat": ("willing_to_relocate", True),
            r"remote|work.*remote": ("open_to_remote", True),
            r"18\s*years|legal\s*age": (None, True),  # Always yes
            r"agree|terms|acknowledge": (None, True),  # Always agree
            r"currently.*employed|presently.*working": ("currently_employed", True),
        }

        for pattern, (field, default_yes) in yes_no_mappings.items():
            if re.search(pattern, label_lower, re.IGNORECASE):
                if field:
                    value = self._resolve_field(field, user_profile)
                    if value is not None:
                        return "Yes" if value else "No"
                return "Yes" if default_yes else "No"

        # Experience-related radio
        if re.search(r"experience.*with|proficien|familiar.*with", label_lower):
            return "Yes"  # Default to yes for skill-related questions

        return None

    def _resolve_field(
        self, field_name: str, profile: Dict[str, Any]
    ) -> Optional[Any]:
        """Resolve a field name to a value from the user profile."""
        # Direct field access
        if field_name in profile:
            return profile[field_name]

        # Computed fields
        if field_name == "first_name":
            full_name = profile.get("full_name", "")
            parts = full_name.split()
            return parts[0] if parts else None

        if field_name == "last_name":
            full_name = profile.get("full_name", "")
            parts = full_name.split()
            return " ".join(parts[1:]) if len(parts) > 1 else None

        if field_name == "work_authorized":
            # Default to True for Indian users
            return profile.get("work_authorized", True)

        if field_name == "needs_sponsorship":
            return profile.get("needs_sponsorship", False)

        if field_name == "willing_to_relocate":
            return profile.get("willing_to_relocate", True)

        if field_name == "open_to_remote":
            pref = profile.get("remote_preference", "any")
            return pref in ("remote", "hybrid", "any")

        if field_name == "currently_employed":
            return bool(profile.get("current_company"))

        if field_name == "skills":
            skills = profile.get("skills", "")
            if isinstance(skills, list):
                return ", ".join(skills)
            return skills

        if field_name == "programming_languages":
            skills = profile.get("skills", "")
            if isinstance(skills, str):
                # Filter for programming languages
                langs = ["Python", "JavaScript", "TypeScript", "Java", "C++",
                         "C#", "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin"]
                found = [l for l in langs if l.lower() in skills.lower()]
                return ", ".join(found) if found else skills
            return skills

        return None

    def map_fields_to_form(
        self, form_fields: List[Dict[str, str]], user_profile: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Map a list of form fields to user profile values.

        Args:
            form_fields: List of dicts with 'label', 'type', 'name' keys
            user_profile: User profile data

        Returns:
            Dict mapping field names to values
        """
        result = {}
        for field in form_fields:
            label = field.get("label", "") or field.get("name", "")
            field_type = field.get("type", "text")
            field_name = field.get("name", label)

            if field_type == "select":
                value = self.get_select_value(label, user_profile)
            elif field_type == "radio":
                value = self.get_radio_value(label, user_profile)
            else:
                value = self.get_field_value(label, user_profile)

            if value:
                result[field_name] = value

        return result
