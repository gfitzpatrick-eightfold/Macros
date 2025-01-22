import json
import os
from typing import Dict, Any
from openai import OpenAI
from time import sleep

class MacroAssistant:
    def __init__(self, api_key: str, assistant_id: str):
        self.client = OpenAI(api_key=api_key)
        self.assistant_id = assistant_id
        self.thread = None
        
    def generate_macro(self, user_requirement: str, api_sample: Dict[Any, Any]) -> Dict[str, Any]:
        """
        Generate a macro based on user requirements and sample API response.
        
        Args:
            user_requirement: String describing what the user wants to achieve
            api_sample: Sample API response showing the structure of available data
            
        Returns:
            Dictionary containing the generated macro configuration
        """
        # Create a new thread for each request
        self.thread = self.client.beta.threads.create()
        
        # Create the message
        message_content = f"""
        User Requirement: {user_requirement}
        
        Sample API Response:
        {json.dumps(api_sample, indent=2)}
        
        Please generate a macro configuration that satisfies this requirement.
        Remember to respond ONLY with a valid JSON object, no additional text or explanation.
        The JSON must follow this exact format:
        {{
            "field_name": {{
                "macro": "standard_macros.chained_macro",
                "kwargs": {{
                    "inner_macro_list": [
                        {{
                            "macro": "adapter_macros.substitute_template",
                            "kwargs": {{
                                "template_string": "template here"
                            }}
                        }}
                    ]
                }}
            }}
        }}
        """
        
        # Add the message to the thread
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=message_content
        )
        
        # Run the assistant
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant_id
        )
        
        # Wait for completion
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            elif run_status.status in ['failed', 'cancelled', 'expired']:
                raise ValueError(f"Assistant run failed with status: {run_status.status}")
            sleep(1)
        
        # Get the response
        messages = self.client.beta.threads.messages.list(
            thread_id=self.thread.id
        )
        
        # Parse the last assistant message
        last_message = next(msg for msg in messages if msg.role == "assistant")
        response_content = last_message.content[0].text.value
        
        # Debug: Print raw response
        print("\nDebug - Raw Assistant Response:")
        print(response_content)
        print("\nAttempting to parse as JSON...")
        
        try:
            # Try to clean the response - remove any markdown code block syntax
            cleaned_response = response_content.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            macro_config = json.loads(cleaned_response)
            return self._validate_macro(macro_config)
        except json.JSONDecodeError as e:
            print(f"\nJSON Parse Error at position {e.pos}: {e.msg}")
            print(f"Near text: {cleaned_response[max(0, e.pos-50):min(len(cleaned_response), e.pos+50)]}")
            raise ValueError("Failed to parse assistant response as JSON. Please try again.")

    def _validate_macro(self, macro_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the generated macro against the schema."""
        if not isinstance(macro_config, dict):
            raise ValueError("Generated macro must be a dictionary")
        
        # Validate the structure matches our expected format
        for field_name, config in macro_config.items():
            if not isinstance(config, dict):
                raise ValueError(f"Configuration for field '{field_name}' must be a dictionary")
            if "macro" not in config:
                raise ValueError(f"Configuration for field '{field_name}' must contain a 'macro' field")
            if "kwargs" not in config:
                raise ValueError(f"Configuration for field '{field_name}' must contain a 'kwargs' field")
            
        return macro_config 