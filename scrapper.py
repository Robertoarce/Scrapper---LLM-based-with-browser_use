from browser_use.llm import ChatGoogle
from browser_use import Agent
from dotenv import load_dotenv
load_dotenv()



import asyncio
import json
import csv
import re
from browser_use import Browser

# Create browser with initial webpage

llm = ChatGoogle(model="gemini-2.5-flash")

prompt = """
go to https://www.leboncoin.fr/recherche?category=9&locations=Paris_75001__48.85717_2.3414_1808_5000
You are a helpful assistant that can help me scrape real estate listings from leboncoin.fr.

I need you to extract the following information from each listing on the page:
- Price (in euros, convert to number without spaces or symbols)
- Surface area in m² (convert to number)
- District (Paris arrondissement number, from 1-20)

For example, if you see:
'Prix: 695 000 €
14 787 € / m²
Appartement · 2 pièces · 47m²
Paris 75007 Saint-Thomas d'Aquin'

Extract: price=695000, m2=47, district=7

Your output should be ONLY a JSON array of objects with "price", "m2", and "district" fields:
[
    {"price": "695000", "m2": "47", "district": "7"},
    {"price": "450000", "m2": "35", "district": "11"}
]

Rules:
- Only include listings that have ALL three fields (price, m2, district)
- District must be between 1-20 (Paris arrondissements)
- Convert prices to numbers (remove € symbols, spaces, and commas)
- Convert m² to numbers
- Return ONLY the JSON array, no other text
- Scroll through the page to get more listings if possible
"""
  
 

async def main():
    try:
        agent = Agent(
            task=prompt,
            llm=llm, 
        )
        
        print("Starting agent...")
        result = await agent.run()
        
        print("Agent Raw Result:", result)
        print("Result type:", type(result))
        print("Final Result:", result.final_result())
        print("Extracted content from Result:", result.extracted_content())
        
        # Handle different result formats
        json_data = None
        
        # If result is a string, try to parse it directly
        if isinstance(result, str):
            # Try to extract JSON from the result
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                json_data = json_match.group(0)
            else:
                json_data = result
        
        # If result is a dict/object, look for common fields
        elif hasattr(result, 'content') or hasattr(result, 'result') or hasattr(result, 'output'):
            # Extract the actual content
            content = getattr(result, 'content', None) or getattr(result, 'result', None) or getattr(result, 'output', None)
            if content:
                json_match = re.search(r'\[.*\]', str(content), re.DOTALL)
                if json_match:
                    json_data = json_match.group(0)
        
        if json_data:
            try:
                listings = json.loads(json_data)
                
                if listings and len(listings) > 0:
                    # Define file names
                    csv_file = "leboncoin_listings.csv"
                    json_file = "leboncoin_listings.json"
                    
                    # Save to JSON file
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(listings, f, ensure_ascii=False, indent=2)
                    
                    # Write to CSV
                    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                        fieldnames = ["price", "m2", "district"]
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        
                        writer.writeheader()
                        for listing in listings:
                            # Validate the listing has all required fields
                            if all(field in listing for field in fieldnames):
                                writer.writerow(listing)
                    
                    print(f"Data successfully saved to {csv_file} and {json_file}")
                    print(f"Found {len(listings)} listings")
                else:
                    print("No listings found in the result")
                    
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                print("Raw JSON data:", json_data)
        else:
            print("Could not extract JSON data from result")
            print("Full result:", result)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())