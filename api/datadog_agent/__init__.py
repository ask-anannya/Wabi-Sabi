import os
from datadog import DogStatsd

def connect_datadog():
    print("Initializing Datadog StatsD client...")
    if not os.getenv("DD_AGENT_HOST") or not os.getenv("DD_PORT"):
       raise EnvironmentError("Datadog environment variables DD_AGENT_HOST and DD_PORT must be set.")
    datadog_statsd = DogStatsd(host=os.getenv("DD_AGENT_HOST"), port=int(os.getenv("DD_PORT")))
    print("Datadog StatsD client initialized.")
    return datadog_statsd

datadog_agent = connect_datadog()