#!/bin/bash
# setup.sh - Script to set up the Research-to-Product Pipeline

echo "🚀 Setting up Research-to-Product Pipeline..."

# Check if Python 3.8+ is installed
python_version=$(python3 --version 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

echo "✅ Python detected: $python_version"

# Check if pip is installed
pip_version=$(pip3 --version 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "❌ pip3 is required but not installed."
    echo "Please install pip3 and try again."
    exit 1
fi

echo "✅ pip3 detected: $pip_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "❌ requirements.txt not found"
    echo "Please make sure you have requirements.txt in the current directory"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p uploads
mkdir -p chroma_db
mkdir -p services
mkdir -p templates
mkdir -p static/{css,js,img}
mkdir -p tests/{test_services}
mkdir -p config
mkdir -p docker
mkdir -p docs
mkdir -p scripts
mkdir -p tasks

echo "✅ Directories created"

# Copy environment template
if [ ! -f .env ]; then
    echo "⚙️ Creating environment configuration..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ .env file created from template"
        echo "📝 Please edit .env file with your API keys and configuration"
    else
        echo "❌ .env.example not found"
        echo "Creating a basic .env file..."
        cat > .env << EOF
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///research_pipeline.db

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Weaviate Configuration
WEAVIATE_URL=http://localhost:8080
# WEAVIATE_API_KEY=your-weaviate-api-key

# Comet ML Configuration
COMET_API_KEY=your-comet-api-key-here
COMET_WORKSPACE=your-workspace-name
COMET_PROJECT_NAME=research-to-product-pipeline

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF
        echo "✅ Basic .env file created"
    fi
else
    echo "✅ .env file already exists"
fi

# Initialize database
echo "🗃️ Initializing database..."
if [ -f "app.py" ]; then
    python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('✅ Database tables created successfully!')
"
else
    echo "❌ app.py not found. Database initialization skipped."
fi

# Start Weaviate (optional, for local development)
if command -v docker &> /dev/null; then
    echo "🐳 Starting local Weaviate instance..."
    
    # Check if Weaviate container is already running
    if [ "$(docker ps -q -f name=weaviate)" ]; then
        echo "✅ Weaviate container is already running"
    else
        # Stop and remove existing container if it exists
        if [ "$(docker ps -aq -f name=weaviate)" ]; then
            echo "🛑 Stopping existing Weaviate container..."
            docker stop weaviate >/dev/null 2>&1
            docker rm weaviate >/dev/null 2>&1
        fi
        
        # Start new Weaviate container
        docker run -d \
            --name weaviate \
            -p 8080:8080 \
            -e QUERY_DEFAULTS_LIMIT=25 \
            -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
            -e PERSISTENCE_DATA_PATH='/var/lib/weaviate' \
            -e DEFAULT_VECTORIZER_MODULE='text2vec-openai' \
            -e ENABLE_MODULES='text2vec-openai' \
            -e CLUSTER_HOSTNAME='node1' \
            -v weaviate_data:/var/lib/weaviate \
            semitechnologies/weaviate:latest
        
        echo "⏳ Waiting for Weaviate to start..."
        sleep 15
        
        # Check if Weaviate is ready
        weaviate_ready=false
        for i in {1..12}; do
            if curl -sf http://localhost:8080/v1/.well-known/ready >/dev/null 2>&1; then
                weaviate_ready=true
                break
            fi
            echo "⏳ Waiting for Weaviate ($i/12)..."
            sleep 5
        done
        
        if [ "$weaviate_ready" = true ]; then
            echo "✅ Weaviate is running and ready!"
        else
            echo "⚠️ Weaviate may need more time to start. Check with: docker logs weaviate"
        fi
    fi
else
    echo "⚠️ Docker not found. Please install Docker to run local Weaviate instance."
    echo "Or configure a cloud Weaviate instance in your .env file."
fi

# Start Redis (optional, for background tasks)
if command -v redis-server &> /dev/null; then
    echo "🔴 Starting Redis server..."
    
    # Check if Redis is already running
    if pgrep redis-server > /dev/null; then
        echo "✅ Redis server is already running"
    else
        redis-server --daemonize yes --port 6379
        sleep 2
        if pgrep redis-server > /dev/null; then
            echo "✅ Redis server started"
        else
            echo "❌ Failed to start Redis server"
        fi
    fi
else
    echo "⚠️ Redis not found. Install Redis for background task processing:"
    echo "   - Ubuntu/Debian: sudo apt update && sudo apt install redis-server"
    echo "   - macOS: brew install redis"
    echo "   - Or use a cloud Redis instance and update .env"
fi

# Create services/__init__.py if it doesn't exist
if [ ! -f "services/__init__.py" ]; then
    echo "📄 Creating services/__init__.py..."
    touch services/__init__.py
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "📄 Creating .gitignore..."
    cat > .gitignore << EOF
# Virtual Environment
venv/
env/
ENV/

# Environment Variables
.env

# Database
*.db
*.sqlite
*.sqlite3

# Logs
logs/
*.log

# Cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Uploads
uploads/*
!uploads/.gitkeep

# ChromaDB
chroma_db/

# Temporary files
*.tmp
*.temp
EOF
    echo "✅ .gitignore created"
fi

# Create uploads/.gitkeep
if [ ! -f "uploads/.gitkeep" ]; then
    touch uploads/.gitkeep
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit the .env file with your API keys:"
echo "   - OpenAI API key (required)"
echo "   - Comet ML API key (for tracking)"
echo "   - Weaviate settings (if using cloud)"
echo ""
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "3. Start the Flask application:"
echo "   python app.py"
echo ""
echo "4. Open your browser and go to:"
echo "   http://localhost:5000"
echo ""
echo "🔧 For development, you can also:"
echo "- Start Celery worker for background tasks:"
echo "  celery -A app.celery worker --loglevel=info"
echo ""
echo "- Monitor Celery tasks:"
echo "  celery -A app.celery flower"
echo ""
echo "- Run tests:"
echo "  pytest tests/"
echo ""
echo "📖 Check README.md for detailed documentation"
echo ""
echo "⚠️ Important: Make sure to:"
echo "1. Never commit your .env file to version control"
echo "2. Set strong SECRET_KEY in production"
echo "3. Use production database instead of SQLite for production deployment"