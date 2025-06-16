# Työsopimuskone

A standalone, self-distributable Mac Python GUI app for generating Finnish employment contract ("työsopimus") PDFs. The app allows users to fill out contract details, generate a PDF, preview the contract, and store/retrieve previous contracts. Built with PyQt5 and reportlab, and packaged with PyInstaller.

## Features
- Fill in all standard employment contract fields in a clear, grouped UI
- Required fields are highlighted with orange labels and borders for better visibility
- Live HTML preview of the contract
- Generate a professional PDF (A4) of the contract with structured formatting using Times-Bold headings
- Save and load previous contracts (individual JSON files per contract)
- All data is stored locally, no cloud or external dependencies
- Dark mode friendly UI with high contrast elements
- Test Driven Development (TDD) with comprehensive automated unittests
- **App icon included in the bundle** (see `assets/app_icon.icns`)
- **App and binary always named `Työsopimuskone.app`** for consistency

## Installation

1. Clone the repository:

   ```sh
   git clone <repo-url>
   cd sopimuskone
   ```

2. Create and activate a Python 3 virtual environment:

   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

## Running the App

```sh
python main.py
```

## Building a Standalone macOS App

PyInstaller is used to create a standalone `.app` bundle using the provided `.spec` file:

```sh
pyinstaller TyosopimusApp.spec
```

The resulting app will be in the `dist/` directory as `Työsopimuskone.app`.

## Running Tests

```sh
python -m unittest test_main.py
```

## Project Structure

- `main.py` — Main application logic, GUI, PDF generation, data persistence
- `test_main.py` — Unittest suite for TDD
- `requirements.txt` — Python dependencies
- `assets/app_icon.icns` — App icon for macOS bundle
- `TyosopimusApp.spec` — PyInstaller spec file (always builds `Työsopimuskone.app`)
- `.vscode/tasks.json` — VS Code build task configuration (uses the spec file)
- `.github/workflows/build_macos.yml` — GitHub Actions CI/CD workflow (uses the spec file and correct app name)

## Dependencies

- PyQt5
- reportlab
- pyinstaller (for packaging)

## License
MIT

## Author
Olli Sulopuisto

[Contract icons created by Freepik - Flaticon](https://www.flaticon.com/free-icons/contract)