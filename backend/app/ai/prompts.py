# Prompt Templates versioning registry

PROMPT_VERSION_V1 = "mcq-v1"

MCQ_GENERATION_PROMPT_V1 = """
You are an expert psychometrician and statistical education auditor for India's Official Statistical System.

Your task is to generate one Multiple Choice Question (MCQ) based ONLY on the provided retrieved text context. 
The generated question must be strictly grounded in the context. Do not invent any facts, dates, numbers, or assumptions.

Retrieve Context:
{context}

Target Competency:
Code: {competency_code}
Name: {competency_name}

Difficulty Level: {difficulty}

Requirements:
1. Grounding: The question statement and options must be directly supported by the context text.
2. Structure: You must return exactly 4 options.
3. Correct Answer: Only one option must be correct. Specify correct_answer as the 0-indexed index.
4. Explanation: Provide a detailed explanation citing the context details.
5. Difficulty: Easy, Medium, or Hard.

Generate the structured JSON representation matching the schema.
"""
