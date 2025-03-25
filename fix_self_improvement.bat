@echo off
cd /d %~dp0
echo ==== Fixing Self-Improvement Module Issues ====
echo.

call lyra_env\Scripts\activate.bat

echo Step 1: Installing required packages...
pip install --quiet GitPython autopep8 pylint pytest requests

echo Step 2: Recreating data directories...
mkdir data 2>nul
mkdir data\vintix_rl 2>nul
mkdir data\advisor_config 2>nul
mkdir logs 2>nul

echo Step 3: Fixing configuration file...
python -c "import sys, os, json; sys.path.append('.'); config_path = os.path.join('data', 'advisor_config.json'); if os.path.exists(config_path): config = json.load(open(config_path, 'r')); else: config = {'default_provider': 'local', 'providers': {'local': {'api_base': 'http://127.0.0.1:8000/v1', 'model': 'local-model', 'enabled': True}, 'openai': {'api_key': '', 'model': 'gpt-4', 'api_base': 'https://api.openai.com/v1', 'enabled': False}, 'deepseek': {'api_key': '', 'model': 'deepseek-coder-33b-instruct', 'api_base': 'https://api.deepseek.com/v1', 'enabled': False}, 'anthropic': {'api_key': '', 'model': 'claude-3-opus-20240229', 'api_base': 'https://api.anthropic.com/v1/messages', 'enabled': False}}, 'prompts': {'code_review': 'You are an expert programmer tasked with improving the following code. Please suggest improvements for clarity, efficiency, security, and best practices. Focus on specific, actionable suggestions that will make the code better.\\n\\nCode to review:\\n```{language}\\n{code}\\n```\\n\\nPlease provide your suggestions in a clear, numbered list format with brief explanations.', 'bug_fixing': 'You are a debugging expert. Review this code and identify any potential bugs or issues:\\n\\n```{language}\\n{code}\\n```\\n\\nPlease list all potential bugs or issues you find and suggest fixes for each one.', 'algorithm_optimization': 'You are an algorithm optimization specialist. Review the following code and suggest optimizations to improve its time/space complexity:\\n\\n```{language}\\n{code}\\n```\\n\\nPlease analyze the algorithm, identify its current complexity, and suggest specific optimizations.'}}; os.makedirs(os.path.dirname(config_path), exist_ok=True); json.dump(config, open(config_path, 'w'), indent=2); print(f'Configuration file {\"updated\" if os.path.exists(config_path) else \"created\"!')"

echo Step 4: Setting up experience data...
python -c "import sys, os, json; sys.path.append('.'); exp_path = os.path.join('data', 'vintix_rl', 'experience.json'); if not os.path.exists(os.path.dirname(exp_path)): os.makedirs(os.path.dirname(exp_path)); if not os.path.exists(exp_path): json.dump({'code_changes': [], 'feedback': [], 'performance_metrics': {}, 'learning_patterns': {}, 'expert_consultations': []}, open(exp_path, 'w'), indent=2); print(f'Experience data {\"updated\" if os.path.exists(exp_path) else \"created\"!')"

echo Step 5: Creating error log...
python -c "import sys, os, logging; sys.path.append('.'); log_dir = os.path.join('logs'); os.makedirs(log_dir, exist_ok=True); logger = logging.getLogger('lyra.self_improvement'); logger.setLevel(logging.INFO); file_handler = logging.FileHandler(os.path.join(log_dir, 'self_improvement.log')); file_handler.setLevel(logging.INFO); formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'); file_handler.setFormatter(formatter); logger.addHandler(file_handler); logger.info('Log initialized by fix_self_improvement.bat'); print('Log file created!')"

echo Step 6: Testing imports...
python -c "import sys; sys.path.append('.'); try: from lyra.self_improvement.llm_advisor import LLMAdvisor; from lyra.self_improvement.reinforcement_learning import VintixRL; from lyra.self_improvement.code_manager import CodeManager; print('All modules imported successfully!'); except ImportError as e: print(f'Import error: {e}')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Module imports failed. Running self_improvement.bat...
    call self_improvement.bat
) else (
    echo All modules imported successfully!
)

echo.
echo Fix completed!
echo Running diagnostics...
echo.
call diagnose_llm_connections.bat

pause