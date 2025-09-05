# AI_CODE_REVIEW_ASSISTANT

**AI-powered multi-language code review tool (Static + Gemini AI)**

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Supported Languages](#supported-languages)
- [License](#license)
- [Contact](#contact)

---

## Overview

AI_CODE_REVIEW_ASSISTANT is a robust, extensible tool designed to automate code review processes using both traditional static analysis and advanced AI-powered review via Google's Gemini AI. The assistant supports multi-language codebases (with Python as default), providing feedback, suggestions, and error detection for developers and teams.

---

## Features

- **Static Code Analysis:**  
  Integrates with popular static analysis tools to catch syntax errors, style issues, and potential bugs.

- **AI-Powered Review:**  
  Uses Gemini AI to perform semantic analysis, suggest improvements, and identify best practices.

- **Multi-Language Support:**  
  Easily extendable to review code in multiple programming languages.

- **Customizable Rules:**  
  Configure review rules and AI prompt settings to fit your project's needs.

- **Report Generation:**  
  Generates detailed, actionable review reports in markdown and JSON formats.

- **Easy Integration:**  
  CLI tool and API endpoints for seamless integration into CI/CD pipelines and developer workflows.

---

## Architecture

```
+-------------------------+
|   Source Code Files     |
+-----------+-------------+
            |
            v
+-----------+-------------+
| Static Analysis Engine  |
+-----------+-------------+
            |
            v
+-------------------------+
|   Gemini AI Reviewer    |
+-------------------------+
            |
            v
+-----------+-------------+
|  Report Generator       |
+-----------+-------------+
            |
            v
+-------------------------+
| Output (MD/JSON/CLI/API)|
+-------------------------+
```

---

## Installation

### Prerequisites

- Python 3.8+
- [pip](https://pip.pypa.io/en/stable/)
- Access to Gemini API (setup required)

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/VAISHNAVISARANGA/AI_CODE_REVIEW_ASSISTANT.git
   cd AI_CODE_REVIEW_ASSISTANT
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Gemini API (if required):**
   - Obtain your API key and set it in `.env` or config file as instructed below.

---

## Usage

### Command Line Interface (CLI)

```bash
python review_assistant.py --path <source_directory> --lang <language>
```

#### Example

```bash
python review_assistant.py --path ./src --lang python
```

### API Usage

Import and use in your Python scripts or web backend:

```python
from review_assistant import CodeReviewAssistant

assistant = CodeReviewAssistant(api_key="YOUR_GEMINI_API_KEY")
report = assistant.review_code(path="./src", language="python")
print(report)
```

### CI/CD Integration

Add the CLI command to your workflow scripts for automated reviews.

---

## Configuration

### Environment Variables

- `GEMINI_API_KEY`: Your Gemini AI API key.
- `REVIEW_LANGUAGES`: Comma-separated list of supported languages.

### Config File

Edit `config.yaml` or `.env` to customize static analysis rules, AI prompt templates, and output preferences.

---

## Supported Languages

- Python (default)
- Extendable for:
  - JavaScript
  - Java
  - C/C++
  - Go
  - ...and more

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

- **Author:** Vaishnavi Saranga
- **GitHub:** [VAISHNAVISARANGA](https://github.com/VAISHNAVISARANGA)
- **Issues:** [GitHub Issues](https://github.com/VAISHNAVISARANGA/AI_CODE_REVIEW_ASSISTANT/issues)

---

**Happy Coding & Reviewing!**
