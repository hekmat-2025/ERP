# Aftab Sahar Blue Cons. ERP

Offline-first desktop ERP for a construction company.

## Tech
- UI: PyQt5
- Database: SQLite
- ORM: SQLAlchemy (mandatory)
- PDF: reportlab (invoice generation)
- Export: pandas / openpyxl
- Charts: matplotlib
- Logging: Python `logging`
- Packaging: PyInstaller compatible

## Setup (development)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Assets (logo)
- Place your company logo at `assets/logo.png`
  - Used on login (optional), dashboard header, and invoice PDF.

## Packaging (PyInstaller)

### Build for Windows 10/11 (recommended)

PyInstaller must be run **on Windows** to produce a Windows `.exe`.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\build_windows.ps1
```

Output:
- `dist\AftabSaharERP\AftabSaharERP.exe`

Icon:
- Replace `assets/app_icon.png` (source) and rebuild to update `assets/app.ico` used by the `.exe`.

### Runtime files location (Windows)
The app stores writable data under:
- `%APPDATA%\AftabSaharERP\`

This includes:
- `config\settings.json`
- `data\*.sqlite3`
- `logs\`

# ERP
