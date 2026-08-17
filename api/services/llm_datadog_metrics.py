from datadog_agent import datadog_agent
from models.hallucination import HallucinationResult

class LLMMetrics:
    def __init__(self):
        self.datadog_statsd = datadog_agent

    def track_request(self):
        return self.datadog_statsd.timed("llm.request.latency")


    def logging_event(self,metric_name, value=1):
        self.datadog_statsd.increment(f"llm.{metric_name}", value)
    
    def log_hallucination(self, hallucination:HallucinationResult):
            print("Logging hallucination metrics to Datadog...")
            self.datadog_statsd.increment("llm.hallucination.score", hallucination.hallucination_score)
            self.datadog_statsd.increment("llm.hallucination.category", hallucination.category)
            self.datadog_statsd.increment("llm.hallucination.reason", hallucination.reason)
            self.datadog_statsd.increment("llm.hallucination.evaluated.count", 1)

            if hallucination.hallucination_score > 0.5:
                self.datadog_statsd.increment("llm.hallucination.flagged.count", 1)
            else:
                self.datadog_statsd.increment("llm.hallucination.clean.count", 1)
            print("Hallucination metrics logged to Datadog.")
    
    def log_prefilter(self, risk_score: float, triggers: list[str]):
        self.datadog_statsd.increment("llm.prefilter.score", risk_score)
        for trigger in triggers:
            self.datadog_statsd.increment(f"llm.prefilter.trigger.{trigger}")
        
    def log_error(self, error_type: str):
        self.datadog_statsd.increment(f"llm.errors.{error_type}")

    # --- scan path (wabi-sabi.* namespace, distinct from the llm.* chat-path names above) ---

    def log_scan_event(self, metric_name: str, value: float = 1):
        self.datadog_statsd.increment(f"wabi-sabi.{metric_name}", value)

    def log_scan_gauge(self, metric_name: str, value: float, tags: list[str] | None = None):
        self.datadog_statsd.gauge(f"wabi-sabi.{metric_name}", value, tags=tags or [])

    def track_scan_latency(self):
        return self.datadog_statsd.timed("wabi-sabi.scan.latency")

    def log_youcam_task(self, latency_ms: float, failed: bool, units_consumed: int = 1):
        self.datadog_statsd.gauge("wabi-sabi.youcam.task.latency", latency_ms)
        self.datadog_statsd.increment("wabi-sabi.youcam.task.units_consumed", units_consumed)
        if failed:
            self.datadog_statsd.increment("wabi-sabi.youcam.task.failures")

    def log_voice_event(self, event: str):
        self.datadog_statsd.increment(f"wabi-sabi.voice.{event}")


llm_metrics = LLMMetrics()