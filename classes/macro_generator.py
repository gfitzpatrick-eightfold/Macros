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
            
        # Load example macro usage
        example_usage_path = os.path.join(project_root, 'examples', 'example_macro_usage.json')
        with open(example_usage_path, 'r') as f:
            self.example_usage = json.load(f)

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
                The response MUST be a valid JSON object in the format:
                {
                    "field_name": {
                        "macro": "name_of_macro",
                        "kwargs": {
                            // required parameters for the macro
                        }
                    }
                }
                
                For path extraction, use standard_macros.extract_path with the expr parameter.
                For combining multiple fields, use standard_macros.chained_macro with adapter_macros.substitute_template.
                Follow the examples from the example_macro_usage.json file exactly.
                
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

        # Extract relevant examples from example usage
        relevant_examples = {
            "path_extraction": {
                "custom_info.LevelName": {
                    "macro": "standard_macros.extract_path",
                    "kwargs": {
                        "expr": "cust_JobCodeNav.results[0].jobLevelNav.picklistLabels.results[0].label"
                    }
                }
            },
            "field_combination": {
                "role_description": {
                    "macro": "standard_macros.chained_macro",
                    "kwargs": {
                        "inner_macro_list": [
                            {
                                "macro": "adapter_macros.substitute_template",
                                "kwargs": {
                                    "template_string": "{{ longDesciptions.results[0].desc_localized }} {{ headers.results[0].desc_defaultValue }} {{ jobResponsibilityContents.results[0].entityNav.name_defaultValue }}"
                                }
                            }
                        ]
                    }
                }
            }
        }

        return f"""
        Based on the following information, generate a macro configuration:

        User Requirement: {user_requirement}
        
        Sample API Response:
        {json.dumps(api_sample, indent=2)}
        
        Available Macros:
        {json.dumps(available_macros, indent=2)}
        
        Example Macro Configurations:
        {json.dumps(relevant_examples, indent=2)}
        
        The macro configuration must:
        1. Follow the exact format shown in the examples
        2. Include the target field name as the top-level key
        3. Use standard_macros.extract_path for path extraction with expr parameter
        4. Use standard_macros.chained_macro with adapter_macros.substitute_template for combining fields
        5. Be a valid JSON object
        
        Respond ONLY with the JSON object, no additional text or explanation.
        """

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