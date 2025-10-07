# API Keys Setup Guide - BestMove RAG

**Status:** ⚠️ **Required before running code.ipynb**

The agentic RAG system needs LLM access to work. Here's what you need:

---

## 🔑 Required API Keys

### 1. **OpenAI API Key** (REQUIRED ✅)

**What it's for:**
- Query optimization (Cell 45)
- Supervisor/Planner reasoning (Cell 66)
- Response synthesis
- All LLM-powered nodes

**How to get it:**

1. **Go to:** https://platform.openai.com/api-keys
2. **Sign in** or create account
3. **Click:** "Create new secret key"
4. **Name it:** "BestMove RAG" (or any name)
5. **Copy the key** (starts with `sk-...`)
6. **⚠️ SAVE IT IMMEDIATELY** - you can't view it again!

**Cost:**
- **Input:** ~$2.50 per 1M tokens (GPT-4o-mini)
- **Output:** ~$10 per 1M tokens
- **Typical query:** ~$0.001-0.01 per query
- **Expected usage:** ~$5-20/month for R&D

**Models used in notebook:**
- `gpt-4o-mini` - Fast, cheap, good for most tasks
- `gpt-4o` - More powerful, used for complex reasoning

---

### 2. **LangSmith API Key** (OPTIONAL 🔹)

**What it's for:**
- Observability and tracing
- Debug LLM calls
- View agent reasoning steps
- Performance monitoring

**How to get it:**

1. **Go to:** https://smith.langchain.com/
2. **Sign in** with GitHub or email
3. **Click:** Settings → API Keys
4. **Create new key**
5. **Copy the key**

**Cost:** Free tier available (10K traces/month)

**Do you need it?**
- ✅ YES if: Debugging agent behavior, monitoring performance
- ❌ NO if: Just want to query and get results

**You can skip this for now and add it later!**

---

### 3. **Tavily API Key** (OPTIONAL 🔹)

**What it's for:**
- Scout web search tool (Cell 56)
- Real-time web searches
- Finding current information not in research papers

**How to get it:**

1. **Go to:** https://tavily.com/
2. **Sign up** for free account
3. **Dashboard** → API Keys
4. **Copy your key**

**Cost:** Free tier (1,000 searches/month)

**Do you need it?**
- ✅ YES if: Need current stock prices, recent news, competitor info
- ❌ NO if: Only querying research papers (BestMove's main use case)

**You can skip this for now!** The Librarian RAG tool doesn't need it.

---

## 🚀 How to Set Up in Jupyter

### Step 1: Open Jupyter

```bash
cd /home/jschu/projects/Agentic.RAG
source venv/bin/activate
jupyter notebook code.ipynb
```

### Step 2: Run Cell 6 (API Key Setup)

The notebook will prompt you:

```
Enter your OpenAI API Key: ········
Enter your LangSmith API Key: ········  # Optional - press Enter to skip
Enter your Tavily API Key: ········     # Optional - press Enter to skip
```

**Enter your OpenAI key and press Enter.**

For optional keys:
- Have them? Enter them.
- Don't have them? Just press Enter to skip.

### Step 3: Verify

You should see:
```
API keys and environment variables are set.
OpenAI Key loaded: sk-pr...
```

✅ **You're ready to go!**

---

## 🔐 Security Best Practices

### ✅ DO:
- Store keys in password manager (1Password, Bitwarden)
- Use `.env` file for production (already in `.gitignore`)
- Rotate keys periodically
- Use separate keys for dev/prod

### ❌ DON'T:
- Commit keys to GitHub
- Share keys in Slack/email
- Hard-code keys in scripts
- Use same key across multiple projects

---

## 🧪 Testing Without Full Setup

### Minimal Setup (OpenAI only):

```python
# Cell 6 - Just set OpenAI
import os
os.environ["OPENAI_API_KEY"] = "sk-your-key-here"
os.environ["LANGCHAIN_TRACING_V2"] = "false"  # Disable LangSmith
# Skip Tavily - Scout tool won't work, but Librarian will!
```

**This is enough to:**
- ✅ Run Librarian RAG tool (query research papers)
- ✅ Test Supervisor/Planner
- ✅ Get AI-powered responses
- ❌ Can't use Scout web search (that's fine!)

---

## 💰 Cost Estimates

### Light Usage (Testing, Development):
```
~50 queries/day × $0.005/query × 30 days = ~$7.50/month
```

### Medium Usage (Active R&D):
```
~200 queries/day × $0.005/query × 30 days = ~$30/month
```

### Heavy Usage (Production Chatbot):
```
~1000 queries/day × $0.005/query × 30 days = ~$150/month
```

**Optimization tip:** Use `gpt-4o-mini` for most tasks (already configured!)

---

## 🔄 Alternative: Use Local LLMs (Advanced)

**Don't want to pay for OpenAI?** You can use local LLMs:

### Option 1: Ollama (Free, Local)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download a model
ollama pull llama3.1:8b

# Update notebook to use Ollama
from langchain_community.llms import Ollama
llm = Ollama(model="llama3.1:8b")
```

**Pros:** Free, private, no API limits  
**Cons:** Slower, lower quality, needs good GPU

### Option 2: Claude via Anthropic (Alternative to OpenAI)

```python
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key="...")
```

**Cost:** Similar to OpenAI (~$3-15/1M tokens)

---

## 📝 Quick Start Checklist

- [ ] Get OpenAI API key from platform.openai.com
- [ ] Open Jupyter: `jupyter notebook code.ipynb`
- [ ] Run Cell 6 and enter your OpenAI key
- [ ] (Optional) Skip LangSmith and Tavily by pressing Enter
- [ ] Run Cell 13 to connect to vector database
- [ ] Run Cell 47 to test Librarian tool
- [ ] Try a query: "What magnesium dose improves sleep?"

---

## 🆘 Troubleshooting

### "Invalid API key" error:
- Check key starts with `sk-proj-` or `sk-...`
- Make sure you copied the full key
- Try regenerating a new key

### "Rate limit exceeded":
- You hit OpenAI's usage limits
- Wait a few minutes or upgrade billing tier
- Check usage at platform.openai.com/usage

### "Module not found: langchain_openai":
- Run: `pip install langchain-openai`
- Or: `pip install -r requirements.txt` (if it exists)

### "Can't connect to LangSmith":
- It's optional! Disable with: `os.environ["LANGCHAIN_TRACING_V2"] = "false"`

---

## 🎯 Recommended Setup for BestMove

### For Initial Testing:
```
✅ OpenAI API key (required)
❌ LangSmith (skip)
❌ Tavily (skip)
```

### For Production R&D Tool:
```
✅ OpenAI API key (required)
✅ LangSmith (for monitoring)
❌ Tavily (Librarian tool is enough)
```

### For Customer Chatbot:
```
✅ OpenAI API key (required)
✅ LangSmith (for monitoring customer queries)
✅ Tavily (for "what's the latest research?" questions)
```

---

## 📚 Next Steps

1. **Get OpenAI key** (5 minutes)
2. **Run Cell 6** in notebook (30 seconds)
3. **Run Cell 13** to connect to vector DB (5 seconds)
4. **Test a query!** (2 seconds)

**Total time to first query: ~6 minutes!** 🚀

---

**Ready?** Open Jupyter and let's query some research papers! 🎉

