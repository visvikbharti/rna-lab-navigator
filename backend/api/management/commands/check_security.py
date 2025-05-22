"""
Django management command to check security headers and configuration.
"""

import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from api.security.headers import SecurityHeadersReporter


class Command(BaseCommand):
    help = 'Check security headers and configuration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='URL to check (defaults to SITE_URL setting)'
        )
        parser.add_argument(
            '--observatory',
            action='store_true',
            help='Include Mozilla Observatory scan'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file for report (JSON format)'
        )
        
    def handle(self, *args, **options):
        url = options['url'] or getattr(settings, 'SITE_URL', 'http://localhost:8000')
        include_observatory = options['observatory']
        output_file = options['output']
        
        self.stdout.write(self.style.SUCCESS(f"Checking security headers for {url}"))
        
        # Create reporter and generate report
        reporter = SecurityHeadersReporter(url)
        report = reporter.generate_report(include_observatory)
        
        # Print report summary
        self._print_report_summary(report)
        
        # Save report to file if requested
        if output_file:
            self._save_report(report, output_file)
            self.stdout.write(self.style.SUCCESS(f"Report saved to {output_file}"))
    
    def _print_report_summary(self, report):
        """Print a summary of the security report"""
        self.stdout.write("\n===== SECURITY CHECK SUMMARY =====\n")
        
        # Basic information
        self.stdout.write(f"URL: {report['site_url']}")
        self.stdout.write(f"Timestamp: {report['timestamp']}")
        
        # Header check
        header_check = report['header_check']
        if header_check['success']:
            self.stdout.write(f"\nSecurity Score: {header_check['security_score']}/100")
            
            # Color code based on score
            if header_check['security_score'] >= 80:
                status = self.style.SUCCESS("GOOD")
            elif header_check['security_score'] >= 50:
                status = self.style.WARNING("MODERATE")
            else:
                status = self.style.ERROR("POOR")
                
            self.stdout.write(f"Status: {status}")
            
            # Missing headers
            if header_check['missing_headers']:
                self.stdout.write("\nMissing Security Headers:")
                for header in header_check['missing_headers']:
                    self.stdout.write(f"  - {header}")
            else:
                self.stdout.write(self.style.SUCCESS("\nAll recommended security headers present!"))
                
            # CSP issues
            if header_check['unsafe_csp']:
                self.stdout.write("\nUnsafe Content-Security-Policy Directives:")
                for directive in header_check['unsafe_csp']:
                    self.stdout.write(f"  - {directive}")
        else:
            self.stdout.write(self.style.ERROR(f"\nError checking headers: {header_check.get('error')}"))
            
        # Observatory scan
        if 'observatory' in report:
            observatory = report['observatory']
            if observatory['success']:
                self.stdout.write("\n===== MOZILLA OBSERVATORY RESULTS =====\n")
                self.stdout.write(f"Score: {observatory['observatory_score']}/100")
                self.stdout.write(f"Grade: {observatory['observatory_grade']}")
            else:
                self.stdout.write(self.style.ERROR(f"\nError with Observatory scan: {observatory.get('error')}"))
                
        # Recommendations
        self._print_recommendations(report)
    
    def _print_recommendations(self, report):
        """Print security recommendations based on the report"""
        self.stdout.write("\n===== RECOMMENDATIONS =====\n")
        
        recommendations = []
        header_check = report['header_check']
        
        # Add recommendations based on missing headers
        if header_check['success']:
            for header in header_check.get('missing_headers', []):
                if header == "Content-Security-Policy":
                    recommendations.append(
                        "Add a Content-Security-Policy header to restrict resource loading"
                    )
                elif header == "Strict-Transport-Security":
                    recommendations.append(
                        "Add a Strict-Transport-Security header to enforce HTTPS"
                    )
                elif header == "X-Content-Type-Options":
                    recommendations.append(
                        "Add X-Content-Type-Options: nosniff to prevent MIME type sniffing"
                    )
                elif header == "X-Frame-Options":
                    recommendations.append(
                        "Add X-Frame-Options: DENY to prevent clickjacking"
                    )
                elif header == "Permissions-Policy":
                    recommendations.append(
                        "Add a Permissions-Policy header to restrict browser features"
                    )
                    
            # Check for unsafe CSP directives
            if header_check.get('unsafe_csp'):
                recommendations.append(
                    "Remove 'unsafe-inline' and 'unsafe-eval' from Content-Security-Policy"
                )
                
            # Check HSTS
            if not header_check.get('has_hsts'):
                recommendations.append(
                    "Add a Strict-Transport-Security header to enforce HTTPS"
                )
                
        # Print recommendations
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                self.stdout.write(f"{i}. {rec}")
        else:
            self.stdout.write(self.style.SUCCESS("No specific recommendations - security configuration looks good!"))
    
    def _save_report(self, report, output_file):
        """Save the report to a JSON file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)