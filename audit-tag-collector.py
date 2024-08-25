import os
import re
import json
import argparse
from datetime import datetime

"""
Audit Tag Collector

This script scans a given repository for audit-related annotations in the code.
It generates two reports:
1. A JSON report (`audit_tag_report.json`) containing all extracted annotations.
2. A Markdown report (`audit_tag_report.md`) with a categorized and organized view of the annotations, including outstanding questions listed at the top.

Usage:
    python audit-tag-collector.py /path/to/repo
"""

# Configuration variables
CONTEXT_LINES_BEFORE = 2  # Number of lines before the annotation to include in the context
CONTEXT_LINES_AFTER = 2   # Number of lines after the annotation to include in the context
OUTPUT_JSON_FILE = 'audit_tag_report.json'  
OUTPUT_MD_FILE = 'audit_tag_report.md'      
DATE_FORMAT = "%B %d, %Y, %H:%M:%S"        

# Regular expressions for matching annotations in the code
ANNOTATION_PATTERNS = {
    'audit': re.compile(r'// @audit\s'),
    'audit-question': re.compile(r'// @audit-question\b'),
    'audit-ok': re.compile(r'// @audit-ok\b'),
    'audit-info': re.compile(r'// @audit-info\b'),
    'audit-issue': re.compile(r'// @audit-issue\b'),
    'audit-gas': re.compile(r'// @audit-gas\b'),
    'audit-noncritical': re.compile(r'// @audit-noncritical\b'),
    'audit-warning': re.compile(r'// @audit-warning\b'),
    'audit-todo': re.compile(r'// @audit-todo\b'),
    'audit-clarify': re.compile(r'// @audit-clarify\b'),
    'audit-test': re.compile(r'// @audit-test\b')
}

# Annotation categories for the report
CATEGORIES = {
    'audit-question': 'Questions',
    'audit': 'General Audit',
    'audit-issue': 'Issues',
    'audit-noncritical': 'Non-Critical Issues',
    'audit-ok': 'OK',
    'audit-info': 'Information',
    'audit-gas': 'Gas',
    'audit-warning': 'Warnings',
    'audit-todo': 'TODOs',
    'audit-clarify': 'Clarifications',
    'audit-test': 'Tests'
}

def extract_context(lines, index):
    """Extracts the context of the annotation with surrounding lines."""
    start = max(0, index - CONTEXT_LINES_BEFORE)
    end = min(len(lines), index + CONTEXT_LINES_AFTER + 1)
    return ''.join(lines[start:end]).strip()

def extract_annotations(file_path):
    """Extracts annotations from a given file and returns them as a list of dictionaries."""
    annotations_found = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            for tag, pattern in ANNOTATION_PATTERNS.items():
                if pattern.search(line):
                    context = extract_context(lines, i)
                    annotations_found.append({
                        'file': file_path,
                        'line_number': i + 1,
                        'tag': tag,
                        'line': line.strip(),
                        'context': context,
                    })
    return annotations_found

def generate_md_report(annotations):
    """Generates a Markdown report from the extracted annotations."""
    with open(OUTPUT_MD_FILE, 'w') as report:
        # Header with report title and generation date
        report.write(f"# Audit Tag Report\n\nGenerated on: {datetime.now().strftime(DATE_FORMAT)}\n\n")
        
        # Outstanding Questions at the top
        questions_list = [
            f"- [ ] {a['line']} [`{a['file']}:{a['line_number']}`]"
            for a in annotations if a['tag'] == 'audit-question'
        ]
        if questions_list:
            report.write("## Outstanding Questions\n\n")
            report.write("\n".join(questions_list) + "\n\n")

        # Process all categories, including questions
        for category, title in CATEGORIES.items():
            relevant_annotations = [a for a in annotations if a['tag'] == category]
            if relevant_annotations:
                report.write(f"## {title}\n\n")
                for a in relevant_annotations:
                    report.write(
                        f"### {a['line']}\n"
                        f"**File:** `{a['file']}`  \n"
                        f"**Location:** Line {a['line_number']}  \n"
                        f"**Context:**\n```js\n{a['context']}\n```\n\n"
                    )

def generate_json_report(annotations):
    """Generates a JSON report from the extracted annotations."""
    with open(OUTPUT_JSON_FILE, 'w') as report:
        json.dump(annotations, report, indent=4)

def main(repo_path):
    """Main function to run the audit tag collector."""
    all_annotations = []
    script_name = os.path.basename(__file__)  # Exclude this script from the search

    # Walk through the repository and extract annotations from relevant files
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file == script_name:
                continue
            if file.endswith(('.sol', '.js')): 
                file_path = os.path.join(root, file)
                all_annotations.extend(extract_annotations(file_path))
    
    # Generate reports
    generate_json_report(all_annotations)
    generate_md_report(all_annotations)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate audit tag reports from code annotations.')
    parser.add_argument('repo_path', type=str, help='Path to the repository')
    
    args = parser.parse_args()
    main(args.repo_path)
