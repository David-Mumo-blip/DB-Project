## Setup (do this once)
1. git clone <repo-url>   (already cloned? run: git checkout main, then git pull)
2. python -m venv venv
3. Activate: Windows CMD: venv\Scripts\activate | Git Bash: source venv/Scripts/activate | Mac/Linux: source venv/bin/activate
4. pip install -r requirements.txt
5. Copy config.example.py to config.py and put YOUR MySQL password in it
6. In MySQL Workbench, open sql/schema.sql and run it
7. python app.py
8. Open http://127.0.0.1:5000/api/health. It should say "connected"

## Every day
1. Activate the venv
2. git checkout main, then git pull
3. Switch to your branch: git checkout <your-branch>, then git merge main
4. Work, commit small and often
5. git push, then open a pull request. A teammate reviews before it merges into main

## Rules
- Never commit config.py (it has your own password)
- Only Leon and I edit app.py and routes/
- Tell the group chat before changing schema.sql or API.md
