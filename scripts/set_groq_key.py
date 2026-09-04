import getpass
import re
from pathlib import Path

def main():
    env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
    
    print("\n==================================================")
    print(" SANKHYAI Platform - Secure Groq API Key Setup")
    print("==================================================")
    key = getpass.getpass("Paste your GROQ_API_KEY (typing is hidden): ").strip()
    
    if not key:
        print("No key entered. Aborting.")
        return
    
    if not key.startswith("gsk_"):
        print("\nNote: Groq keys usually start with 'gsk_'. Proceeding with entered key...")

    if not env_path.exists():
        example_path = env_path.parent / ".env.example"
        if example_path.exists():
            env_path.write_text(example_path.read_text())
        else:
            env_path.write_text("")

    content = env_path.read_text()

    if "GROQ_API_KEY=" in content:
        content = re.sub(r"GROQ_API_KEY=.*", f"GROQ_API_KEY={key}", content)
    else:
        content += f"\nGROQ_API_KEY={key}\n"

    if "AI_PROVIDER=" in content:
        content = re.sub(r"AI_PROVIDER=.*", "AI_PROVIDER=groq", content)
    else:
        content += "AI_PROVIDER=groq\n"

    env_path.write_text(content)
    print("\n Success! Saved securely to backend/.env")
    print("AI_PROVIDER is now set to 'groq'.")
    print("==================================================\n")

if __name__ == "__main__":
    main()
