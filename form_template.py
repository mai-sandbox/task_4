"""
Form Template for CLI Form-Filling Agent

This module defines the structure and fields for each form section used by the
CLI form-filling agent. It provides a comprehensive template that demonstrates
the agent's capabilities for handling different types of form fields and
validation requirements.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class FieldType(Enum):
    """Enumeration of supported field types."""
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    DATE = "date"
    SELECT = "select"
    MULTISELECT = "multiselect"
    BOOLEAN = "boolean"
    NUMBER = "number"
    TEXTAREA = "textarea"


@dataclass
class FormField:
    """
    Represents a single form field with its properties and validation rules.
    
    Attributes:
        name: Unique identifier for the field
        prompt: User-friendly prompt text
        field_type: Type of field (text, email, etc.)
        required: Whether the field is mandatory
        options: Available options for select/multiselect fields
        validation_pattern: Regex pattern for validation
        help_text: Additional help text for the user
        placeholder: Example or placeholder text
        min_length: Minimum length for text fields
        max_length: Maximum length for text fields
    """
    name: str
    prompt: str
    field_type: FieldType = FieldType.TEXT
    required: bool = False
    options: Optional[List[str]] = None
    validation_pattern: Optional[str] = None
    help_text: Optional[str] = None
    placeholder: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None


@dataclass
class FormSection:
    """
    Represents a form section containing multiple fields.
    
    Attributes:
        name: Unique identifier for the section
        title: Display title for the section
        description: Optional description of the section
        fields: List of fields in this section
        order: Display order of the section
    """
    name: str
    title: str
    description: Optional[str]
    fields: List[FormField]
    order: int


class FormTemplate:
    """
    Complete form template defining all sections and fields.
    
    This class provides the structure for a comprehensive user registration
    form that demonstrates various field types and validation scenarios.
    """
    
    def __init__(self):
        self.sections = self._create_form_sections()
    
    def _create_form_sections(self) -> Dict[str, FormSection]:
        """Create and return all form sections with their fields."""
        
        # Personal Information Section
        personal_info_fields = [
            FormField(
                name="first_name",
                prompt="Enter your first name",
                field_type=FieldType.TEXT,
                required=True,
                min_length=2,
                max_length=50,
                help_text="Your legal first name as it appears on official documents",
                placeholder="e.g., John"
            ),
            FormField(
                name="last_name",
                prompt="Enter your last name",
                field_type=FieldType.TEXT,
                required=True,
                min_length=2,
                max_length=50,
                help_text="Your legal last name as it appears on official documents",
                placeholder="e.g., Smith"
            ),
            FormField(
                name="date_of_birth",
                prompt="Enter your date of birth",
                field_type=FieldType.DATE,
                required=True,
                validation_pattern=r"^\d{4}-\d{2}-\d{2}$",
                help_text="Format: YYYY-MM-DD (e.g., 1990-01-15)",
                placeholder="1990-01-15"
            ),
            FormField(
                name="phone",
                prompt="Enter your phone number",
                field_type=FieldType.PHONE,
                required=False,
                validation_pattern=r"^[\+]?[1-9][\d]{0,15}$",
                help_text="Include country code if international (e.g., +1-555-123-4567)",
                placeholder="+1-555-123-4567"
            ),
            FormField(
                name="gender",
                prompt="Select your gender",
                field_type=FieldType.SELECT,
                required=False,
                options=["Male", "Female", "Non-binary", "Prefer not to say"],
                help_text="This information is optional and used for demographic purposes only"
            )
        ]
        
        # Contact Information Section
        contact_info_fields = [
            FormField(
                name="email",
                prompt="Enter your email address",
                field_type=FieldType.EMAIL,
                required=True,
                validation_pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                help_text="We'll use this email for important notifications",
                placeholder="john.smith@example.com"
            ),
            FormField(
                name="address",
                prompt="Enter your street address",
                field_type=FieldType.TEXT,
                required=True,
                max_length=200,
                help_text="Include apartment, suite, or unit number if applicable",
                placeholder="123 Main Street, Apt 4B"
            ),
            FormField(
                name="city",
                prompt="Enter your city",
                field_type=FieldType.TEXT,
                required=True,
                min_length=2,
                max_length=100,
                placeholder="New York"
            ),
            FormField(
                name="state",
                prompt="Enter your state/province",
                field_type=FieldType.TEXT,
                required=True,
                min_length=2,
                max_length=50,
                help_text="Full name or abbreviation (e.g., California or CA)",
                placeholder="California"
            ),
            FormField(
                name="zip_code",
                prompt="Enter your ZIP/postal code",
                field_type=FieldType.TEXT,
                required=True,
                validation_pattern=r"^[0-9]{5}(-[0-9]{4})?$|^[A-Za-z]\d[A-Za-z] \d[A-Za-z]\d$",
                help_text="US ZIP code (12345 or 12345-6789) or Canadian postal code (A1A 1A1)",
                placeholder="12345 or A1A 1A1"
            ),
            FormField(
                name="country",
                prompt="Select your country",
                field_type=FieldType.SELECT,
                required=True,
                options=[
                    "United States", "Canada", "United Kingdom", "Australia",
                    "Germany", "France", "Japan", "Other"
                ],
                help_text="Select your country of residence"
            )
        ]
        
        # Preferences Section
        preferences_fields = [
            FormField(
                name="newsletter",
                prompt="Subscribe to our newsletter?",
                field_type=FieldType.BOOLEAN,
                required=False,
                help_text="Receive updates about new features and important announcements"
            ),
            FormField(
                name="contact_method",
                prompt="Preferred contact method",
                field_type=FieldType.SELECT,
                required=False,
                options=["Email", "Phone", "Mail", "SMS"],
                help_text="How would you like us to contact you for non-urgent matters?"
            ),
            FormField(
                name="interests",
                prompt="Select your areas of interest",
                field_type=FieldType.MULTISELECT,
                required=False,
                options=[
                    "Technology", "Business", "Health & Wellness", "Education",
                    "Entertainment", "Sports", "Travel", "Food & Cooking",
                    "Arts & Culture", "Science", "Finance", "Environment"
                ],
                help_text="Select all that apply (comma-separated if multiple)"
            ),
            FormField(
                name="experience_level",
                prompt="What is your experience level with our services?",
                field_type=FieldType.SELECT,
                required=False,
                options=["Beginner", "Intermediate", "Advanced", "Expert"],
                help_text="This helps us provide more relevant content"
            ),
            FormField(
                name="comments",
                prompt="Additional comments or special requests",
                field_type=FieldType.TEXTAREA,
                required=False,
                max_length=500,
                help_text="Optional: Share any additional information or special requirements",
                placeholder="Enter any additional comments here..."
            )
        ]
        
        # Create sections
        sections = {
            "personal_info": FormSection(
                name="personal_info",
                title="Personal Information",
                description="Please provide your basic personal information. Required fields are marked with an asterisk (*).",
                fields=personal_info_fields,
                order=1
            ),
            "contact_info": FormSection(
                name="contact_info",
                title="Contact Information",
                description="Please provide your contact details so we can reach you when necessary.",
                fields=contact_info_fields,
                order=2
            ),
            "preferences": FormSection(
                name="preferences",
                title="Preferences & Interests",
                description="Help us personalize your experience by sharing your preferences (all optional).",
                fields=preferences_fields,
                order=3
            )
        }
        
        return sections
    
    def get_section(self, section_name: str) -> Optional[FormSection]:
        """Get a specific form section by name."""
        return self.sections.get(section_name)
    
    def get_all_sections(self) -> Dict[str, FormSection]:
        """Get all form sections."""
        return self.sections
    
    def get_sections_in_order(self) -> List[FormSection]:
        """Get all sections sorted by their order."""
        return sorted(self.sections.values(), key=lambda x: x.order)
    
    def get_field(self, section_name: str, field_name: str) -> Optional[FormField]:
        """Get a specific field from a section."""
        section = self.get_section(section_name)
        if section:
            for field in section.fields:
                if field.name == field_name:
                    return field
        return None
    
    def validate_field_value(self, section_name: str, field_name: str, value: str) -> tuple[bool, Optional[str]]:
        """
        Validate a field value against its validation rules.
        
        Args:
            section_name: Name of the section
            field_name: Name of the field
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        field = self.get_field(section_name, field_name)
        if not field:
            return False, f"Field {field_name} not found in section {section_name}"
        
        # Check required fields
        if field.required and not value.strip():
            return False, f"{field.prompt} is required"
        
        # Skip validation for empty optional fields
        if not value.strip() and not field.required:
            return True, None
        
        # Length validation
        if field.min_length and len(value) < field.min_length:
            return False, f"{field.prompt} must be at least {field.min_length} characters long"
        
        if field.max_length and len(value) > field.max_length:
            return False, f"{field.prompt} must be no more than {field.max_length} characters long"
        
        # Pattern validation
        if field.validation_pattern:
            import re
            if not re.match(field.validation_pattern, value):
                return False, f"{field.prompt} format is invalid. {field.help_text or ''}"
        
        # Options validation for select fields
        if field.field_type in [FieldType.SELECT] and field.options:
            if value not in field.options:
                return False, f"{field.prompt} must be one of: {', '.join(field.options)}"
        
        return True, None
    
    def to_simple_dict(self) -> Dict[str, Any]:
        """
        Convert the form template to a simple dictionary format
        compatible with the existing agent implementation.
        """
        simple_sections = {}
        
        for section_name, section in self.sections.items():
            simple_fields = []
            for field in section.fields:
                simple_field = {
                    "name": field.name,
                    "prompt": field.prompt,
                    "required": field.required
                }
                
                # Add additional properties if they exist
                if field.help_text:
                    simple_field["help_text"] = field.help_text
                if field.placeholder:
                    simple_field["placeholder"] = field.placeholder
                if field.options:
                    simple_field["options"] = field.options
                
                simple_fields.append(simple_field)
            
            simple_sections[section_name] = {
                "title": section.title,
                "description": section.description,
                "fields": simple_fields
            }
        
        return simple_sections


# Create a global instance for easy access
form_template = FormTemplate()

# Export the simple dictionary format for backward compatibility
FORM_SECTIONS = form_template.to_simple_dict()

# Section processing order
SECTION_ORDER = ["personal_info", "contact_info", "preferences", "review"]


def get_field_validation_info(section_name: str, field_name: str) -> Dict[str, Any]:
    """
    Get validation information for a specific field.
    
    Args:
        section_name: Name of the section
        field_name: Name of the field
        
    Returns:
        Dictionary containing validation information
    """
    field = form_template.get_field(section_name, field_name)
    if not field:
        return {}
    
    validation_info = {
        "required": field.required,
        "field_type": field.field_type.value,
    }
    
    if field.min_length:
        validation_info["min_length"] = field.min_length
    if field.max_length:
        validation_info["max_length"] = field.max_length
    if field.validation_pattern:
        validation_info["pattern"] = field.validation_pattern
    if field.options:
        validation_info["options"] = field.options
    if field.help_text:
        validation_info["help_text"] = field.help_text
    if field.placeholder:
        validation_info["placeholder"] = field.placeholder
    
    return validation_info


def validate_form_data(form_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validate complete form data against the template.
    
    Args:
        form_data: Dictionary containing form field values
        
    Returns:
        Dictionary mapping section names to lists of validation errors
    """
    errors = {}
    
    for section_name, section in form_template.get_all_sections().items():
        section_errors = []
        
        for field in section.fields:
            value = form_data.get(field.name, "")
            is_valid, error_message = form_template.validate_field_value(
                section_name, field.name, str(value)
            )
            
            if not is_valid and error_message:
                section_errors.append(error_message)
        
        if section_errors:
            errors[section_name] = section_errors
    
    return errors


if __name__ == "__main__":
    # Demonstration of the form template
    print("🔥 CLI Form-Filling Agent - Form Template")
    print("=" * 50)
    
    # Display all sections and their fields
    for section in form_template.get_sections_in_order():
        print(f"\n📝 {section.title}")
        if section.description:
            print(f"   {section.description}")
        print("-" * 40)
        
        for field in section.fields:
            required_marker = " *" if field.required else ""
            print(f"   • {field.prompt}{required_marker}")
            if field.help_text:
                print(f"     Help: {field.help_text}")
            if field.options:
                print(f"     Options: {', '.join(field.options)}")
            print()
    
    print("\n✨ Form template loaded successfully!")
    print(f"Total sections: {len(form_template.sections)}")
    total_fields = sum(len(section.fields) for section in form_template.sections.values())
    print(f"Total fields: {total_fields}")
