# Create virtual environment
if [ ! -d ".venv" ]; then
    python -m venv .venv
fi

# Activate and install requirements
source .venv/Scripts/activate
pip install -r requirements.txt

# Clone assets repo
if [ ! -d "prsk-sheet-assets" ]; then
    git clone https://github.com/yhsanave/prsk-sheet-assets.git
fi

# Clone/Pull DB repo and populate database
python data.py
