import streamlit as st
import streamlit as st
import os
from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_community.document_loaders import PyPDFLoader
from system_prompt import SYSTEM_PROMPT
import tempfile
import base64

if "OPENROUTER_API_KEY" in st.secrets:
    OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
else:
    from dotenv import load_dotenv
    load_dotenv()
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    st.error("OpenRouter API Key not found!")
    st.stop()

llm = ChatOpenRouter(
    model="openai/gpt-3.5-turbo",
    temperature=0.3,
    api_key = OPENROUTER_API_KEY,

)
# 1️⃣ Add background image first
with open("background.jpg", "rb") as f:
    encoded_image = base64.b64encode(f.read()).decode()

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded_image}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    </style>
    """,
    unsafe_allow_html=True
)


st.title("🎓 AI Teacher Bot")
st.success("👋 Welcome! Ask your doubts in Physics, Chemistry, or Mathematics.")

#Upload PDF/image
uploaded_file = st.file_uploader(
    "Upload PDF or Image (Optional)",
    type=["pdf", "png", "jpg", "jpeg"]
)
pdf_text = ""
image_data = ""
if uploaded_file is not None:

    file_type = uploaded_file.type

    #If PDF
    if file_type == "application/pdf":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        loader = PyPDFLoader(tmp_path)
        documents = loader.load()

        pdf_text = "\n".join([doc.page_content for doc in documents])

        st.success("✅ PDF uploaded and processed!")

    #If Image
    elif file_type.startswith("image/"):
        image_data = uploaded_file.read()
        st.session_state.uploaded_image = image_data
        st.success("✅ Image uploaded successfully!")
   

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# Display previous messages
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Ask your JEE question...")

if user_input:

    langchain_messages = []


    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )


    with st.chat_message("user"):
        col1, col2 = st.columns([1, 6])

        if "uploaded_image" in st.session_state:
            with col1:
                st.image(st.session_state.uploaded_image, width=60)

        with col2:
            st.markdown(user_input)


    for msg in st.session_state.messages[:-1]:
        if msg["role"] == "system":
            langchain_messages.append(SystemMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))
        elif msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))

    if image_data:
        base64_image = base64.b64encode(image_data).decode("utf-8")

        langchain_messages.append(
            HumanMessage(
                content=[
                    {"type": "text", "text": user_input},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ]
            )
        )

    elif pdf_text:
        langchain_messages.append(
            HumanMessage(
                content=f"""
                Use this study material if needed:
                {pdf_text}

                Question:
                {user_input}
                """
            )
        )

    else:
        langchain_messages.append(HumanMessage(content=user_input))

    #  Get response
    response = llm.invoke(langchain_messages)

    with st.chat_message("assistant"):
        st.markdown(response.content)

    st.session_state.messages.append(
        {"role": "assistant", "content": response.content}
    )