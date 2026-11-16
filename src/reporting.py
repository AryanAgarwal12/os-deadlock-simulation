"""Reporting and Data Export Module.

Generates structured CSV and Markdown reports for analytical test case results
(TC1 to TC6) and the student AI Usage Record suitable for B.Tech submission.
"""

import io
import csv
from typing import List, Dict, Any
from datetime import datetime


def export_test_results_to_csv(test_results: List[Dict[str, Any]]) -> str:
    """Generate a clean CSV string of the analytical test results."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Test ID",
        "Scenario Name",
        "Inputs Summary",
        "Expected Result",
        "Actual Output",
        "Status",
        "Analysis & Conclusion",
    ])

    for tc in test_results:
        writer.writerow([
            tc.get("test_id", ""),
            tc.get("scenario_name", ""),
            tc.get("inputs_summary", ""),
            tc.get("expected_result", ""),
            tc.get("actual_output", ""),
            tc.get("status", ""),
            tc.get("analysis", ""),
        ])

    return output.getvalue()


def export_test_results_to_markdown(test_results: List[Dict[str, Any]]) -> str:
    """Generate a comprehensive Markdown report of test results."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_tests = len(test_results)
    passed_tests = sum(1 for tc in test_results if tc.get("status") == "PASS")

    md = [
        "# Operating Systems IA Activity 2 — Analytical Test Report",
        f"**Generated On:** {timestamp}  ",
        f"**Project:** OS Deadlock Analysis & Resource Allocation Dashboard  ",
        "**Institution:** MIT Academy of Engineering  ",
        "**Department:** Computer Department  ",
        "**Team Members:** Parth Wankhade, Aryan Agarwal, Vikas Choudhary, Sanket Kongare  ",
        f"**Test Suite Summary:** {passed_tests}/{total_tests} Tests Passed ({(passed_tests/total_tests)*100:.1f}%)  ",
        "\n---\n",
        "## Summary Results Table\n",
        "| Test ID | Scenario Name | Status | Expected Result | Actual Output |",
        "| :--- | :--- | :---: | :--- | :--- |",
    ]

    for tc in test_results:
        status_badge = "✅ PASS" if tc.get("status") == "PASS" else "❌ FAIL"
        md.append(
            f"| **{tc.get('test_id')}** | {tc.get('scenario_name')} | {status_badge} | "
            f"{tc.get('expected_result')} | {tc.get('actual_output')} |"
        )

    md.append("\n---\n")
    md.append("## Detailed Scenario Analyses\n")

    for tc in test_results:
        status_badge = "✅ PASS" if tc.get("status") == "PASS" else "❌ FAIL"
        md.append(f"### {tc.get('test_id')} — {tc.get('scenario_name')} ({status_badge})")
        md.append(f"- **Inputs:** {tc.get('inputs_summary')}")
        md.append(f"- **Expected Result:** {tc.get('expected_result')}")
        md.append(f"- **Actual Output:** {tc.get('actual_output')}")
        md.append(f"- **Academic Analysis:** {tc.get('analysis')}\n")

    md.append("---\n")
    md.append("*Report generated automatically by OS Deadlock Analysis Dashboard.*")

    return "\n".join(md)


def export_ai_usage_record_to_csv(ai_usage_rows: List[Dict[str, str]]) -> str:
    """Generate a CSV string of the student AI Usage Record."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "AI Tool Used",
        "Purpose",
        "Output Generated",
        "Student Verification",
    ])

    for row in ai_usage_rows:
        writer.writerow([
            row.get("AI Tool Used", ""),
            row.get("Purpose", ""),
            row.get("Output Generated", ""),
            row.get("Student Verification", ""),
        ])

    return output.getvalue()


def export_ai_usage_record_to_markdown(ai_usage_rows: List[Dict[str, str]]) -> str:
    """Generate a Markdown document of the AI Usage Record."""
    md = [
        "# AI Usage Record & Academic Integrity Statement",
        "**Activity:** Operating Systems IA Activity 2 — Resource Allocation and Deadlock Analysis  ",
        "**Institution:** MIT Academy of Engineering  ",
        "**Department:** Computer Department  ",
        "**Course:** Operating Systems Lab  ",
        "**Team Members:** Parth Wankhade, Aryan Agarwal, Vikas Choudhary, Sanket Kongare  ",
        "\n### Record Table\n",
        "| AI Tool Used | Purpose | Output Generated | Student Verification |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for row in ai_usage_rows:
        md.append(
            f"| {row.get('AI Tool Used', '')} | {row.get('Purpose', '')} | "
            f"{row.get('Output Generated', '')} | {row.get('Student Verification', '')} |"
        )

    md.append("\n### Team Declaration")
    md.append(
        "We (Parth Wankhade, Aryan Agarwal, Vikas Choudhary, Sanket Kongare) hereby declare that the analytical results, "
        "algorithm implementations, and explanations have been thoroughly verified against theoretical concepts from Silberschatz & Galvin's "
        "Operating Systems Principles. All code logic, test cases, and edge cases have been independently validated."
    )

    return "\n".join(md)
