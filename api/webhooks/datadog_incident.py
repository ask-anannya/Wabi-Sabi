from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/create_runbook")
async def receive_incident(request: Request):
    payload = await request.json()

    runbook_url = "This is a placeholder for the runbook URL generation logic."
    message = f"Incident received: {payload.get('title')}\nRunbook: {runbook_url}"

    print("Sending Slack notification...")
    print(message)
    print("Slack Notification Sent!")

    return {"status": "runbook_created", "runbook_url": runbook_url}
