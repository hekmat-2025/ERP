$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Clean previous builds
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

pyinstaller --clean --noconfirm "aftab_sahar_erp.spec"

Write-Host ""
Write-Host "Build complete."
Write-Host "Output folder: dist\\AftabSaharERP\\AftabSaharERP.exe"
