
import streamlit as st
from openai import OpenAI
import os
import uuid
from dotenv import load_dotenv
from ddtrace.llmobs import LLMObs
from ddtrace.llmobs.decorators import llm, workflow, task, agent, tool, retrieval, embedding

# Load environment variables
load_dotenv()

EVAL_CATEGORIES = [
    "Toxicity",
    "Prompt Injection",
    "Positive Sentiment",
    "Negative Sentiment",
    "Off-Topic",
    "On-Topic",
    "Data Leakage"
]

ML_APP_NAME = os.getenv("DD_ML_APP_NAME", "Streamlit Demo App")

LLMObs.enable(
    ml_app=ML_APP_NAME,
    api_key=os.getenv("DD_API_KEY"),
    site=os.getenv("DD_SITE", "datadoghq.com"),
    agentless_enabled=True,
    service=os.getenv("DD_SERVICE", "streamlit-chatbot")
)

st.title("Chatbot Demo with LLM Observability")
st.write("This chatbot uses OpenAI's GPT-3.5 and is instrumented with Datadog LLM Observability to trace evaluations such as toxicity, prompt injection, sentiment, and more.")

# OpenAI API key
default_api_key = os.getenv("OPENAI_API_KEY", "")
openai_api_key = st.text_input("OpenAI API Key", value=default_api_key, type="password")
if not openai_api_key:
    st.info("Please provide your OpenAI API key to continue.")
    st.stop()

client = OpenAI(api_key=openai_api_key)

# Session setup
if "messages" not in st.session_state:
    st.session_state.messages = []
if "_session_id" not in st.session_state:
    st.session_state._session_id = str(uuid.uuid4())

session_id = st.session_state._session_id

# Display history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Prompt form
with st.form("prompt_form"):
    st.markdown("Prompt Evaluation Form")
    selected_eval = st.selectbox("Choose a test category:", EVAL_CATEGORIES, index=0, key="eval_type")
    custom_prompt = st.text_area("Or enter a custom prompt:", placeholder="Write your own prompt here...", key="prompt_text")
    submitted = st.form_submit_button("Send Prompt")

prompt = None
selected_eval = st.session_state.get("eval_type", EVAL_CATEGORIES[0])

@llm(name="generate_eval_prompt", model_name="gpt-3.5-turbo", model_provider="openai")
def generate_eval_prompt(category):
    query = f"Give me an example of a prompt that would be used to test {category.lower()} in an LLM."
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": query}]
    )
    return response.choices[0].message.content.strip()

if submitted:
    prompt = custom_prompt.strip() if custom_prompt.strip() else generate_eval_prompt(selected_eval)
    st.markdown(f"Prompt in use: `{prompt}`")

    def log_user_input(text: str):
        return f"User input length: {len(text)}"

    log_metadata = log_user_input(prompt)
    LLMObs.annotate(input_data=prompt, metadata={"log_tool_output": log_metadata})

    @agent()
    def run_chatbot(prompt):
        @workflow(name="chatbot_conversation")
        def handle_conversation(user_prompt):
            @retrieval(name="retrieve_context")
            def retrieve_context(prompt: str):
                return [{"title": "Example Doc", "content": "This is background info."}]

            @embedding(model_name="mock-embedder")
            def embed_prompt(prompt: str):
                return [float(len(prompt))] * 384

            @task(name="process_input")
            def process_input(text):
                if not any(m["content"] == text and m["role"] == "user" for m in st.session_state.messages):
                    st.session_state.messages.append({"role": "user", "content": text})
                with st.chat_message("user"):
                    st.markdown(text)
                return [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

            messages = process_input(user_prompt)
            embed_vector = embed_prompt(user_prompt)
            LLMObs.annotate(metadata={"embedding_vector_norm": sum(embed_vector)})
            docs = retrieve_context(user_prompt)
            LLMObs.annotate(metadata={"retrieved_docs": len(docs)})

            @llm(model_name="gpt-3.5-turbo", model_provider="openai", name="generate_chat_completion")
            def generate_llm_response(messages):
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    stream=True
                )
                
                LLMObs.annotate(
                    input_data=user_prompt,
                    metadata={"model": "gpt-3.5-turbo", "stream": True},
                    metrics={"input_messages": len(messages)},
                    tags={"interface": "streamlit", "api": "openai"}
                )
                return response

            stream = generate_llm_response(messages)

            with st.chat_message("assistant"):
                response_text = st.write_stream(stream)

            if not any(m["content"] == response_text and m["role"] == "assistant" for m in st.session_state.messages):
                st.session_state.messages.append({"role": "assistant", "content": response_text})

            LLMObs.annotate(
                input_data=user_prompt,
                output_data=response_text,
                metadata={"turn": len(st.session_state.messages) // 2},
                tags={"workflow": "conversation"}
            )
            return response_text

        return handle_conversation(prompt)

    LLMObs.annotate(tags={"eval_type": selected_eval})
    final_response = run_chatbot(prompt)
    LLMObs.annotate(
        input_data=prompt,
        output_data=final_response,
        metadata={
            "total_messages": len(st.session_state.messages),
            "conversation_turns": len(st.session_state.messages) // 2
        },
        tags={"agent": "streamlit_chatbot"}
    )
