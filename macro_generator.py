import os
import json
import argparse
from dotenv import load_dotenv
from classes.macro_generator import MacroGenerator

def load_api_response(file_path: str) -> dict:
    """Load and validate the API response from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON file. Please provide a valid JSON file for the API response.")
    except FileNotFoundError:
        raise ValueError(f"File not found: {file_path}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate macros based on user requirements and API response')
    parser.add_argument('--api-response', type=str, help='Path to the JSON file containing the API response')
    args = parser.parse_args()

    # Load environment variables from .env file
    load_dotenv()
    
    # Get OpenAI API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API key not found. Please:\n"
            "1. Copy .env.template to .env\n"
            "2. Add your OpenAI API key to the .env file"
        )
    
    # Initialize generator
    generator = MacroGenerator(api_key)
    
    # Load API response
    if args.api_response:
        api_sample = load_api_response(args.api_response)
    else:
        # Use default example if no file provided
        project_root = os.path.dirname(os.path.abspath(__file__))
        default_response_path = os.path.join(project_root, 'examples', 'example_api_response.json')
        print(f"\nNo API response file provided. Using default example from: {default_response_path}")
        api_sample = load_api_response(default_response_path)
    
    # Get user requirement
    print("\nPlease describe what you want to extract or transform from the API response.")
    print("For example: 'I want to extract the candidate's first name' or 'I need to combine first and last name'")
    user_requirement = input("\nYour requirement: ").strip()
    
    if not user_requirement:
        raise ValueError("Requirement cannot be empty")
    
    try:
        macro = generator.generate_macro(user_requirement, api_sample)
        print("\nGenerated Macro:")
        print(json.dumps(macro, indent=2))
    except Exception as e:
        print(f"\nError generating macro: {str(e)}")

if __name__ == "__main__":
    main() 