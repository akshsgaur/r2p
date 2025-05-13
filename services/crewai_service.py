# services/crewai_service.py - CrewAI integration
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
import os
import logging
from typing import Dict, List, Any
import json

logger = logging.getLogger(__name__)

class ResearchAnalysisTool(BaseTool):
    name: str = "Research Analysis Tool"
    description: str = "Analyzes research papers and extracts key insights"
    
    def _run(self, research_data: str) -> str:
        # Analyze research data and return insights
        return f"Analysis complete for: {research_data[:100]}..."

class PrototypingTool(BaseTool):
    name: str = "Prototyping Tool"
    description: str = "Generates prototype code based on research insights"
    
    def _run(self, concept: str, requirements: str) -> str:
        # Generate prototype code
        return f"Prototype generated for {concept} with requirements: {requirements}"

class TestingTool(BaseTool):
    name: str = "Testing Tool"
    description: str = "Creates test cases and validation strategies"
    
    def _run(self, prototype_code: str, requirements: str) -> str:
        # Generate test cases
        return f"Test cases generated for prototype"

class ProductionizationTool(BaseTool):
    name: str = "Productionization Tool"
    description: str = "Suggests production deployment strategies and optimizations"
    
    def _run(self, prototype_code: str, performance_metrics: str) -> str:
        # Suggest production deployment
        return f"Production deployment strategy created"

class CrewAIService:
    def __init__(self):
        self.setup_agents()
        self.current_tasks = {}
        
    def setup_agents(self):
        """Initialize CrewAI agents for different stages of the pipeline"""
        
        # Research Analyst Agent
        self.research_analyst = Agent(
            role='Research Analyst',
            goal='Analyze research papers and extract key insights and concepts',
            backstory='''You are an expert research analyst with deep knowledge in various 
            scientific domains. You excel at identifying key concepts, methodologies, 
            and practical applications from research papers.''',
            tools=[ResearchAnalysisTool()],
            verbose=True,
            memory=True
        )
        
        # Prototype Developer Agent
        self.prototype_developer = Agent(
            role='Prototype Developer',
            goal='Transform research concepts into working prototypes',
            backstory='''You are a skilled software engineer who specializes in rapidly 
            prototyping research concepts. You can translate complex academic ideas 
            into practical, working code implementations.''',
            tools=[PrototypingTool()],
            verbose=True,
            memory=True
        )
        
        # Testing Specialist Agent
        self.testing_specialist = Agent(
            role='Testing Specialist',
            goal='Design comprehensive testing strategies for prototypes',
            backstory='''You are a quality assurance expert who ensures that prototypes 
            are robust, well-tested, and ready for production. You create both unit 
            tests and integration tests.''',
            tools=[TestingTool()],
            verbose=True,
            memory=True
        )
        
        # Production Engineer Agent
        self.production_engineer = Agent(
            role='Production Engineer',
            goal='Optimize and deploy prototypes to production',
            backstory='''You are a DevOps and production engineering expert who takes 
            prototypes and makes them production-ready with proper scaling, monitoring, 
            and deployment strategies.''',
            tools=[ProductionizationTool()],
            verbose=True,
            memory=True
        )
    
    def analyze_research(self, project_id: int, research_data: Dict) -> Dict:
        """Have the research analyst analyze research papers"""
        try:
            task = Task(
                description=f"""
                Analyze the following research data for project {project_id}:
                
                Research Papers: {json.dumps(research_data.get('papers', []), indent=2)}
                Research Concepts: {json.dumps(research_data.get('concepts', []), indent=2)}
                
                Please:
                1. Identify the main research themes and methodologies
                2. Extract key technical concepts that can be implemented
                3. Assess the practical feasibility of each concept
                4. Suggest potential applications and use cases
                5. Recommend the best concepts for prototyping
                """,
                agent=self.research_analyst,
                expected_output='Detailed analysis report with actionable insights'
            )
            
            crew = Crew(agents=[self.research_analyst], tasks=[task], process=Process.sequential)
            result = crew.kickoff()
            
            self.current_tasks[f"research_analysis_{project_id}"] = {
                "status": "completed",
                "result": result
            }
            
            return {
                "task_id": f"research_analysis_{project_id}",
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error in research analysis: {str(e)}")
            return {"error": str(e)}
    
    def create_prototype(self, project_id: int, concept: str, requirements: Dict) -> Dict:
        """Have the prototype developer create a prototype"""
        try:
            task = Task(
                description=f"""
                Create a prototype for the following concept from project {project_id}:
                
                Concept: {concept}
                Requirements: {json.dumps(requirements, indent=2)}
                
                Please:
                1. Design the architecture for the prototype
                2. Create the main implementation code
                3. Include necessary dependencies and setup instructions
                4. Provide a simple example of how to use the prototype
                5. Document any assumptions or limitations
                """,
                agent=self.prototype_developer,
                expected_output='Complete prototype with code, documentation, and usage examples'
            )
            
            crew = Crew(agents=[self.prototype_developer], tasks=[task], process=Process.sequential)
            result = crew.kickoff()
            
            self.current_tasks[f"prototyping_{project_id}"] = {
                "status": "completed",
                "result": result
            }
            
            return {
                "task_id": f"prototyping_{project_id}",
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error in prototyping: {str(e)}")
            return {"error": str(e)}
    
    def design_tests(self, project_id: int, prototype_code: str, requirements: Dict) -> Dict:
        """Have the testing specialist design tests for the prototype"""
        try:
            task = Task(
                description=f"""
                Design comprehensive tests for the prototype in project {project_id}:
                
                Prototype Code: {prototype_code[:500]}... (truncated)
                Requirements: {json.dumps(requirements, indent=2)}
                
                Please:
                1. Create unit tests for individual components
                2. Design integration tests for the full system
                3. Develop performance benchmarks
                4. Create test data and scenarios
                5. Propose a testing strategy and timeline
                """,
                agent=self.testing_specialist,
                expected_output='Complete testing suite with test cases, benchmarks, and strategy'
            )
            
            crew = Crew(agents=[self.testing_specialist], tasks=[task], process=Process.sequential)
            result = crew.kickoff()
            
            self.current_tasks[f"testing_{project_id}"] = {
                "status": "completed",
                "result": result
            }
            
            return {
                "task_id": f"testing_{project_id}",
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error in test design: {str(e)}")
            return {"error": str(e)}
    
    def productionize(self, project_id: int, prototype_code: str, test_results: Dict) -> Dict:
        """Have the production engineer prepare the prototype for production"""
        try:
            task = Task(
                description=f"""
                Prepare the prototype from project {project_id} for production deployment:
                
                Prototype Code: {prototype_code[:500]}... (truncated)
                Test Results: {json.dumps(test_results, indent=2)}
                
                Please:
                1. Suggest production architecture and infrastructure
                2. Recommend optimization strategies
                3. Design monitoring and logging solutions
                4. Create deployment scripts and configurations
                5. Plan rollback and disaster recovery procedures
                """,
                agent=self.production_engineer,
                expected_output='Production deployment plan with scripts, monitoring, and optimization strategies'
            )
            
            crew = Crew(agents=[self.production_engineer], tasks=[task], process=Process.sequential)
            result = crew.kickoff()
            
            self.current_tasks[f"productionization_{project_id}"] = {
                "status": "completed",
                "result": result
            }
            
            return {
                "task_id": f"productionization_{project_id}",
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error in productionization: {str(e)}")
            return {"error": str(e)}
    
    def collaborate_full_pipeline(self, project_id: int, research_data: Dict) -> Dict:
        """Run a collaborative session with all agents for the full pipeline"""
        try:
            # Create tasks for each agent
            research_task = Task(
                description=f"Analyze research data and extract key implementable concepts for project {project_id}",
                agent=self.research_analyst,
                expected_output='List of prioritized concepts with implementation feasibility scores'
            )
            
            prototype_task = Task(
                description="Take the top research concepts and create working prototypes",
                agent=self.prototype_developer,
                expected_output='Functional prototype code with documentation',
                dependencies=[research_task]
            )
            
            testing_task = Task(
                description="Design and implement comprehensive tests for the prototypes",
                agent=self.testing_specialist,
                expected_output='Complete test suite with coverage analysis',
                dependencies=[prototype_task]
            )
            
            production_task = Task(
                description="Prepare prototypes for production deployment with optimization and monitoring",
                agent=self.production_engineer,
                expected_output='Production-ready deployment plan and optimized code',
                dependencies=[testing_task]
            )
            
            # Create crew with all agents
            crew = Crew(
                agents=[self.research_analyst, self.prototype_developer, 
                       self.testing_specialist, self.production_engineer],
                tasks=[research_task, prototype_task, testing_task, production_task],
                process=Process.sequential,
                memory=True,
                verbose=2
            )
            
            # Execute the full pipeline
            result = crew.kickoff()
            
            self.current_tasks[f"full_pipeline_{project_id}"] = {
                "status": "completed",
                "result": result
            }
            
            return {
                "task_id": f"full_pipeline_{project_id}",
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error in full pipeline collaboration: {str(e)}")
            return {"error": str(e)}
    
    def get_task_status(self, task_id: str) -> Dict:
        """Get the status of a specific task"""
        return self.current_tasks.get(task_id, {"status": "not found"})
    
    def list_active_tasks(self) -> List[str]:
        """List all active tasks"""
        return list(self.current_tasks.keys())