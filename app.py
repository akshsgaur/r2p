# app_fixed_datetime.py - Fixed version with timezone-aware datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
import json
import asyncio
from threading import Thread
from datetime import datetime, timezone
from services.pipeline_orchestrator import PipelineOrchestrator

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///research_pipeline.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Custom function for timezone-aware datetime
def utc_now():
    """Get current UTC time in a timezone-aware manner"""
    return datetime.now(timezone.utc)



# Initialize pipeline orchestrator
orchestrator = PipelineOrchestrator()

# Models with timezone-aware datetime
class ResearchProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='initialized')  # initialized, running, completed, failed
    pipeline_config = db.Column(db.Text)  # JSON config for pipeline
    results = db.Column(db.Text)  # JSON results from pipeline
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationships
    research_papers = db.relationship('ResearchPaper', backref='project', lazy=True, cascade='all, delete-orphan')
    prototypes = db.relationship('Prototype', backref='project', lazy=True, cascade='all, delete-orphan')

class ResearchPaper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    authors = db.Column(db.String(1000))
    abstract = db.Column(db.Text)
    url = db.Column(db.String(500))
    paper_type = db.Column(db.String(50), default='manual')  # manual, arxiv, web
    indexed_at = db.Column(db.DateTime, default=utc_now)
    
    # Foreign keys
    project_id = db.Column(db.Integer, db.ForeignKey('research_project.id'), nullable=False)

class Prototype(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    code = db.Column(db.Text)
    github_url = db.Column(db.String(500))
    status = db.Column(db.String(50), default='development')  # development, testing, deployed
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Foreign keys
    project_id = db.Column(db.Integer, db.ForeignKey('research_project.id'), nullable=False)

# Routes
@app.route('/')
def index():
    projects = ResearchProject.query.order_by(ResearchProject.updated_at.desc()).all()
    health_status = orchestrator.get_pipeline_health()
    return render_template('index.html', projects=projects, health_status=health_status)

@app.route('/project/<int:id>')
def project_detail(id):
    project = ResearchProject.query.get_or_404(id)
    status = orchestrator.get_project_status(id)
    results = json.loads(project.results) if project.results else {}
    return render_template('project_detail.html', project=project, status=status, results=results)

@app.route('/new_project', methods=['GET', 'POST'])
def new_project():
    if request.method == 'POST':
        # Extract features from form data
        features = request.form.get('features', '').split(',')
        features = [f.strip() for f in features if f.strip()]
        
        # Build pipeline configuration
        pipeline_config = {
            "prototype_requirements": {
                "language": request.form.get('language', 'python'),
                "framework": request.form.get('framework', 'flask'),
                "features": features
            },
            "deployment_target": request.form.get('deployment_target', 'docker'),
            "ai_model": request.form.get('ai_model', 'gpt-3.5-turbo'),
            "max_concepts": int(request.form.get('max_concepts', 20)),
            "prototype_complexity": request.form.get('prototype_complexity', 'moderate'),
            "include_tests": request.form.get('include_tests') == 'on',
            "enable_monitoring": request.form.get('enable_monitoring') == 'on'
        }
        
        project = ResearchProject(
            title=request.form['title'],
            description=request.form['description'],
            pipeline_config=json.dumps(pipeline_config)
        )
        db.session.add(project)
        db.session.commit()
        flash('Project created successfully!', 'success')
        return redirect(url_for('project_detail', id=project.id))
    
    return render_template('new_project.html')

@app.route('/project/<int:id>/add_paper', methods=['POST'])
def add_paper(id):
    project = ResearchProject.query.get_or_404(id)
    
    paper = ResearchPaper(
        title=request.form['title'],
        authors=request.form.get('authors', ''),
        abstract=request.form.get('abstract', ''),
        url=request.form.get('url', ''),
        paper_type=request.form.get('paper_type', 'manual'),
        project_id=id
    )
    
    db.session.add(paper)
    db.session.commit()
    
    flash('Research paper added successfully!', 'success')
    return redirect(url_for('project_detail', id=id))

# Add favicon route to stop the errors
@app.route('/favicon.ico')
def favicon():
    return '', 404

# API Routes for pipeline integration
@app.route('/api/pipeline/run/<int:project_id>', methods=['POST'])
def run_pipeline(project_id):
    """Run the complete pipeline for a project"""
    try:
        project = ResearchProject.query.get_or_404(project_id)
        project.status = 'running'
        project.updated_at = utc_now()  # Use timezone-aware datetime
        db.session.commit()
        
        # Get papers for the project
        papers = []
        for paper in project.research_papers:
            papers.append({
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "url": paper.url,
                "type": paper.paper_type
            })
        
        # Get pipeline config
        config = json.loads(project.pipeline_config) if project.pipeline_config else {}
        config["papers"] = papers
        
        # Run pipeline in background thread
        def run_pipeline_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(orchestrator.run_complete_pipeline(project_id, config))
                
                # Update project with results
                project.results = json.dumps(result)
                project.status = 'completed' if result.get('status') == 'completed' else 'failed'
                project.updated_at = utc_now()  # Use timezone-aware datetime
                db.session.commit()
                
            except Exception as e:
                project.status = 'failed'
                project.results = json.dumps({"error": str(e)})
                project.updated_at = utc_now()  # Use timezone-aware datetime
                db.session.commit()
            
            finally:
                loop.close()
        
        thread = Thread(target=run_pipeline_async)
        thread.start()
        
        return jsonify({
            'status': 'started',
            'message': 'Pipeline execution started',
            'project_id': project_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pipeline/stage/<int:project_id>/<stage>', methods=['POST'])
def run_stage(project_id, stage):
    """Run a single stage of the pipeline"""
    try:
        project = ResearchProject.query.get_or_404(project_id)
        config = request.json or {}
        
        # Add project-specific data to config
        if stage == 'research':
            papers = []
            for paper in project.research_papers:
                papers.append({
                    "title": paper.title,
                    "authors": paper.authors,
                    "abstract": paper.abstract,
                    "url": paper.url,
                    "type": paper.paper_type
                })
            config["papers"] = papers
        
        result = orchestrator.run_single_stage(project_id, stage, config)
        
        # Update project status
        current_results = json.loads(project.results) if project.results else {}
        if 'stages' not in current_results:
            current_results['stages'] = {}
        current_results['stages'][stage] = result
        project.results = json.dumps(current_results)
        project.updated_at = utc_now()  # Use timezone-aware datetime
        db.session.commit()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project/<int:project_id>/status')
def get_project_status(project_id):
    """Get current project status"""
    try:
        project = ResearchProject.query.get_or_404(project_id)
        status = orchestrator.get_project_status(project_id)
        
        return jsonify({
            'project_status': project.status,
            'pipeline_status': status,
            'last_updated': project.updated_at.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Check pipeline component health"""
    return jsonify(orchestrator.get_pipeline_health())

@app.route('/api/project/<int:project_id>/export')
def export_project(project_id):
    """Export project data for external use"""
    try:
        project = ResearchProject.query.get_or_404(project_id)
        
        export_data = {
            "project": {
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()
            },
            "papers": [
                {
                    "title": paper.title,
                    "authors": paper.authors,
                    "abstract": paper.abstract,
                    "url": paper.url,
                    "type": paper.paper_type
                }
                for paper in project.research_papers
            ],
            "prototypes": [
                {
                    "name": prototype.name,
                    "description": prototype.description,
                    "code": prototype.code,
                    "status": prototype.status
                }
                for prototype in project.prototypes
            ],
            "results": json.loads(project.results) if project.results else None
        }
        
        return jsonify(export_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API Routes for individual service integrations
@app.route('/api/llamaindex/index_papers', methods=['POST'])
def index_papers():
    """Index research papers using LlamaIndex"""
    try:
        project_id = request.json.get('project_id')
        papers = request.json.get('papers', [])
        
        # Use orchestrator to index papers
        indexed_count = orchestrator.llamaindex.index_papers(project_id, papers)
        
        return jsonify({
            'status': 'success', 
            'indexed_count': indexed_count,
            'message': f'Successfully indexed {indexed_count} papers'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/llamaindex/query', methods=['POST'])
def query_research():
    """Query indexed research papers"""
    try:
        project_id = request.json.get('project_id')
        query = request.json.get('query')
        top_k = request.json.get('top_k', 5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        result = orchestrator.llamaindex.query_research(project_id, query, top_k)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weaviate/connect_concepts', methods=['POST'])
def connect_concepts():
    """Connect research concepts to implementations using Weaviate"""
    try:
        project_id = request.json.get('project_id')
        concepts = request.json.get('concepts', [])
        
        # Create schema if it doesn't exist
        orchestrator.weaviate.create_schema(project_id)
        
        # Store concepts
        concept_data = [{"title": concept, "description": concept} for concept in concepts]
        stored_count = orchestrator.weaviate.store_concepts(project_id, concept_data)
        
        return jsonify({
            'status': 'success', 
            'stored_concepts': stored_count,
            'message': f'Connected {stored_count} concepts'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weaviate/suggestions', methods=['POST'])
def get_implementation_suggestions():
    """Get implementation suggestions from Weaviate"""
    try:
        project_id = request.json.get('project_id')
        concept = request.json.get('concept', 'main concept')
        limit = request.json.get('limit', 3)
        
        suggestions = orchestrator.weaviate.get_implementation_suggestions(project_id, concept, limit)
        return jsonify(suggestions)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/crewai/analyze', methods=['POST'])
def crewai_analyze():
    """Trigger CrewAI agents for analysis and prototyping"""
    try:
        project_id = request.json.get('project_id')
        task = request.json.get('task')  # research_analysis, prototyping, testing, productionization
        data = request.json.get('data', {})
        
        if task == 'research_analysis':
            result = orchestrator.crewai.analyze_research(project_id, data)
        elif task == 'prototyping':
            concept = data.get('concept', '')
            requirements = data.get('requirements', {})
            result = orchestrator.crewai.create_prototype(project_id, concept, requirements)
        elif task == 'testing':
            prototype_code = data.get('prototype_code', '')
            requirements = data.get('requirements', {})
            result = orchestrator.crewai.design_tests(project_id, prototype_code, requirements)
        elif task == 'productionization':
            prototype_code = data.get('prototype_code', '')
            test_results = data.get('test_results', {})
            result = orchestrator.crewai.productionize(project_id, prototype_code, test_results)
        else:
            return jsonify({'error': f'Unknown task: {task}'}), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/crewai/status/<task_id>')
def crewai_task_status(task_id):
    """Get CrewAI task status"""
    try:
        status = orchestrator.crewai.get_task_status(task_id)
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/comet/track', methods=['POST'])
def comet_track():
    """Track progress and metrics with Comet"""
    try:
        project_id = request.json.get('project_id')
        stage = request.json.get('stage')  # research, prototype, testing, production
        metrics = request.json.get('metrics', {})
        
        if stage == 'research':
            success = orchestrator.comet.log_research_metrics(project_id, metrics)
        elif stage == 'prototype':
            success = orchestrator.comet.log_prototype_metrics(project_id, metrics)
        elif stage == 'testing':
            success = orchestrator.comet.log_testing_metrics(project_id, metrics)
        elif stage == 'production':
            success = orchestrator.comet.log_production_metrics(project_id, metrics)
        else:
            return jsonify({'error': f'Unknown stage: {stage}'}), 400
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Metrics logged for {stage} stage',
                'logged_metrics': list(metrics.keys())
            })
        else:
            return jsonify({'error': 'Failed to log metrics'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/comet/dashboard/<int:project_id>')
def get_comet_dashboard(project_id):
    """Get Comet dashboard URL for a project"""
    try:
        url = orchestrator.comet.get_project_dashboard_url(project_id)
        if url:
            return jsonify({'dashboard_url': url})
        else:
            return jsonify({'error': 'No dashboard found for this project'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Additional routes for paper management
@app.route('/api/project/<int:project_id>/papers', methods=['GET'])
def list_papers(project_id):
    """List all papers for a project"""
    try:
        project = ResearchProject.query.get_or_404(project_id)
        papers = [
            {
                "id": paper.id,
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "url": paper.url,
                "type": paper.paper_type,
                "indexed_at": paper.indexed_at.isoformat()
            }
            for paper in project.research_papers
        ]
        return jsonify(papers)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project/<int:project_id>/papers/<int:paper_id>', methods=['DELETE'])
def delete_paper(project_id, paper_id):
    """Delete a research paper"""
    try:
        paper = ResearchPaper.query.filter_by(id=paper_id, project_id=project_id).first_or_404()
        db.session.delete(paper)
        db.session.commit()
        flash('Paper deleted successfully!', 'success')
        return jsonify({'status': 'success', 'message': 'Paper deleted'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Project management routes
@app.route('/api/project/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Update project details"""
    try:
        project = ResearchProject.query.get_or_404(project_id)
        data = request.json
        
        if 'title' in data:
            project.title = data['title']
        if 'description' in data:
            project.description = data['description']
        if 'pipeline_config' in data:
            project.pipeline_config = json.dumps(data['pipeline_config'])
        
        project.updated_at = utc_now()  # Use timezone-aware datetime
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Project updated'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project and all its data"""
    try:
        project = ResearchProject.query.get_or_404(project_id)
        
        # Clean up pipeline resources
        orchestrator.cleanup_project(project_id)
        
        # Delete the project (cascades to papers and prototypes)
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Project deleted'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Template filters
@app.template_filter('from_json')
def from_json_filter(value):
    """Template filter to parse JSON strings"""
    try:
        return json.loads(value) if value else {}
    except:
        return {}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)