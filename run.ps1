# Activate venv
Write-Output 'Activating venv...'
.venv/Scripts/activate

# Update DB
Write-Output 'Updating database...'
python data.py

# Get honor images and bake them
Write-Output 'Getting images...'
Set-Location .\prsk-sheet-assets
git pull
Set-Location ..\

python get-honor-images.py
Write-Output 'Baking images...'
python bake-honors.py -nu

# Update sheets
Write-Output 'Updating sheets...'
python update-sheets.py -nu

# Deactivate venv
deactivate

# Push updated images to git
Write-Output 'Pushing baked images to github...'
Set-Location .\prsk-sheet-assets
$timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
git add -A
git commit -m "Auto-update $timestamp"
git push
Set-Location ..\