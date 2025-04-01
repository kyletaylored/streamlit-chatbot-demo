import streamlit as st
from openai import OpenAI
import os
import uuid
from dotenv import load_dotenv
from ddtrace.llmobs import LLMObs
from ddtrace.llmobs.decorators import llm, workflow, task, agent

# Load environment variables from .env file
load_dotenv()

# Initialize Datadog LLM Observability with environment variables
LLMObs.enable(
    ml_app=os.getenv("DD_ML_APP_NAME"),
    api_key=os.getenv("DD_API_KEY"),
    site=os.getenv("DD_SITE", "datadoghq.com"),
    agentless_enabled=True,
    service=os.getenv("DD_SERVICE", "streamlit-chatbot")
)

# Show title and description.
st.title("💬 Chatbot")
st.write(
    "This is a simple chatbot that uses OpenAI's GPT-3.5 model to generate responses. "
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
    "You can also learn how to build this app step by step by [following our tutorial](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)."
)

# Ask user for their OpenAI API key via `st.text_input` or use from environment
default_api_key = os.getenv("OPENAI_API_KEY", "")
openai_api_key = st.text_input("OpenAI API Key", value=default_api_key, type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:
    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    # Create a session state variable to store the chat messages.
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Ensure we have a session ID for tracking
    if "_session_id" not in st.session_state:
        st.session_state._session_id = str(uuid.uuid4())
    
    session_id = st.session_state._session_id
    ml_app_name = os.getenv("DD_ML_APP_NAME")

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Generate a response using the OpenAI API
    @llm(
        model_name="gpt-3.5-turbo",
        model_provider="openai",
        name="generate_chat_completion",
        session_id=session_id,
        ml_app=ml_app_name
    )
    def generate_llm_response(messages):
        """
        Generate a response from OpenAI with Datadog observability.
        """
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True,
        )
        
        # Explicitly annotate the LLM call with input data
        LLMObs.annotate(
            input_data=messages,
            metadata={"model": "gpt-3.5-turbo", "stream": True},
            metrics={"input_messages": len(messages)},
            tags={"interface": "streamlit", "api": "openai"}
        )
        
        return response
    
    # Process user input
    def process_user_input(prompt):
        """
        Process and prepare the user input before sending to the LLM.
        """
        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Prepare messages for the API call
        messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]
        
        return messages
    
    # Handle streaming response
    def handle_response_streaming(stream):
        """
        Stream the assistant's response to the UI.
        """
        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        
        # Store the response
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        return response
    
    # Main chatbot function
    @agent(
        name="streamlit_chatbot",
        session_id=session_id,
        ml_app=ml_app_name
    )
    def run_chatbot():
        # Create a chat input field
        prompt = st.chat_input("What is up?")
        
        if not prompt:
            return None
            
        # Track the conversation with the workflow decorator
        @workflow(
            name="chatbot_conversation",
            session_id=session_id,
            ml_app=ml_app_name
        )
        def handle_conversation(user_prompt):
            # Track the input processing with the task decorator
            @task(
                name="process_input",
                session_id=session_id,
                ml_app=ml_app_name
            )
            def process_input(text):
                processed = process_user_input(text)
                LLMObs.annotate(
                    input_data=text,
                    output_data=processed,
                    metadata={"message_count": len(processed)},
                    tags={"process": "user_input"}
                )
                return processed
            
            # Process the input
            messages = process_input(user_prompt)
            
            # Get model response
            stream = generate_llm_response(messages)
            
            # Stream the response
            response = handle_response_streaming(stream)
            
            # Annotate the workflow with complete conversation
            LLMObs.annotate(
                input_data=user_prompt,
                output_data=response,
                metadata={"turn": len(st.session_state.messages) // 2},
                tags={"workflow": "conversation"}
            )
            
            return response
        
        # Execute the conversation workflow
        final_response = handle_conversation(prompt)
        
        # Annotate the agent with the full interaction
        LLMObs.annotate(
            input_data=prompt,
            output_data=final_response,
            metadata={
                "total_messages": len(st.session_state.messages),
                "conversation_turns": len(st.session_state.messages) // 2
            },
            tags={"agent": "streamlit_chatbot"}
        )
        
        return final_response
    
    # Run the chatbot
    run_chatbot()