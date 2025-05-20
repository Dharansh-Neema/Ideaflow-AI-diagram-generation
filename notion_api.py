import requests
import json
from typing import Dict, Any, Optional, List, Union
import os
from dotenv import load_dotenv

load_dotenv()

def extract_notion_page_content(notion_api_token: str, page_id: str) -> Dict[Any, Any]:
    """
    Extract content from a Notion page using the Notion API.
    
    Args:
        notion_api_token (str): The Notion API integration token
        page_id (str): The ID of the Notion page to extract content from
                      (can be found in the URL: notion.so/[workspace]/[page_id])
    
    Returns:
        Dict[Any, Any]: Dictionary containing the page content
    """
    # Ensure page_id is properly formatted (remove any hyphens or URL components)
    page_id = page_id.replace("-", "")
    if "/" in page_id:
        page_id = page_id.split("/")[-1]
    
    # Set up the request headers with authorization
    headers = {
        "Authorization": f"Bearer {notion_api_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"  # Use the latest Notion API version
    }
    
    # API endpoint for retrieving a page
    url = f"https://api.notion.com/v1/pages/{page_id}"
    
    try:
        # Make the request to get the page
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the JSON response
        page_data = response.json()
        
        # Get page blocks (content)
        blocks_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        blocks_response = requests.get(blocks_url, headers=headers)
        blocks_response.raise_for_status()
        
        # Combine page data with its content blocks
        page_data["blocks"] = blocks_response.json().get("results", [])
        
        return page_data
    
    except requests.exceptions.RequestException as e:
        print(f"Error making request to Notion API: {e}")
        return {"error": str(e)}
    except json.JSONDecodeError:
        print("Error decoding JSON response")
        return {"error": "Invalid JSON response"}


def get_block_content_recursive(notion_api_token: str, block_id: str) -> List[Dict[Any, Any]]:
    """
    Recursively get all nested block content from a Notion block.
    
    Args:
        notion_api_token (str): The Notion API integration token
        block_id (str): The ID of the block to retrieve children from
    
    Returns:
        List[Dict[Any, Any]]: List of block content including nested children
    """
    headers = {
        "Authorization": f"Bearer {notion_api_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        blocks = response.json().get("results", [])
        
        # Process each block to get its children if it has them
        for block in blocks:
            if block.get("has_children", False):
                children = get_block_content_recursive(notion_api_token, block["id"])
                block["children"] = children
        
        return blocks
    except Exception as e:
        print(f"Error retrieving nested blocks: {e}")
        return []


def extract_notion_page_with_content(notion_api_token: str, page_id: str) -> Dict[Any, Any]:
    """
    Extract a Notion page with all of its content, including nested blocks.
    
    Args:
        notion_api_token (str): The Notion API integration token
        page_id (str): The ID of the Notion page
    
    Returns:
        Dict[Any, Any]: Dictionary containing the page properties and all content
    """
    # Get the page metadata
    page_data = extract_notion_page_content(notion_api_token, page_id)
    
    # If there was an error getting the page, return early
    if "error" in page_data:
        return page_data
    
    # Get all blocks with recursive content
    blocks_with_content = get_block_content_recursive(notion_api_token, page_id)
    page_data["blocks_with_children"] = blocks_with_content
    
    return page_data


def extract_readable_content(notion_data: Dict[Any, Any]) -> Dict[str, Union[str, List[str]]]:
    """
    Convert the raw Notion API response into a more readable format.
    
    Args:
        notion_data (Dict[Any, Any]): The raw Notion API response
        
    Returns:
        Dict[str, Union[str, List[str]]]: Dictionary with readable content
    """
    result = {
        "title": "",
        "properties": {},
        "content": []
    }
    
    # Extract title if available
    if "properties" in notion_data and "title" in notion_data["properties"]:
        title_items = notion_data["properties"]["title"].get("title", [])
        title_parts = [item.get("plain_text", "") for item in title_items]
        result["title"] = "".join(title_parts)
    
    # Extract other properties
    if "properties" in notion_data:
        for prop_name, prop_data in notion_data["properties"].items():
            if prop_name == "title":
                continue
                
            prop_type = prop_data.get("type", "")
            if prop_type == "rich_text":
                text_items = prop_data.get("rich_text", [])
                text_parts = [item.get("plain_text", "") for item in text_items]
                result["properties"][prop_name] = "".join(text_parts)
            elif prop_type == "select":
                if prop_data.get("select"):
                    result["properties"][prop_name] = prop_data["select"].get("name", "")
            # Add other property types as needed
    
    # Process blocks to extract text content
    blocks = notion_data.get("blocks_with_children", notion_data.get("blocks", []))
    
    for block in blocks:
        block_type = block.get("type", "")
        if block_type == "paragraph":
            paragraph_text = extract_text_from_rich_text(block.get("paragraph", {}).get("rich_text", []))
            if paragraph_text:
                result["content"].append(paragraph_text)
        elif block_type == "heading_1":
            heading_text = extract_text_from_rich_text(block.get("heading_1", {}).get("rich_text", []))
            if heading_text:
                result["content"].append(f"# {heading_text}")
        elif block_type == "heading_2":
            heading_text = extract_text_from_rich_text(block.get("heading_2", {}).get("rich_text", []))
            if heading_text:
                result["content"].append(f"## {heading_text}")
        elif block_type == "heading_3":
            heading_text = extract_text_from_rich_text(block.get("heading_3", {}).get("rich_text", []))
            if heading_text:
                result["content"].append(f"### {heading_text}")
        elif block_type == "bulleted_list_item":
            bullet_text = extract_text_from_rich_text(block.get("bulleted_list_item", {}).get("rich_text", []))
            if bullet_text:
                result["content"].append(f"• {bullet_text}")
        elif block_type == "numbered_list_item":
            number_text = extract_text_from_rich_text(block.get("numbered_list_item", {}).get("rich_text", []))
            if number_text:
                result["content"].append(f"1. {number_text}")  # Simplified, won't have proper numbering
        elif block_type == "code":
            code_text = extract_text_from_rich_text(block.get("code", {}).get("rich_text", []))
            language = block.get("code", {}).get("language", "")
            if code_text:
                result["content"].append(f"```{language}\n{code_text}\n```")
        
        # Process children recursively if present
        if "children" in block and block["children"]:
            for child in block["children"]:
                child_result = extract_readable_content({"blocks": [child]})
                result["content"].extend(child_result.get("content", []))
    
    return result


def extract_text_from_rich_text(rich_text_list: List[Dict[Any, Any]]) -> str:
    """
    Extract plain text from Notion's rich_text format.
    
    Args:
        rich_text_list (List[Dict[Any, Any]]): List of rich text objects
        
    Returns:
        str: Extracted plain text
    """
    text_parts = []
    for text_item in rich_text_list:
        if "plain_text" in text_item:
            text_parts.append(text_item["plain_text"])
    return "".join(text_parts)


# Example usage:
if __name__ == "__main__":
    # Replace with your actual token and page ID
    api_token = os.getenv("NOTION_API")
    page_id = "1f8e4db1914180329177d006eb1a8595"
    # Get page with all content
    page_data = extract_notion_page_with_content(api_token, page_id)
    
    # Convert to readable format
    readable_content = extract_readable_content(page_data)
    
    # print(f"Title: {readable_content['title']}")
    # print("\nContent:")
    # for content_item in readable_content['content']:
    #     print(content_item)
    print(readable_content)
