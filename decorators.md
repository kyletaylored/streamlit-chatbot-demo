# 🧠 Datadog LLM Observability: Python Decorators

The following decorators are provided by the `ddtrace.llmobs` package to help trace key stages of your LLM-based application. They automatically create and finish spans that appear in Datadog's LLM Observability dashboard.

---

## Overview

| Decorator    | Type      | Purpose                                                 |
| ------------ | --------- | ------------------------------------------------------- |
| `@llm`       | LLM Span  | Traces model inference calls (e.g., OpenAI completions) |
| `@workflow`  | Workflow  | High-level orchestration of multi-step processes        |
| `@agent`     | Agent     | Autonomous reasoning or multi-turn decision logic       |
| `@tool`      | Tool      | External API or internal utility logic calls            |
| `@task`      | Task      | Logical sub-tasks (e.g., formatting, parsing, routing)  |
| `@embedding` | Embedding | Embedding generation spans                              |
| `@retrieval` | Retrieval | Document search and fetch spans                         |

---

## Decorator Reference

### `@llm(...)`

**Use for:** Any direct LLM call (e.g., GPT, Claude, Gemini).

**Arguments**:

* `model_name` (str, required): Name of the LLM model.
* `name` (str, optional): Override default span name.
* `model_provider` (str, optional): Provider name (`openai`, `anthropic`, etc.).
* `session_id` (str, optional): Shared session identifier.
* `ml_app` (str, optional): Logical app name for grouping spans.

---

### `@workflow(...)`

**Use for:** Multi-step conversation flows or pipelines.

**Arguments**:

* `name` (str, optional): Name of the workflow span.
* `session_id` (str, optional)
* `ml_app` (str, optional)

---

### `@agent(...)`

**Use for:** Agent reasoning or autonomous logic.

**Arguments**:

* `name` (str, optional)
* `session_id` (str, optional)
* `ml_app` (str, optional)

---

### `@tool(...)`

**Use for:** External API or utility functions used by an agent or workflow.

**Arguments**:

* `name` (str, optional)
* `session_id` (str, optional)
* `ml_app` (str, optional)

---

### `@task(...)`

**Use for:** Logical sub-units of a pipeline (e.g., formatting, splitting, scoring).

**Arguments**:

* `name` (str, optional)
* `session_id` (str, optional)
* `ml_app` (str, optional)

---

### `@embedding(...)`

**Use for:** Embedding generation (from text to vector).

**Arguments**:

* `model_name` (str, required)
* `name` (str, optional)
* `model_provider` (str, optional)
* `session_id` (str, optional)
* `ml_app` (str, optional)

---

### `@retrieval(...)`

**Use for:** Document search, similarity lookup, or knowledge base fetches.

**Arguments**:

* `name` (str, optional)
* `session_id` (str, optional)
* `ml_app` (str, optional)

---

## Additional Span Metadata

In any span (decorated or contextual), use:

```python
LLMObs.annotate(
    input_data={...},
    output_data={...},
    metadata={...},
    tags={...},
    metrics={...}
)
```

To enrich spans with relevant payloads, tags, or metrics. This enhances trace detail and helps power LLM dashboards and analytics.