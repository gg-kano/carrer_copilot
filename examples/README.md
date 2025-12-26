# Career Copilot Examples

This directory contains example files and usage scenarios to help you get started with Career Copilot.

## Contents

### 1. Sample Job Descriptions

Example job descriptions you can use to test the matching functionality:

- `job_descriptions/software_engineer.txt` - Software Engineer position
- `job_descriptions/data_scientist.txt` - Data Scientist position
- `job_descriptions/product_manager.txt` - Product Manager position

### 2. API Usage Examples

Python scripts showing how to use Career Copilot programmatically:

- `api_usage.py` - Basic API usage examples
- `batch_processing.py` - Batch resume processing example
- `custom_matching.py` - Custom matching logic example

### 3. Integration Examples

Examples of integrating Career Copilot with other tools:

- `export_to_csv.py` - Export matched candidates to CSV
- `send_emails.py` - Email candidates automatically
- `slack_integration.py` - Send match notifications to Slack

## Quick Start

### Using Sample Job Descriptions

1. Start the Career Copilot application:
   ```bash
   streamlit run app.py
   ```

2. Navigate to the "Job Description" tab

3. Copy the content from any sample job description file in `job_descriptions/`

4. Paste it into the text area and click "Analyze"

### Running API Examples

```bash
cd examples
python api_usage.py
```

Make sure you have:
- Set up your `.env` file with `GOOGLE_API_KEY`
- Installed all dependencies
- Have some resumes already uploaded in the database

## Contributing Examples

Have a useful example? Please contribute!

1. Add your example to the appropriate directory
2. Include clear comments and documentation
3. Update this README with a description
4. Submit a pull request

## Need Help?

- Check the main [README](../README.md) for setup instructions
- Open an issue on GitHub
- Join the community discussions
