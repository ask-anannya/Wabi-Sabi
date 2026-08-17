from datadog_agent import datadog_agent

class APIMetrics:
    def __init__(self):
        self.datadog_statsd = datadog_agent

    def tracked_request(self):
        return self.datadog_statsd.timed("api.request.latency")
    
    def send_metric(self,metric_name: str, value: int):
      self.datadog_statsd.gauge("api.metrics." + metric_name, value)

api_metrics = APIMetrics()