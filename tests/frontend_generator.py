import asyncio
from playwright.async_api import async_playwright
import random

APP_URL = "http://localhost:8001" 

SCENARIOS = [
    "Hi there!",
    "i am 22 i have dry skin and my concern is acne",
    "What is the best moisturizer for oily skin?",
    "Give me a 5 step routine for sensitive skin"
]

async def run_user_session(browser, user_id):
    context = await browser.new_context()
    page = await context.new_page()
    
    print(f"User {user_id}: Opening Wabi-Sabi...")
    try:
        await page.goto(APP_URL, wait_until="networkidle")
        
   
        landing_input = page.get_by_placeholder("Type something...")
        await landing_input.wait_for(state="visible")
        await landing_input.fill("Hello Wabi-Sabi!")
        
        start_btn = page.get_by_role("button", name="Start chat")
        await start_btn.click(force=True)
        print(f"User {user_id}: Entered Chatroom")

        
        for i in range(0,3):

            chat_input = page.get_by_placeholder("Ask the AI") 
            
            await chat_input.wait_for(state="visible", timeout=5000)
            
            message = SCENARIOS[i]
            print(f"User {user_id} message {i+1}: {message}")
            
            await chat_input.fill(message)
            await page.keyboard.press("Enter")
            
            await asyncio.sleep(random.uniform(4, 7)) 

        print(f"User {user_id}: Session complete.")
    except Exception as e:
        print(f"User {user_id} encountered an issue: {str(e)[:100]}...")
    finally:
        await context.close()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        print("Starting Frontend Traffic Generator...")
        tasks = []
        for i in range(5): 
            tasks.append(run_user_session(browser, i))
        
        await asyncio.gather(*tasks)
        await browser.close()
        print("All frontend sessions finished.")

if __name__ == "__main__":
    asyncio.run(main())