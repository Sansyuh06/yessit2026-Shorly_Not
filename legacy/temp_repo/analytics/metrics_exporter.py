"""
Export system metrics for monitoring dashboards (Prometheus/Grafana format).
Useful for showing judges the observability of the system.
"""
from quantum_engine.metrics import quantum_entropy_score

class MetricsExporter:
    def __init__(self, kms):
        self.kms = kms
    
    def prometheus_format(self) -> str:
        """Export metrics in Prometheus exposition format."""
        health = self.kms.check_link_health()
        qber = health.get("qber", 0)
        lines = [
            f'# HELP shorlynot_qber Current Quantum Bit Error Rate',
            f'# TYPE shorlynot_qber gauge',
            f'shorlynot_qber {qber}',
            f'',
            f'# HELP shorlynot_escalation_level Current escalation level (0-4)',
            f'# TYPE shorlynot_escalation_level gauge',
            f'shorlynot_escalation_level {self.kms.escalation_level}',
            f'',
            f'# HELP shorlynot_sessions_total Total sessions created',
            f'# TYPE shorlynot_sessions_total counter',
            f'shorlynot_sessions_total {len(self.kms.sessions)}',
            f'',
            f'# HELP shorlynot_attacks_detected Total attacks detected',
            f'# TYPE shorlynot_attacks_detected counter',
            f'shorlynot_attacks_detected {self.kms.attacks_detected}',
            f'',
            f'# HELP shorlynot_entropy_score Composite security score (0-100)',
            f'# TYPE shorlynot_entropy_score gauge',
            f'shorlynot_entropy_score {quantum_entropy_score(qber, 256, 128, self.kms.attacks_detected)}',
        ]
        return '\\n'.join(lines)
