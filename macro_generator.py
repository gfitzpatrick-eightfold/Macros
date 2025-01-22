import os
import json
from classes.macro_generator import MacroGenerator

def main():
    # Get OpenAI API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set OPENAI_API_KEY environment variable")
    
    # Get the absolute path to the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    generator = MacroGenerator(api_key)
    
    # Load example API response
    api_response_path = os.path.join(project_root, 'examples', 'example_api_response.json')
    with open(api_response_path, 'r') as f:
        api_sample = json.load(f)
    
    # Example usage
    user_requirement = "I want to extract the candidate's first name from the API response"
    
    try:
        macro = generator.generate_macro(user_requirement, api_sample)
        print("\nGenerated Macro:")
        print(json.dumps(macro, indent=2))
    except Exception as e:
        print(f"\nError generating macro: {str(e)}")

if __name__ == "__main__":
    main() 