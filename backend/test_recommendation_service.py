import unittest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
from app.models.schemas import MetricTimeSeriesPoint, Cluster
from app.services.recommendation_service import (
    parse_cpu_cores,
    parse_memory_mb,
    format_cpu_cores,
    format_memory_mb,
    calculate_percentile,
    RecommendationService
)


class TestRecommendationServicePhase1And2(unittest.TestCase):
    # -----------------------------------------------------------------------
    # Phase 1 Regression Tests
    # -----------------------------------------------------------------------
    def test_parse_cpu_cores(self):
        self.assertAlmostEqual(parse_cpu_cores("500m"), 0.5)
        self.assertAlmostEqual(parse_cpu_cores("100m"), 0.1)
        self.assertAlmostEqual(parse_cpu_cores("1.5 Cores"), 1.5)
        self.assertAlmostEqual(parse_cpu_cores("2 Cores"), 2.0)
        self.assertAlmostEqual(parse_cpu_cores(1.0), 1.0)
        self.assertAlmostEqual(parse_cpu_cores("1000000u"), 1.0)
        self.assertAlmostEqual(parse_cpu_cores("1000000000n"), 1.0)
        self.assertAlmostEqual(parse_cpu_cores(""), 0.1)

    def test_parse_memory_mb(self):
        self.assertAlmostEqual(parse_memory_mb("512 MB"), 512.0)
        self.assertAlmostEqual(parse_memory_mb("512Mi"), 512.0)
        self.assertAlmostEqual(parse_memory_mb("1 Gi"), 1024.0)
        self.assertAlmostEqual(parse_memory_mb("2.0 GB"), 2048.0)
        self.assertAlmostEqual(parse_memory_mb("1024Ki"), 1.0)

    def test_format_cpu_and_memory(self):
        self.assertEqual(format_cpu_cores(0.5), "500m")
        self.assertEqual(format_cpu_cores(0.05), "50m")
        self.assertEqual(format_cpu_cores(1.5), "1.50 Cores")
        self.assertEqual(format_memory_mb(512), "512 MB")
        self.assertEqual(format_memory_mb(2048), "2.0 GB")

    def test_calculate_percentile_interpolation(self):
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        self.assertAlmostEqual(calculate_percentile(values, 0.50), 30.0)
        self.assertAlmostEqual(calculate_percentile(values, 0.0), 10.0)
        self.assertAlmostEqual(calculate_percentile(values, 1.0), 50.0)
        self.assertAlmostEqual(calculate_percentile(values, 0.90), 46.0)

    def test_validate_metrics_insufficient_samples(self):
        is_valid, msg, hours, cpu, mem = RecommendationService.validate_metrics([])
        self.assertFalse(is_valid)
        self.assertIn("Insufficient observations", msg)

    def test_validate_metrics_corrupted_value_never_zeroed(self):
        now = datetime.now(timezone.utc)
        samples = [
            MetricTimeSeriesPoint(
                timestamp=now.isoformat(),
                cpuUsage=float('nan'),
                cpuRequest=1.0,
                cpuLimit=2.0,
                memoryUsageMb=512.0,
                memoryLimitMb=1024.0
            ),
            MetricTimeSeriesPoint(
                timestamp=(now + timedelta(hours=1)).isoformat(),
                cpuUsage=0.5,
                cpuRequest=1.0,
                cpuLimit=2.0,
                memoryUsageMb=512.0,
                memoryLimitMb=1024.0
            )
        ]
        is_valid, msg, hours, cpu, mem = RecommendationService.validate_metrics(samples)
        self.assertFalse(is_valid)
        self.assertIn("Invalid or missing CPU usage metric", msg)
        self.assertEqual(len(cpu), 0)

    def test_classification_logic(self):
        cls_over = RecommendationService.classify_provisioning(
            current_cpu_request=2.0,
            target_cpu_request=0.5,
            current_mem_request=2048.0,
            target_mem_request=512.0,
            oom_kills=0,
            throttling_count=0
        )
        self.assertEqual(cls_over, "OVERPROVISIONED")

        cls_under = RecommendationService.classify_provisioning(
            current_cpu_request=0.5,
            target_cpu_request=1.2,
            current_mem_request=512.0,
            target_mem_request=1024.0,
            oom_kills=0,
            throttling_count=0
        )
        self.assertEqual(cls_under, "UNDERPROVISIONED")

    # -----------------------------------------------------------------------
    # Phase 2: Task 6 Specific Safety & Autoscaler Tests
    # -----------------------------------------------------------------------

    def test_1_hpa_detected_for_deployment(self):
        """1. HPA detected for a Deployment."""
        mock_api = MagicMock()
        mock_hpa = MagicMock()
        mock_hpa.metadata.name = "frontend-hpa"
        mock_hpa.spec.scale_target_ref.name = "frontend-app"
        mock_hpa.spec.scale_target_ref.kind = "Deployment"
        mock_hpa.spec.min_replicas = 2
        mock_hpa.spec.max_replicas = 10
        mock_hpa.status.current_replicas = 3
        mock_hpa.status.desired_replicas = 3
        
        # Metric spec with CPU target
        mock_metric = MagicMock()
        mock_metric.type = "Resource"
        mock_metric.resource.name = "cpu"
        mock_metric.resource.target.average_utilization = 75
        mock_hpa.spec.metrics = [mock_metric]
        
        mock_api.list_namespaced_horizontal_pod_autoscaler.return_value.items = [mock_hpa]

        result = RecommendationService.detect_hpa(
            cluster=None,
            namespace="production",
            workload_name="frontend-app",
            workload_type="Deployment",
            client_override=mock_api
        )

        self.assertEqual(result["status"], "DETECTED")
        self.assertEqual(result["hpaName"], "frontend-hpa")
        self.assertEqual(result["minReplicas"], 2)
        self.assertEqual(result["maxReplicas"], 10)
        self.assertEqual(result["cpuTargetPercent"], 75)

    def test_2_hpa_not_detected_after_successful_api_query(self):
        """2. HPA not detected after successful API query."""
        mock_api = MagicMock()
        mock_hpa = MagicMock()
        mock_hpa.spec.scale_target_ref.name = "other-service"
        mock_hpa.spec.scale_target_ref.kind = "Deployment"
        mock_api.list_namespaced_horizontal_pod_autoscaler.return_value.items = [mock_hpa]

        result = RecommendationService.detect_hpa(
            cluster=None,
            namespace="production",
            workload_name="frontend-app",
            workload_type="Deployment",
            client_override=mock_api
        )

        self.assertEqual(result["status"], "NOT_DETECTED")

    def test_3_hpa_detection_unavailable_because_of_api_failure(self):
        """3. HPA detection unavailable because of API failure."""
        mock_api = MagicMock()
        mock_api.list_namespaced_horizontal_pod_autoscaler.side_effect = RuntimeError("Connection timeout to Kube API")

        result = RecommendationService.detect_hpa(
            cluster=None,
            namespace="production",
            workload_name="frontend-app",
            workload_type="Deployment",
            client_override=mock_api
        )

        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertIn("Connection timeout", result["reason"])

    def test_4_hpa_cpu_and_mem_utilization_target_affects_safety_warnings(self):
        """4. HPA CPU and memory utilization target affects safety warnings."""
        hpa_info = {
            "status": "DETECTED",
            "hpaName": "orders-hpa",
            "cpuTargetPercent": 80,
            "memoryTargetPercent": 70,
            "minReplicas": 2,
            "maxReplicas": 8
        }
        vpa_info = {"status": "NOT_DETECTED"}

        status, warnings, blocked, review = RecommendationService.evaluate_safety_rules(hpa_info, vpa_info)

        self.assertEqual(status, "WARNING")
        self.assertTrue(review)
        self.assertEqual(len(blocked), 0)
        # Check warnings explain changing requests alters scaling baseline
        cpu_warning = any("target CPU utilization of 80%" in w for w in warnings)
        mem_warning = any("target Memory utilization of 70%" in w for w in warnings)
        self.assertTrue(cpu_warning)
        self.assertTrue(mem_warning)

    def test_5_vpa_detected_and_matched_correctly(self):
        """5. VPA detected and matched correctly."""
        mock_custom_api = MagicMock()
        mock_custom_api.list_namespaced_custom_object.return_value = {
            "items": [
                {
                    "metadata": {"name": "payment-vpa"},
                    "spec": {
                        "targetRef": {"name": "payment-service", "kind": "Deployment"},
                        "updatePolicy": {"updateMode": "Off"}
                    },
                    "status": {
                        "recommendation": {
                            "containerRecommendations": [
                                {
                                    "containerName": "payment-container",
                                    "target": {"cpu": "250m", "memory": "512Mi"}
                                }
                            ]
                        }
                    }
                }
            ]
        }

        result = RecommendationService.detect_vpa(
            cluster=None,
            namespace="production",
            workload_name="payment-service",
            workload_type="Deployment",
            client_override=mock_custom_api
        )

        self.assertEqual(result["status"], "DETECTED")
        self.assertEqual(result["vpaName"], "payment-vpa")
        self.assertEqual(result["updateMode"], "Off")
        self.assertEqual(result["cpuRecommendation"], "250m")
        self.assertEqual(result["memoryRecommendation"], "512Mi")

    def test_6_vpa_crd_unavailable(self):
        """6. VPA CRD unavailable."""
        mock_custom_api = MagicMock()
        mock_custom_api.list_namespaced_custom_object.side_effect = Exception("404 Not Found: the server could not find the requested resource")

        result = RecommendationService.detect_vpa(
            cluster=None,
            namespace="production",
            workload_name="payment-service",
            workload_type="Deployment",
            client_override=mock_custom_api
        )

        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertIn("CRD is unavailable", result["reason"])

    def test_7_vpa_actively_controlling_requests_blocks_conflicting_recommendations(self):
        """7. VPA actively controlling requests blocks conflicting recommendations."""
        hpa_info = {"status": "NOT_DETECTED"}
        vpa_info = {
            "status": "DETECTED",
            "vpaName": "active-vpa",
            "updateMode": "Auto",
            "cpuRecommendation": "500m"
        }

        status, warnings, blocked, review = RecommendationService.evaluate_safety_rules(hpa_info, vpa_info)

        self.assertEqual(status, "BLOCKED")
        self.assertTrue(review)
        self.assertTrue(any("active VPA 'active-vpa' with updateMode='Auto'" in b for b in blocked))

    def test_8_autoscaler_information_unavailable_results_in_unknown_safety(self):
        """8. Autoscaler information unavailable results in UNKNOWN safety."""
        hpa_info = {"status": "UNAVAILABLE", "reason": "Kube API server 503"}
        vpa_info = {"status": "NOT_DETECTED"}

        status, warnings, blocked, review = RecommendationService.evaluate_safety_rules(hpa_info, vpa_info)

        self.assertEqual(status, "UNKNOWN")
        self.assertTrue(review)
        self.assertTrue(any("Autoscaler status could not be verified" in w for w in warnings))

    def test_9_workload_without_autoscalers_receives_appropriate_safety_status(self):
        """9. Workload without autoscalers receives appropriate safety status."""
        hpa_info = {"status": "NOT_DETECTED"}
        vpa_info = {"status": "NOT_DETECTED"}

        status, warnings, blocked, review = RecommendationService.evaluate_safety_rules(hpa_info, vpa_info)

        self.assertEqual(status, "SAFE")
        self.assertFalse(review)
        self.assertEqual(len(warnings), 0)
        self.assertEqual(len(blocked), 0)


if __name__ == '__main__':
    unittest.main()
