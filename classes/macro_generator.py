import json
import os
from typing import Dict, Any
from openai import OpenAI

class MacroGenerator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        
        # Get the absolute path to the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Load macro definitions for reference
        macro_def_path = os.path.join(project_root, 'examples', 'macro_definitions.json')
        with open(macro_def_path, 'r') as f:
            self.macro_definitions = json.load(f)

    def generate_macro(self, user_requirement: str, api_sample: Dict[Any, Any]) -> Dict[str, Any]:
        """
        Generate a macro based on user requirements and sample API response.
        
        Args:
            user_requirement: String describing what the user wants to achieve
            api_sample: Sample API response showing the structure of available data
            
        Returns:
            Dictionary containing the generated macro configuration
        """
        # Construct the prompt for OpenAI
        prompt = self._construct_prompt(user_requirement, api_sample)
        
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """You are an expert at creating macros for data transformation.
                Your task is to generate a macro configuration that maps external API data to internal fields.
                The response MUST be a valid JSON object with at least these fields:
                {
                    "macro": "name_of_macro",
                    "kwargs": {
                        // any required parameters for the macro
                    }
                }
                Choose the macro from the available macro types in the macro_definitions.json.
                IMPORTANT: Respond ONLY with the JSON object, no additional text or explanation."""},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        # Parse the response
        try:
            macro_config = json.loads(response.choices[0].message.content)
            return self._validate_macro(macro_config)
        except json.JSONDecodeError as e:
            raise ValueError("Failed to generate valid macro configuration")

    def _construct_prompt(self, user_requirement: str, api_sample: Dict[Any, Any]) -> str:
        """Construct the prompt for OpenAI with context about available macros and requirements."""
        available_macros = []
        for schema in self.macro_definitions['macros']['docstring_schema']:
            if 'macro_name' in schema:
                available_macros.append({
                    'name': schema['macro_name'],
                    'description': schema.get('description', ''),
                    'type': schema.get('macro_type', '')
                })

        return f"""
        Based on the following information, generate a macro configuration:

        User Requirement: {user_requirement}
        
        Sample API Response:
        {json.dumps(api_sample, indent=2)}
        
        Available Macros:
        {json.dumps(available_macros, indent=2)}
        
        The macro configuration must:
        1. Use one of the available macros listed above
        2. Include a 'macro' field with the exact macro name
        3. Include a 'kwargs' field with any required parameters
        4. Be a valid JSON object
        
        Example format:
        {{
            "macro": "adapter_macros.example_macro",
            "kwargs": {{
                "field1": "value1",
                "field2": "value2"
            }}
        }}

        Respond ONLY with the JSON object, no additional text or explanation.
        """

    def _validate_macro(self, macro_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the generated macro against the schema."""
        if not isinstance(macro_config, dict):
            raise ValueError("Generated macro must be a dictionary")
        
        if "macro" not in macro_config:
            raise ValueError("Generated macro must contain a 'macro' field")
            
        return macro_config 