# CodeAuditX

A powerful static code analysis tool for multiple programming languages, providing comprehensive code quality checks and linting capabilities.

## Features

- **Multi-language support**: Analyzes code in Python, JavaScript, Go, PHP, Java, and C/C++
- **Comprehensive rule sets**: Built-in support for popular coding standards
- **Extensible architecture**: Easy to add new languages and custom rules
- **Detailed reporting**: Clear violation messages with line numbers
- **Integration-ready**: Can be used in CI/CD pipelines

## Supported Languages

- Python
- JavaScript
- Go
- PHP
- Java
- C/C++

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Scan a single file
python -m src.main --scan path/to/file.py

# Scan multiple files
python -m src.main --scan file1.py file2.js file3.go

# Scan a directory
python -m src.main --scan path/to/directory/
```

### Using the Shell Script

```bash
chmod +x run.sh
./run.sh path/to/code
```

## Configuration

Custom rules can be defined in `config/custom_rules.json`. The tool will automatically load these rules when running.

## Development

To contribute to this project:

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.