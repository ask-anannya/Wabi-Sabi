import asyncio
import httpx
import random
import time

API_URL = "http://localhost:8000/api/v1/llm/chat"

SCENARIOS = [
    {"role": "human", "content": "Hi"},
    {"role": "human", "content": "i am 22 i have dry skin and my concern is acne"},
    {"role": "human", "content": "Recommend a 10-step nighttime routine for aging skin with high sensitivity."},
    {"role": "human", "content": "What are the best ingredients for dark spots on oily skin?"}
]

async def send_request(client, mode="normal"):
    payload = {
        "messages": [random.choice(SCENARIOS)]
    }
    print (f"Sending request in '{mode}' mode with payload: {payload}")
    headers = {
        "Content-Type": "application/json",
        "X-Simulation-Mode": mode 
    }

    try:
        start = time.time()
        response = await client.post(API_URL, json=payload, headers=headers, timeout=20.0)
        duration = time.time() - start
        
        status_icon = "good" if response.status_code == 200 else "error"
        print(f"[{mode.upper():12}] Status: {response.status_code} {status_icon} | Latency: {duration:.2f}s")
    except Exception as e:
        print(f"[{mode.upper():12}] Request failed: {e}")

async def main():
    async with httpx.AsyncClient() as client:
        print("Starting Wabi-Sabi Traffic Generator...")
        print("Phase 1: Generating normal healthy traffic...")
        for _ in range(5):
            await send_request(client, mode="normal")
            await asyncio.sleep(1)

        print("\nPhase 2: Triggering 'High Latency' Monitor (Simulation)...")
        await send_request(client, mode="high_latency")

        print("\nPhase 3: Triggering 'Error Rate' SLO (Simulation)...")
        for _ in range(3):
            await send_request(client, mode="error")

        print("\nPhase 4: High Volume burst...")
        tasks = [send_request(client, mode="normal") for _ in range(10)]
        await asyncio.gather(*tasks)

    print("\nTraffic generation complete. Check your Datadog Dashboard!")

if __name__ == "__main__":
    asyncio.run(main())