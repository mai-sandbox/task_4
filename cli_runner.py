#!/usr/bin/env python3
"""
CLI Runner for Form-Filling Agent

This script provides a command-line interface for interacting with the LangGraph
form-filling agent. It handles user input collection, manages graph execution
with checkpointing, and uses Command objects to resume execution after interrupts.
"""

import uuid
import sys
from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text

from langgraph.types import Command
from agent import app, FORM_SECTIONS


class CLIFormRunner:
    """Command-line interface for the form-filling agent."""
    
    def __init__(self):
        self.console = Console()
        self.thread_id = str(uuid.uuid4())
        self.config = {
            "configurable": {
                "thread_id": self.thread_id
            }
        }
    
    def display_welcome(self):
        """Display welcome message and instructions."""
        welcome_text = Text()
        welcome_text.append("🔥 CLI Form-Filling Agent", style="bold blue")
        welcome_text.append("\n\nThis agent will guide you through filling out a form section by section.")
        welcome_text.append("\nYou can provide information for each field, and the agent will save your progress.")
        welcome_text.append("\n\nPress Ctrl+C at any time to exit.")
        
        panel = Panel(
            welcome_text,
            title="Welcome",
            border_style="blue",
            padding=(1, 2)
        )
        self.console.print(panel)
        self.console.print()
    
    def collect_section_data(self, interrupt_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect user input for a form section.
        
        Args:
            interrupt_data: Data from the interrupt containing section info and fields
            
        Returns:
            Dictionary containing collected field values
        """
        section_name = interrupt_data["section_name"]
        section_title = interrupt_data["section_title"]
        fields = interrupt_data["fields"]
        
        # Display section header
        self.console.print(f"\n📝 {section_title}", style="bold green")
        self.console.print("=" * (len(section_title) + 4))
        
        collected_data = {}
        
        for field in fields:
            field_name = field["name"]
            prompt_text = field["prompt"]
            required = field.get("required", False)
            
            # Create prompt with required indicator
            if required:
                display_prompt = f"{prompt_text} [red]*[/red]"
            else:
                display_prompt = f"{prompt_text} (optional)"
            
            # Collect input with validation for required fields
            while True:
                try:
                    value = Prompt.ask(display_prompt, console=self.console)
                    
                    # Validate required fields
                    if required and not value.strip():
                        self.console.print("❌ This field is required. Please provide a value.", style="red")
                        continue
                    
                    # Store the value (empty string for optional fields if not provided)
                    collected_data[field_name] = value.strip()
                    break
                    
                except KeyboardInterrupt:
                    self.console.print("\n\n👋 Form filling cancelled by user.", style="yellow")
                    sys.exit(0)
        
        # Show collected data for this section
        self.console.print(f"\n✅ {section_title} completed!", style="green")
        self._display_section_summary(collected_data)
        
        return collected_data
    
    def review_form_data(self, interrupt_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Display form data for review and get user confirmation.
        
        Args:
            interrupt_data: Data containing form data and completed sections
            
        Returns:
            Dictionary with confirmation status
        """
        form_data = interrupt_data["form_data"]
        completed_sections = interrupt_data["completed_sections"]
        
        # Display review header
        self.console.print("\n🔍 Form Review", style="bold blue")
        self.console.print("=" * 15)
        
        # Create a comprehensive review table
        table = Table(title="Your Form Data", show_header=True, header_style="bold magenta")
        table.add_column("Section", style="cyan", width=20)
        table.add_column("Field", style="green", width=25)
        table.add_column("Value", style="white", width=30)
        
        # Group data by sections for better display
        for section_name in ["personal_info", "contact_info", "preferences"]:
            if section_name in completed_sections:
                section_config = FORM_SECTIONS[section_name]
                section_title = section_config["title"]
                
                # Add section data to table
                first_field = True
                for field in section_config["fields"]:
                    field_name = field["name"]
                    field_prompt = field["prompt"]
                    field_value = form_data.get(field_name, "")
                    
                    # Display section name only for first field
                    section_display = section_title if first_field else ""
                    first_field = False
                    
                    # Handle empty values
                    display_value = field_value if field_value else "[dim]Not provided[/dim]"
                    
                    table.add_row(section_display, field_prompt, display_value)
        
        self.console.print(table)
        
        # Get user confirmation
        self.console.print()
        try:
            confirmed = Confirm.ask("✅ Is this information correct? Do you want to submit the form?", console=self.console)
            
            if confirmed:
                self.console.print("🎉 Form submitted successfully!", style="bold green")
            else:
                self.console.print("📝 You can modify the form data if needed.", style="yellow")
            
            return {"confirmed": confirmed}
            
        except KeyboardInterrupt:
            self.console.print("\n\n👋 Form review cancelled by user.", style="yellow")
            sys.exit(0)
    
    def _display_section_summary(self, section_data: Dict[str, Any]):
        """Display a summary of collected section data."""
        if not section_data:
            return
            
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        for field_name, value in section_data.items():
            display_value = value if value else "[dim]Not provided[/dim]"
            table.add_row(f"  {field_name}:", display_value)
        
        self.console.print(table)
    
    def handle_interrupt(self, interrupt_info: Dict[str, Any]) -> Command:
        """
        Handle an interrupt from the agent and collect user input.
        
        Args:
            interrupt_info: Information about the interrupt
            
        Returns:
            Command object to resume execution
        """
        interrupt_data = interrupt_info["value"]
        action = interrupt_data.get("action")
        
        if action == "collect_section_data":
            # Collect data for a form section
            collected_data = self.collect_section_data(interrupt_data)
            return Command(resume=collected_data)
            
        elif action == "review_form":
            # Review and confirm form data
            confirmation = self.review_form_data(interrupt_data)
            return Command(resume=confirmation)
            
        else:
            # Unknown action - provide empty response
            self.console.print(f"⚠️  Unknown interrupt action: {action}", style="yellow")
            return Command(resume={})
    
    def run_form_filling(self):
        """Main method to run the form-filling process."""
        try:
            self.display_welcome()
            
            # Start the form-filling process
            self.console.print("🚀 Starting form-filling process...\n", style="bold")
            
            # Initial state for the form
            initial_state = {
                "form_data": {},
                "current_section": "personal_info",
                "completed_sections": [],
                "is_complete": False
            }
            
            # Stream the graph execution
            for event in app.stream(initial_state, self.config, stream_mode="values"):
                # Check if we have an interrupt
                if "__interrupt__" in event:
                    interrupt_info = event["__interrupt__"][0]  # Get first interrupt
                    
                    # Handle the interrupt and get resume command
                    resume_command = self.handle_interrupt({"value": interrupt_info.value})
                    
                    # Continue execution with the resume command
                    for continue_event in app.stream(resume_command, self.config, stream_mode="values"):
                        if continue_event.get("is_complete", False):
                            self._display_completion_message(continue_event)
                            return
                
                # Check if form is complete
                elif event.get("is_complete", False):
                    self._display_completion_message(event)
                    return
            
        except KeyboardInterrupt:
            self.console.print("\n\n👋 Form filling cancelled by user.", style="yellow")
            sys.exit(0)
        except Exception as e:
            self.console.print(f"\n❌ An error occurred: {str(e)}", style="red")
            sys.exit(1)
    
    def _display_completion_message(self, final_state: Dict[str, Any]):
        """Display completion message with final form data."""
        self.console.print("\n" + "="*50, style="green")
        self.console.print("🎉 FORM COMPLETED SUCCESSFULLY! 🎉", style="bold green")
        self.console.print("="*50, style="green")
        
        # Display final summary
        form_data = final_state.get("form_data", {})
        if form_data:
            self.console.print("\n📋 Final Form Summary:", style="bold blue")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Field", style="cyan", width=25)
            table.add_column("Value", style="white", width=35)
            
            for field_name, value in form_data.items():
                display_value = value if value else "[dim]Not provided[/dim]"
                table.add_row(field_name.replace("_", " ").title(), display_value)
            
            self.console.print(table)
        
        self.console.print("\n✨ Thank you for using the CLI Form-Filling Agent!", style="bold green")


def main():
    """Main entry point for the CLI runner."""
    runner = CLIFormRunner()
    runner.run_form_filling()


if __name__ == "__main__":
    main()
