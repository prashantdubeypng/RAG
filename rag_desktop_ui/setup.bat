@echo off
echo Setting up RAG Desktop UI...
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
echo Setup complete! Run 'run.bat' to start the application.