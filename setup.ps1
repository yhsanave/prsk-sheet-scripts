# Create virtual environment
if (!(Test-Path -Path ".venv")){
    python -m venv .venv
}

# Activate and install requirements
.venv/Scripts/activate
pip install -r requirements.txt

# Clone assets repo
if (!(Test-Path -Path "prsk-sheet-assets")){
    git clone https://github.com/yhsanave/prsk-sheet-assets.git
}

# Clone/Pull DB repo and populate database
python data.py
