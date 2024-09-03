# AI Research Agent

A Streamlit app that takes a research topic, searches the web, and streams a structured Markdown report token by token as it's written — running entirely on a local Ollama model.

## How it works

```
User input
    └── router          classifies: greeting or research topic
         ├── greeter    replies conversationally
         └── planner    breaks topic into N sections
                └── researcher × N  (parallel)  searches & summarises each section
                        └── writer   synthesises all sections → streams final report
```

The graph is built with LangGraph. The writer streams its output token by token into the UI. Researcher nodes run in parallel — a 6-section report takes roughly the same time as a 1-section report.

## Project structure

```
research_agent/
├── app.py                  # Streamlit entry point
├── requirements.txt
├── .env
└── src/
    ├── agent.py            # ResearchAgent class — all node logic in one place
    ├── graph.py            # LangGraph graph wiring + streaming functions
    ├── prompts.py          # All LLM prompts
    ├── state.py            # TypedDicts: ResearchState, Section, Brief
    ├── config.py           # Env var constants
    ├── llm.py              # Ollama LLM factory
    ├── diagram.py          # Prints Mermaid diagram of the graph
    ├── tools/
    │   └── search.py       # DuckDuckGo search with retry logic
    └── utils/
        └── log.py          # Logging configuration
```

## Setup

**1. Install Ollama and pull a model**

```bash
# Install Ollama — https://ollama.com
ollama pull llama3
ollama serve
```

**2. Install Python dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure environment**

Create a `.env` file in the project root:

```
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=llama3
MAX_WORKERS=8
MAX_SEARCH_RESULTS=5

# Optional — LangSmith tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key_here
LANGCHAIN_PROJECT=research-agent
```

**4. Run the app**

```bash
streamlit run app.py
```

## Features

- **Token-by-token streaming** — report appears word by word as the LLM writes it
- **Live status updates** — UI shows progress through each phase (planning, searching, analysing)
- **Parallel research** — all sections are researched concurrently via LangGraph `Send()`
- **Smart routing** — greetings get a conversational reply; only real topics trigger the research pipeline
- **Download button** — save the finished report as a `.md` file (only shown for research reports)

## Configuration

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `MODEL_NAME` | `llama3` | Any model available via Ollama |
| `MAX_WORKERS` | `8` | Max sections the planner will create |
| `MAX_SEARCH_RESULTS` | `5` | DuckDuckGo results fetched per query |

## Generate graph diagram

```bash
python src/diagram.py
```

Paste the output into [mermaid.live](https://mermaid.live) to visualise the agent graph.
