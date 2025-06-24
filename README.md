# Datadog Streamlit LLM Example

A simple Streamlit app that shows how to build a chatbot using OpenAI's GPT-3.5, instrumented with **Datadog LLM Observability** for full pipeline tracing.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://chatbot-bulh3tfzqio.streamlit.app/)

---

## How to Run Locally

1. Install the requirements

   ```bash
   pip install -r requirements.txt
````

2. Run the app

   ```bash
   streamlit run streamlit_app.py
   ```

3. Optional: Create a `.env` file for secrets

   ```env
   OPENAI_API_KEY=sk-...
   DD_API_KEY=...
   DD_SITE=datadoghq.com
   DD_ML_APP_NAME=chatbot-demo
   DD_SERVICE=streamlit-chatbot
   ```

4. If running in Github Codespaces, add these variables in your Codespace Secrets.
---

## LLM Observability with Datadog

This project uses [`ddtrace.llmobs`](https://docs.datadoghq.com/llm_observability/setup/sdk/python/) to track LLM interactions in Datadog.

### Decorators Used

| Decorator    | Type      | Purpose                                           |
| ------------ | --------- | ------------------------------------------------- |
| `@llm`       | LLM Span  | Tracks GPT calls via OpenAI API                   |
| `@workflow`  | Workflow  | Wraps a single user interaction cycle             |
| `@agent`     | Agent     | Traces the entire Streamlit chatbot logic         |
| `@task`      | Task      | Captures input parsing and session prep           |
| `@tool`      | Tool      | Logs and inspects user input for metadata         |
| `@retrieval` | Retrieval | Simulated document fetching for context injection |
| `@embedding` | Embedding | Generates mock embeddings for input prompt        |

### Span Enrichment

The app also uses `LLMObs.annotate()` to log:

* User input and model responses
* Retrieved documents and embedding metadata
* Turn numbers and message counts
* Tags for Streamlit, OpenAI, and workflow stages

---

## Built With

* [Streamlit](https://streamlit.io)
* [OpenAI Python SDK](https://github.com/openai/openai-python)
* [Datadog LLM Observability](https://docs.datadoghq.com/llm_observability/)

---

## Dashboards & Monitoring

You can visualize all spans and enrichments in the Datadog APM > Traces Explorer. For enhanced insight, set up a custom dashboard filtered by:

* `service:streamlit-chatbot`
* `ml_app:chatbot-demo`

---

## License

MIT