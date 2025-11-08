#!/usr/bin/env python3
"""
Report Generator Module
Generates configuration validation reports and exports
"""

import os
import json
import csv
import xlsxwriter
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import structlog

logger = structlog.get_logger()

class ReportGenerator:
    """Generates various reports for configuration validation"""
    
    def __init__(self, reports_dir: str = "/app/reports"):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_validation_report(self, validation_results: List[Dict[str, Any]], 
                                 report_format: str = "json") -> str:
        """Generate validation report in specified format"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if report_format == "json":
                return self._generate_json_report(validation_results, timestamp)
            elif report_format == "csv":
                return self._generate_csv_report(validation_results, timestamp)
            elif report_format == "xlsx":
                return self._generate_xlsx_report(validation_results, timestamp)
            elif report_format == "html":
                return self._generate_html_report(validation_results, timestamp)
            else:
                raise ValueError(f"Unsupported report format: {report_format}")
                
        except Exception as e:
            logger.error("Failed to generate validation report", error=str(e))
            raise
    
    def _generate_json_report(self, results: List[Dict[str, Any]], timestamp: str) -> str:
        """Generate JSON report"""
        report_data = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_devices": len(results),
                "devices_with_drift": len([r for r in results if r.get("drift_detected", False)]),
                "devices_with_errors": len([r for r in results if r.get("status") == "error"])
            },
            "validation_results": results
        }
        
        report_file = self.reports_dir / f"validation_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info("JSON report generated", file=str(report_file))
        return str(report_file)
    
    def _generate_csv_report(self, results: List[Dict[str, Any]], timestamp: str) -> str:
        """Generate CSV report"""
        report_file = self.reports_dir / f"validation_report_{timestamp}.csv"
        
        with open(report_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                "Device", "Status", "Drift Detected", "Issues Count", 
                "Issues", "Timestamp"
            ])
            
            # Write data rows
            for result in results:
                issues_text = "; ".join(result.get("issues", []))
                writer.writerow([
                    result.get("device", ""),
                    result.get("status", ""),
                    result.get("drift_detected", False),
                    len(result.get("issues", [])),
                    issues_text,
                    result.get("timestamp", "")
                ])
        
        logger.info("CSV report generated", file=str(report_file))
        return str(report_file)
    
    def _generate_xlsx_report(self, results: List[Dict[str, Any]], timestamp: str) -> str:
        """Generate Excel report"""
        report_file = self.reports_dir / f"validation_report_{timestamp}.xlsx"
        
        workbook = xlsxwriter.Workbook(str(report_file))
        
        # Summary sheet
        summary_sheet = workbook.add_worksheet("Summary")
        summary_data = [
            ["Report Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Total Devices", len(results)],
            ["Devices with Drift", len([r for r in results if r.get("drift_detected", False)])],
            ["Devices with Errors", len([r for r in results if r.get("status") == "error"])],
            ["Success Rate", f"{len([r for r in results if r.get('status') == 'success'])}/{len(results)}"]
        ]
        
        for row, data in enumerate(summary_data):
            summary_sheet.write(row, 0, data[0])
            summary_sheet.write(row, 1, data[1])
        
        # Detailed results sheet
        details_sheet = workbook.add_worksheet("Validation Results")
        headers = ["Device", "Status", "Drift Detected", "Issues Count", "Issues", "Timestamp"]
        
        for col, header in enumerate(headers):
            details_sheet.write(0, col, header)
        
        for row, result in enumerate(results, 1):
            issues_text = "; ".join(result.get("issues", []))
            details_sheet.write(row, 0, result.get("device", ""))
            details_sheet.write(row, 1, result.get("status", ""))
            details_sheet.write(row, 2, result.get("drift_detected", False))
            details_sheet.write(row, 3, len(result.get("issues", [])))
            details_sheet.write(row, 4, issues_text)
            details_sheet.write(row, 5, result.get("timestamp", ""))
        
        workbook.close()
        
        logger.info("Excel report generated", file=str(report_file))
        return str(report_file)
    
    def _generate_html_report(self, results: List[Dict[str, Any]], timestamp: str) -> str:
        """Generate HTML report"""
        report_file = self.reports_dir / f"validation_report_{timestamp}.html"
        
        # Calculate summary statistics
        total_devices = len(results)
        devices_with_drift = len([r for r in results if r.get("drift_detected", False)])
        devices_with_errors = len([r for r in results if r.get("status") == "error"])
        success_rate = (total_devices - devices_with_errors) / total_devices * 100 if total_devices > 0 else 0
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Configuration Validation Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
                .summary-item {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; text-align: center; }}
                .summary-item.error {{ background-color: #ffe8e8; }}
                .summary-item.warning {{ background-color: #fff8e8; }}
                .summary-item.success {{ background-color: #e8f8e8; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .status-success {{ color: green; }}
                .status-error {{ color: red; }}
                .drift-yes {{ color: orange; font-weight: bold; }}
                .drift-no {{ color: green; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Configuration Validation Report</h1>
                <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
            
            <div class="summary">
                <div class="summary-item">
                    <h3>Total Devices</h3>
                    <p style="font-size: 24px; margin: 0;">{total_devices}</p>
                </div>
                <div class="summary-item {'error' if devices_with_errors > 0 else 'success'}">
                    <h3>Errors</h3>
                    <p style="font-size: 24px; margin: 0;">{devices_with_errors}</p>
                </div>
                <div class="summary-item {'warning' if devices_with_drift > 0 else 'success'}">
                    <h3>Drift Detected</h3>
                    <p style="font-size: 24px; margin: 0;">{devices_with_drift}</p>
                </div>
                <div class="summary-item {'success' if success_rate >= 90 else 'warning'}">
                    <h3>Success Rate</h3>
                    <p style="font-size: 24px; margin: 0;">{success_rate:.1f}%</p>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Device</th>
                        <th>Status</th>
                        <th>Drift Detected</th>
                        <th>Issues</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for result in results:
            status_class = "status-success" if result.get("status") == "success" else "status-error"
            drift_class = "drift-yes" if result.get("drift_detected", False) else "drift-no"
            issues_text = "; ".join(result.get("issues", []))
            
            html_content += f"""
                    <tr>
                        <td>{result.get("device", "")}</td>
                        <td class="{status_class}">{result.get("status", "")}</td>
                        <td class="{drift_class}">{result.get("drift_detected", False)}</td>
                        <td>{issues_text}</td>
                        <td>{result.get("timestamp", "")}</td>
                    </tr>
            """
        
        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        logger.info("HTML report generated", file=str(report_file))
        return str(report_file)
    
    def list_reports(self) -> List[Dict[str, Any]]:
        """List available reports"""
        try:
            reports = []
            
            for report_file in self.reports_dir.glob("validation_report_*"):
                stat = report_file.stat()
                reports.append({
                    "id": report_file.stem,
                    "filename": report_file.name,
                    "path": str(report_file),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            # Sort by creation time (newest first)
            reports.sort(key=lambda x: x["created"], reverse=True)
            
            return reports
            
        except Exception as e:
            logger.error("Failed to list reports", error=str(e))
            return []
    
    def get_report(self, report_id: str) -> Dict[str, Any]:
        """Get specific report content"""
        try:
            report_file = self.reports_dir / f"{report_id}.json"
            
            if not report_file.exists():
                # Try other formats
                for ext in ["csv", "xlsx", "html"]:
                    alt_file = self.reports_dir / f"{report_id}.{ext}"
                    if alt_file.exists():
                        return {
                            "id": report_id,
                            "filename": alt_file.name,
                            "path": str(alt_file),
                            "format": ext,
                            "content": alt_file.read_text() if ext in ["csv", "html"] else "Binary file"
                        }
                
                raise FileNotFoundError(f"Report {report_id} not found")
            
            with open(report_file, 'r') as f:
                content = json.load(f)
            
            return {
                "id": report_id,
                "filename": report_file.name,
                "path": str(report_file),
                "format": "json",
                "content": content
            }
            
        except Exception as e:
            logger.error("Failed to get report", report_id=report_id, error=str(e))
            raise

