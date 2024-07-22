import streamlit as st
import os
import time
import re
import json
from utils import get_outputs_processed as get_text_from_pdf
from groq import Groq


# streamlit run app_v4.py --server.enableXsrfProtection false



global messages
messages = [
        {"role": "system", "content": "You are a chatbot that answers only based on the context provided and nothing else."},
]

def process_file(doc_content, model_name="mixtral-8x7b-32768"):
    
    client = Groq(
        api_key=st.secrets["GROQ_API_KEY"],
    )
    
    prompt = '''Here is a document, give me all the personal information of any individuals mentioned, such as name, contact number, email, address, etc. from the documents as strings in a JSON. 

    Give me the exact string matches for each field. DONOT format them, give the text matches as it is. 

    The JSON Schema is as follows :- 

    {
        "persons": [{
            "name": .... ,
            "contact_number": .... ,
            "email": ..... , 
            "address": ..... ,
            "dob": .....
        }, ....
        ]
    }

    Give me ONLY the JSON output and nothing else
    Document :- ''' + doc_content

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={ "type": "json_object"}
    )

    individual_entities = json.loads(response.choices[0].message.content)

    sensitive_info = []
    for comp in individual_entities["persons"]:
        for k in comp:
            if (comp[k] is not None) and (comp[k] != ""):
                temp_info = comp[k].split(",")
                for t in temp_info:
                    sensitive_info.append(t.strip())

    pattern = re.compile(r'\b(' + '|'.join(re.escape(word) for word in sensitive_info) + r')\b', re.IGNORECASE)
    cleaned_text = pattern.sub('##########', doc_content)

    return cleaned_text    

def chat_with_openai(doc_content, question):

    client = Groq(
        api_key=st.secrets["GROQ_API_KEY"],
    )

    if len(messages) == 1:
        messages.append({"role": "user", "content": f"Here is the document content :- {doc_content}\nAnswer the questions based on the context given only. Do not respond for any other question rather than ones about this document."})

    messages.append({"role": "user", "content": question})
    
    response = client.chat.completions.create(model="mixtral-8x7b-32768", messages=messages, temperature=0)

    messages.append({"role":"assistant", "content":response})
    # print(response.choices[0])
    return response.choices[0].message.content

st.title("Puchase Documents Q&A Chatbot")



global prev_doc, selected_doc


uploaded_file = st.file_uploader('Choose your pdf file', type="pdf")

# st.write(uploaded_file)

if uploaded_file:

    doc_name = uploaded_file.name


    if "docs" not in st.session_state:
        st.session_state["docs"] = {}

    if "docs" not in st.session_state:
        st.session_state["docs"] = {}



    tab2, tab1 = st.tabs(["Without PII" , "With PII"])

    # Without PII
    with tab2:

        if doc_name not in st.session_state["docs"]:

            st.session_state["docs"][doc_name] = [None, None]

            with st.spinner('Getting the text content from the document ...'):

                doc_content = get_text_from_pdf(uploaded_file.read())

                st.session_state["docs"][doc_name][0] = doc_content

            doc_content_clean = ""
            with st.spinner('PII is being erased from the document ...'):
                # time.sleep(5)

                
                doc_content_clean = process_file(doc_content, model_name="mixtral-8x7b-32768")
                st.success('PII erased from the doc')

                st.session_state["docs"][doc_name][1] = [doc_content_clean]

        else:
            st.success('PII erased from the doc')

            doc_content_clean = st.session_state["docs"][doc_name][1]


        st.text_area("Document Content", doc_content_clean, height=300,  key = "5")
        

        question = st.text_input("Ask a question about the document", key="3")

        if st.button("Get Answer", key="4"):
            if question:
                answer = chat_with_openai(doc_content_clean, question)
                st.write("**Question:**", question)
                st.write("**Answer:**", answer)
            else:
                st.write("Please enter a question.")



    # With PII
    with tab1:

        if doc_name not in st.session_state["docs"]:

            st.session_state["docs"][doc_name] = [None, None]

            with st.spinner('Getting the text content from the document ...'):

                doc_content = get_text_from_pdf(uploaded_file.read())

                st.session_state["docs"][doc_name][0] = doc_content

        
        else:

            doc_content = st.session_state["docs"][doc_name][0]


        st.text_area("Document Content", doc_content, height=300, key = "6")
        

        question = st.text_input("Ask a question about the document", key="1")

        if st.button("Get Answer", key="2"):
            if question:
                answer = chat_with_openai(doc_content, question)
                st.write("**Question:**", question)
                st.write("**Answer:**", answer)
            else:
                st.write("Please enter a question.")

