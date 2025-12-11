# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Alfred Workflow for generating epoch in various ways.

## Development Environment

- Python package manager: uv
- **Python version**: 3.9+
- **Virtual environment**: `.venv/` directory contains the Python virtual environment
- **Project configuration**: `pyproject.toml` defines project metadata and dependencies

## Coding Standards
- Follow PEP 8 style guide
- Use type hints where appropriate
- Keep functions small and focused

## Workflow Structure
- Main script handles Alfred input/output
- Use Alfred JSON format for results
- Error handling for all external API calls

## Testing
- Test locally before packaging
- Verify Alfred integration manually

## Important Rules
- NEVER create unnecessary files
- ALWAYS prefer editing existing files
- Keep dependencies minimal for Alfred workflow
- Document API keys/tokens setup in README only if asked

## Common Commands

### Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies (when added)
pip install -e .
```

### Package Management
```bash
# Add dependencies by editing pyproject.toml, then:
pip install -e .
```
