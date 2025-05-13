# services/comet_service.py - Comet ML integration for tracking
import comet_ml
import os
import logging
from typing import Dict, List, Any
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class CometService:
    def __init__(self):
        self.api_key = os.getenv('COMET_API_KEY')
        self.workspace = os.getenv('COMET_WORKSPACE')
        self.project_name = os.getenv('COMET_PROJECT_NAME', 'research-to-product-pipeline')
        self.experiments = {}
        
    def create_experiment(self, project_id: int, stage: str) -> str:
        """Create a new Comet experiment for tracking a project stage"""
        try:
            experiment = comet_ml.Experiment(
                api_key=self.api_key,
                workspace=self.workspace,
                project_name=self.project_name,
                auto_param_logging=False,
                auto_metric_logging=False
            )
            
            experiment.set_name(f"Project_{project_id}_{stage}")
            experiment.add_tag(f"project_{project_id}")
            experiment.add_tag(stage)
            experiment.add_tag("research-pipeline")
            
            experiment_key = experiment.get_key()
            self.experiments[f"{project_id}_{stage}"] = experiment
            
            logger.info(f"Created Comet experiment {experiment_key} for project {project_id} stage {stage}")
            return experiment_key
            
        except Exception as e:
            logger.error(f"Error creating Comet experiment: {str(e)}")
            return None
    
    def log_research_metrics(self, project_id: int, metrics: Dict) -> bool:
        """Log metrics from the research analysis stage"""
        try:
            experiment_key = f"{project_id}_research"
            
            if experiment_key not in self.experiments:
                self.create_experiment(project_id, "research")
            
            experiment = self.experiments[experiment_key]
            
            # Log research-specific metrics
            experiment.log_metric("papers_indexed", metrics.get("papers_indexed", 0))
            experiment.log_metric("concepts_extracted", metrics.get("concepts_extracted", 0))
            experiment.log_metric("avg_concept_confidence", metrics.get("avg_concept_confidence", 0.0))
            experiment.log_metric("query_response_time", metrics.get("query_response_time", 0.0))
            
            # Log parameters
            experiment.log_parameter("indexing_method", metrics.get("indexing_method", "llamaindex"))
            experiment.log_parameter("embedding_model", metrics.get("embedding_model", "openai"))
            
            # Log research papers as assets
            if "papers" in metrics:
                papers_data = json.dumps(metrics["papers"], indent=2)
                experiment.log_text(papers_data, name="research_papers.json")
            
            # Log concepts as assets
            if "concepts" in metrics:
                concepts_data = json.dumps(metrics["concepts"], indent=2)
                experiment.log_text(concepts_data, name="extracted_concepts.json")
            
            logger.info(f"Logged research metrics for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging research metrics: {str(e)}")
            return False
    
    def log_prototype_metrics(self, project_id: int, metrics: Dict) -> bool:
        """Log metrics from the prototyping stage"""
        try:
            experiment_key = f"{project_id}_prototype"
            
            if experiment_key not in self.experiments:
                self.create_experiment(project_id, "prototype")
            
            experiment = self.experiments[experiment_key]
            
            # Log prototype-specific metrics
            experiment.log_metric("development_time_hours", metrics.get("development_time", 0.0))
            experiment.log_metric("lines_of_code", metrics.get("lines_of_code", 0))
            experiment.log_metric("complexity_score", metrics.get("complexity_score", 0.0))
            experiment.log_metric("feature_completeness", metrics.get("feature_completeness", 0.0))
            
            # Log parameters
            experiment.log_parameter("programming_language", metrics.get("language", "python"))
            experiment.log_parameter("framework", metrics.get("framework", "unknown"))
            experiment.log_parameter("implementation_approach", metrics.get("approach", "unknown"))
            
            # Log code as asset
            if "source_code" in metrics:
                experiment.log_code(metrics["source_code"])
            
            # Log architecture diagram if available
            if "architecture_diagram" in metrics:
                experiment.log_image(metrics["architecture_diagram"], name="architecture.png")
            
            logger.info(f"Logged prototype metrics for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging prototype metrics: {str(e)}")
            return False
    
    def log_testing_metrics(self, project_id: int, metrics: Dict) -> bool:
        """Log metrics from the testing stage"""
        try:
            experiment_key = f"{project_id}_testing"
            
            if experiment_key not in self.experiments:
                self.create_experiment(project_id, "testing")
            
            experiment = self.experiments[experiment_key]
            
            # Log testing-specific metrics
            experiment.log_metric("test_coverage", metrics.get("test_coverage", 0.0))
            experiment.log_metric("tests_passed", metrics.get("tests_passed", 0))
            experiment.log_metric("tests_failed", metrics.get("tests_failed", 0))
            experiment.log_metric("performance_score", metrics.get("performance_score", 0.0))
            experiment.log_metric("memory_usage_mb", metrics.get("memory_usage", 0.0))
            experiment.log_metric("avg_response_time_ms", metrics.get("response_time", 0.0))
            
            # Log parameters
            experiment.log_parameter("testing_framework", metrics.get("testing_framework", "pytest"))
            experiment.log_parameter("test_environment", metrics.get("environment", "development"))
            
            # Log test reports
            if "test_report" in metrics:
                experiment.log_text(metrics["test_report"], name="test_report.html")
            
            # Log performance charts
            if "performance_charts" in metrics:
                for chart_name, chart_data in metrics["performance_charts"].items():
                    experiment.log_image(chart_data, name=f"{chart_name}.png")
            
            logger.info(f"Logged testing metrics for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging testing metrics: {str(e)}")
            return False
    
    def log_production_metrics(self, project_id: int, metrics: Dict) -> bool:
        """Log metrics from the production deployment stage"""
        try:
            experiment_key = f"{project_id}_production"
            
            if experiment_key not in self.experiments:
                self.create_experiment(project_id, "production")
            
            experiment = self.experiments[experiment_key]
            
            # Log production-specific metrics
            experiment.log_metric("deployment_time_minutes", metrics.get("deployment_time", 0.0))
            experiment.log_metric("optimization_improvement", metrics.get("optimization_improvement", 0.0))
            experiment.log_metric("scalability_score", metrics.get("scalability_score", 0.0))
            experiment.log_metric("security_score", metrics.get("security_score", 0.0))
            experiment.log_metric("monitoring_coverage", metrics.get("monitoring_coverage", 0.0))
            
            # Log parameters
            experiment.log_parameter("deployment_platform", metrics.get("platform", "unknown"))
            experiment.log_parameter("containerization", metrics.get("containerization", "docker"))
            experiment.log_parameter("orchestration", metrics.get("orchestration", "kubernetes"))
            
            # Log deployment configuration
            if "deployment_config" in metrics:
                config_data = json.dumps(metrics["deployment_config"], indent=2)
                experiment.log_text(config_data, name="deployment_config.json")
            
            # Log monitoring dashboards
            if "monitoring_dashboard" in metrics:
                experiment.log_image(metrics["monitoring_dashboard"], name="monitoring_dashboard.png")
            
            logger.info(f"Logged production metrics for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging production metrics: {str(e)}")
            return False
    
    def log_project_progression(self, project_id: int, progression_data: Dict) -> bool:
        """Log overall project progression metrics"""
        try:
            experiment_key = f"{project_id}_progression"
            
            if experiment_key not in self.experiments:
                self.create_experiment(project_id, "progression")
            
            experiment = self.experiments[experiment_key]
            
            # Log progression metrics
            experiment.log_metric("total_project_time_days", progression_data.get("total_time", 0.0))
            experiment.log_metric("research_to_prototype_time", progression_data.get("research_to_prototype", 0.0))
            experiment.log_metric("prototype_to_production_time", progression_data.get("prototype_to_production", 0.0))
            experiment.log_metric("overall_success_score", progression_data.get("success_score", 0.0))
            
            # Log stage completions
            for stage, completed in progression_data.get("stage_completions", {}).items():
                experiment.log_metric(f"{stage}_completed", 1 if completed else 0)
            
            # Log timeline
            if "timeline" in progression_data:
                timeline_data = json.dumps(progression_data["timeline"], indent=2)
                experiment.log_text(timeline_data, name="project_timeline.json")
            
            logger.info(f"Logged project progression for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging project progression: {str(e)}")
            return False
    
    def compare_projects(self, project_ids: List[int]) -> Dict:
        """Compare metrics across multiple projects"""
        try:
            comparison_data = {}
            
            for project_id in project_ids:
                # Get experiments for this project
                project_experiments = {}
                for stage in ["research", "prototype", "testing", "production"]:
                    exp_key = f"{project_id}_{stage}"
                    if exp_key in self.experiments:
                        project_experiments[stage] = self.experiments[exp_key]
                
                comparison_data[project_id] = project_experiments
            
            logger.info(f"Compared {len(project_ids)} projects")
            return comparison_data
            
        except Exception as e:
            logger.error(f"Error comparing projects: {str(e)}")
            return {}
    
    def get_project_dashboard_url(self, project_id: int) -> str:
        """Get the Comet dashboard URL for a project"""
        experiment_key = f"{project_id}_progression"
        if experiment_key in self.experiments:
            experiment = self.experiments[experiment_key]
            return experiment.get_url()
        return None
    
    def close_experiments(self, project_id: int):
        """Close all experiments for a project"""
        try:
            for stage in ["research", "prototype", "testing", "production", "progression"]:
                exp_key = f"{project_id}_{stage}"
                if exp_key in self.experiments:
                    self.experiments[exp_key].end()
                    del self.experiments[exp_key]
            
            logger.info(f"Closed all experiments for project {project_id}")
            
        except Exception as e:
            logger.error(f"Error closing experiments: {str(e)}")