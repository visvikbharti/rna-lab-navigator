"""
Django management command to run the security verification system.
"""

import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from api.security.verification import get_verifier


class Command(BaseCommand):
    help = 'Run security verification checks'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Output file for report (JSON format)'
        )
        parser.add_argument(
            '--details',
            action='store_true',
            help='Include detailed check results in the report'
        )
        parser.add_argument(
            '--check',
            type=str,
            help='Run a specific check by name'
        )
        
    def handle(self, *args, **options):
        output_file = options['output']
        include_details = options['details']
        specific_check = options['check']
        
        # Get verifier
        verifier = get_verifier()
        
        if specific_check:
            # Run specific check
            check_method = getattr(verifier, specific_check, None)
            if not check_method:
                self.stdout.write(self.style.ERROR(f"Check '{specific_check}' not found"))
                return
            
            self.stdout.write(self.style.SUCCESS(f"Running check: {specific_check}"))
            result = check_method()
            self.stdout.write(f"Status: {result['status']}")
            self.stdout.write(f"Message: {result['message']}")
            
            if result.get("details"):
                self.stdout.write("Details:")
                for key, value in result["details"].items():
                    self.stdout.write(f"  {key}: {value}")
        else:
            # Run all checks
            self.stdout.write(self.style.SUCCESS("Running security verification"))
            
            # Generate report
            report = verifier.generate_report(include_details=include_details)
            
            # Print report summary
            self._print_report_summary(report)
            
            # Save report to file if requested
            if output_file:
                self._save_report(report, output_file)
                self.stdout.write(self.style.SUCCESS(f"Report saved to {output_file}"))
    
    def _print_report_summary(self, report):
        """Print a summary of the security report"""
        self.stdout.write("\n===== SECURITY VERIFICATION SUMMARY =====\n")
        
        # Basic information
        self.stdout.write(f"Timestamp: {report['timestamp']}")
        
        # Overall status
        status = report['overall_status']
        if status == "pass":
            status_str = self.style.SUCCESS("PASS")
        elif status == "warning":
            status_str = self.style.WARNING("WARNING")
        elif status == "critical":
            status_str = self.style.ERROR("CRITICAL")
        else:
            status_str = self.style.WARNING(status.upper())
            
        self.stdout.write(f"Overall Status: {status_str}")
        
        # Summary
        summary = report['summary']
        
        passing_percent = summary['passing_percent']
        if passing_percent == 100:
            percent_str = self.style.SUCCESS(f"{passing_percent:.1f}%")
        elif passing_percent >= 80:
            percent_str = self.style.WARNING(f"{passing_percent:.1f}%")
        else:
            percent_str = self.style.ERROR(f"{passing_percent:.1f}%")
            
        self.stdout.write(f"Passing Checks: {summary['passing_checks']}/{summary['total_checks']} ({percent_str})")
        
        # Status counts
        self.stdout.write("\nCheck Results:")
        for status, count in summary['status_counts'].items():
            if status == "pass":
                status_str = self.style.SUCCESS(f"{status}: {count}")
            elif status == "warning":
                status_str = self.style.WARNING(f"{status}: {count}")
            elif status in ["critical", "error"]:
                status_str = self.style.ERROR(f"{status}: {count}")
            else:
                status_str = f"{status}: {count}"
                
            self.stdout.write(f"  {status_str}")
            
        # Recommendations
        if report['recommendations']:
            self.stdout.write("\nRecommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                self.stdout.write(f"  {i}. {rec}")
        else:
            self.stdout.write(self.style.SUCCESS("\nNo recommendations - all checks passed!"))
            
    def _save_report(self, report, output_file):
        """Save the report to a JSON file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)