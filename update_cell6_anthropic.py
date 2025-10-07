#!/usr/bin/env python3
"""
Update Cell 6 (set-keys) to use Anthropic instead of OpenAI
"""

import json

NOTEBOOK_PATH = "code.ipynb"

print("Reading notebook...")
with open(NOTEBOOK_PATH, 'r') as f:
    notebook = json.load(f)

# Find the cell with id "set-keys"
target_cell_idx = None
for i, cell in enumerate(notebook['cells']):
    if cell.get('id') == 'set-keys':
        target_cell_idx = i
        print(f"Found 'set-keys' cell at index {i}")
        break

if target_cell_idx is None:
    print("ERROR: Could not find cell with id 'set-keys'")
    exit(1)

# New cell content
new_source = [
    "# BestMove RAG uses Claude (Anthropic) for LLM-powered reasoning\n",
    "# API key should be set in ~/.bashrc: export ANTHROPIC_API_KEY=\"sk-ant-...\"\n",
    "\n",
    "if \"ANTHROPIC_API_KEY\" not in os.environ:\n",
    "    print(\"⚠️  ANTHROPIC_API_KEY not found in environment!\")\n",
    "    print(\"   Please set it in ~/.bashrc or enter it now:\")\n",
    "    os.environ[\"ANTHROPIC_API_KEY\"] = getpass(\"Enter your Anthropic API Key: \")\n",
    "\n",
    "# Optional: LangSmith for observability (press Enter to skip)\n",
    "if \"LANGCHAIN_API_KEY\" not in os.environ:\n",
    "    langsmith_key = getpass(\"Enter your LangSmith API Key (optional, press Enter to skip): \")\n",
    "    if langsmith_key:\n",
    "        os.environ[\"LANGCHAIN_API_KEY\"] = langsmith_key\n",
    "        os.environ[\"LANGCHAIN_TRACING_V2\"] = \"true\"\n",
    "        os.environ[\"LANGCHAIN_ENDPOINT\"] = \"https://api.smith.langchain.com\"\n",
    "        os.environ[\"LANGCHAIN_PROJECT\"] = \"BestMove_Electrolyte_RAG\"\n",
    "    else:\n",
    "        os.environ[\"LANGCHAIN_TRACING_V2\"] = \"false\"\n",
    "        print(\"   Skipped LangSmith (observability disabled)\")\n",
    "\n",
    "# Optional: Tavily for web search (press Enter to skip)\n",
    "if \"TAVILY_API_KEY\" not in os.environ:\n",
    "    tavily_key = getpass(\"Enter your Tavily API Key (optional, press Enter to skip): \")\n",
    "    if tavily_key:\n",
    "        os.environ[\"TAVILY_API_KEY\"] = tavily_key\n",
    "    else:\n",
    "        print(\"   Skipped Tavily (web search disabled)\")\n",
    "\n",
    "print(\"\\n✅ API keys configured!\")\n",
    "print(f\"   Claude Key: {os.environ['ANTHROPIC_API_KEY'][:15]}...{os.environ['ANTHROPIC_API_KEY'][-10:]}\")\n",
    "print(f\"   LangSmith: {'Enabled' if os.environ.get('LANGCHAIN_TRACING_V2') == 'true' else 'Disabled'}\")\n",
    "print(f\"   Tavily: {'Enabled' if os.environ.get('TAVILY_API_KEY') else 'Disabled'}\")"
]

# Update the cell
notebook['cells'][target_cell_idx]['source'] = new_source

# Clear outputs
notebook['cells'][target_cell_idx]['outputs'] = []
notebook['cells'][target_cell_idx]['execution_count'] = None

print("\nWriting updated notebook...")
with open(NOTEBOOK_PATH, 'w') as f:
    json.dump(notebook, f, indent=1)

print("✅ Cell 6 updated successfully!")
print("\nChanges made:")
print("  • Changed from OPENAI_API_KEY → ANTHROPIC_API_KEY")
print("  • Made LangSmith and Tavily optional (can skip)")
print("  • API key loaded from ~/.bashrc automatically")
print("  • Better visual output with status indicators")
print("\nNext: Open Jupyter and run Cell 6!")

