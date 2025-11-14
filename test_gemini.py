#!/usr/bin/env python3
import google.generativeai as genai

api_key = "your_api_key_here"  # Replace with your actual API key
genai.configure(api_key=api_key)

print("\nAvailable Gemini models:")
print("="*60)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
        print(f"   Display name: {model.display_name}")
        print(f"   Description: {model.description[:100]}...")
        print()

print("="*60)
