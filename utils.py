import os
from dotenv import load_dotenv
load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI
from prompts import mermaid_prompt
from notion_api import extract_notion_page_with_content, extract_readable_content

def convert_data_into_mermaid_code(data):
    """
        This function converts the data into mermaid code.Using LLM.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        api_key=os.getenv('GOOGLE_API_KEY')
    )
    
    prompt = mermaid_prompt.format(content=data)
    response = llm.invoke(prompt)
    return response.content


def initiate_flow(title):
    print("Initiating flow")
    page_id = "1f8e4db1914180329177d006eb1a8595"
    notion_api_key = os.getenv("NOTION_API")
    #fetch page content
    page_info = extract_notion_page_with_content(notion_api_key, page_id)
    page_content = extract_readable_content(page_info)
    if page_content["title"] == title:
        mermaid_code = convert_data_into_mermaid_code(page_content)
        #code cleanup
        mermaid_code = mermaid_code.replace("```mermaid", "").replace("```", "")
        return mermaid_code
    else :
        return "Page title does not match"

if __name__ == "__main__":
    mermaid_code = initiate_flow("OSI Layer")
    print(mermaid_code)