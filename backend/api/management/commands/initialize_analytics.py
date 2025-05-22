"""
Django management command to initialize the analytics system.
Creates necessary database structures and populates with initial data.
"""

import datetime
import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from api.analytics.models import (
    SystemMetric,
    AuditEvent,
    UserActivityLog,
    DailyMetricAggregate,
    QueryTypeAggregate,
    SecurityEvent,
    SystemStatusLog
)


class Command(BaseCommand):
    help = "Initialize the analytics system with sample data for testing/development"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of historical data to generate'
        )
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of sample users to create (if not existing)'
        )
        parser.add_argument(
            '--with-sample-data',
            action='store_true',
            help='Generate sample data for metrics and events'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        create_users = options['users']
        with_sample_data = options['with_sample_data']
        
        self.stdout.write("Initializing analytics system...")
        
        # Create users if needed
        if User.objects.count() < create_users:
            self._create_sample_users(create_users)
        
        # Generate sample data if requested
        if with_sample_data:
            self._generate_sample_data(days)
            self._generate_aggregated_data(days)
            self.stdout.write(self.style.SUCCESS(f"Generated sample data for {days} days"))
        
        self.stdout.write(self.style.SUCCESS("Analytics system initialized successfully"))
    
    def _create_sample_users(self, user_count):
        """Create sample users for development/testing"""
        self.stdout.write("Creating sample users...")
        existing_count = User.objects.count()
        
        for i in range(1, user_count + 1):
            username = f"user{existing_count + i}"
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password="password123"
                )
                self.stdout.write(f"Created user: {username}")
        
        self.stdout.write(self.style.SUCCESS(f"Created {user_count} sample users"))
    
    def _generate_sample_data(self, days):
        """Generate sample data for development/testing"""
        self.stdout.write("Generating sample metrics and events...")
        
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.WARNING("No users found. Events will be anonymous."))
            users = [None]
        
        # Generate data for each day
        end_date = timezone.now()
        for day in range(days):
            date = end_date - datetime.timedelta(days=day)
            date_str = date.strftime('%Y-%m-%d')
            self.stdout.write(f"Generating data for {date_str}...")
            
            # Generate 20-100 queries per day
            query_count = random.randint(20, 100)
            for i in range(query_count):
                # Distribute throughout the day
                hour = random.randint(8, 20)  # Business hours
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                timestamp = date.replace(hour=hour, minute=minute, second=second)
                
                # Random user
                user = random.choice(users)
                
                # Create user activity for query
                response_time = random.randint(200, 3000)  # 200ms - 3s
                is_success = random.random() > 0.05  # 5% chance of failure
                
                # Create user activity log
                activity = UserActivityLog.objects.create(
                    user=user,
                    activity_type='query',
                    timestamp=timestamp,
                    ip_address=f"192.168.1.{random.randint(1, 254)}",
                    session_id=f"session_{random.randint(1000, 9999)}",
                    status='success' if is_success else 'failure',
                    metadata={
                        'query_text': self._get_random_query(),
                        'response_time': response_time,
                    }
                )
                
                # Create system metric for response time
                SystemMetric.objects.create(
                    metric_type='response_time',
                    value=response_time,
                    unit='ms',
                    timestamp=timestamp,
                    metadata={
                        'user_id': user.id if user else None,
                        'status_code': 200 if is_success else 500,
                    }
                )
                
                # Create system metric for CPU and memory usage (2 times per hour)
                if i % 30 == 0:
                    SystemMetric.objects.create(
                        metric_type='cpu_usage',
                        value=random.uniform(10, 80),
                        unit='%',
                        timestamp=timestamp
                    )
                    
                    SystemMetric.objects.create(
                        metric_type='memory_usage',
                        value=random.uniform(30, 90),
                        unit='%',
                        timestamp=timestamp
                    )
            
            # Generate 1-5 document uploads per day
            upload_count = random.randint(1, 5)
            for i in range(upload_count):
                hour = random.randint(8, 20)
                timestamp = date.replace(hour=hour)
                user = random.choice(users)
                
                UserActivityLog.objects.create(
                    user=user,
                    activity_type='document_upload',
                    timestamp=timestamp,
                    ip_address=f"192.168.1.{random.randint(1, 254)}",
                    session_id=f"session_{random.randint(1000, 9999)}",
                    status='success',
                    metadata={
                        'filename': f"document_{random.randint(1000, 9999)}.pdf",
                        'filesize': random.randint(100000, 10000000),
                    }
                )
            
            # Generate 0-3 security events per day
            security_event_count = random.randint(0, 3)
            for i in range(security_event_count):
                hour = random.randint(0, 23)
                timestamp = date.replace(hour=hour)
                event_type = random.choice([
                    'login_failure', 'access_denied', 'pii_detected', 
                    'security_scan', 'configuration_change'
                ])
                severity = random.choice(['info', 'warning', 'error', 'critical'])
                
                SecurityEvent.objects.create(
                    event_type=event_type,
                    user=random.choice(users),
                    timestamp=timestamp,
                    ip_address=f"192.168.1.{random.randint(1, 254)}",
                    description=f"Sample security event: {event_type}",
                    severity=severity,
                    is_resolved=random.random() > 0.3,  # 70% chance of being resolved
                )
            
            # Generate system status logs
            for component in ['api', 'db', 'vector_db', 'celery', 'redis', 'llm', 'embedding']:
                # 98% healthy, 1.5% degraded, 0.5% down
                status_roll = random.random()
                if status_roll > 0.98:
                    status = 'down'
                    message = f"{component} service is down"
                elif status_roll > 0.965:
                    status = 'degraded'
                    message = f"{component} service is experiencing degraded performance"
                else:
                    status = 'healthy'
                    message = f"{component} service is healthy"
                
                SystemStatusLog.objects.create(
                    component=component,
                    status=status,
                    timestamp=date.replace(hour=random.randint(0, 23)),
                    message=message,
                    details={'sample': True}
                )
    
    def _generate_aggregated_data(self, days):
        """Generate aggregated data based on raw metrics"""
        self.stdout.write("Generating aggregated metrics...")
        
        end_date = timezone.now().date()
        for day in range(days):
            date = end_date - datetime.timedelta(days=day)
            
            from api.analytics.aggregator import MetricsAggregator
            MetricsAggregator.aggregate_daily_metrics(date)
            MetricsAggregator.aggregate_query_types(date)
            
            self.stdout.write(f"Aggregated data for {date.strftime('%Y-%m-%d')}")
    
    def _get_random_query(self):
        """Generate a random sample query"""
        protocol_queries = [
            "How do I extract RNA using TRIzol?",
            "What's the protocol for western blotting?",
            "What temperature should I use for PCR annealing?",
            "Protocol for CRISPR guide RNA design?",
            "How long should I run the gel electrophoresis?",
        ]
        
        troubleshooting_queries = [
            "Why is my RNA yield so low?",
            "PCR not working, what could be wrong?",
            "Gel bands are smeared, how to fix?",
            "Western blot has high background, why?",
            "My CRISPR experiment has low efficiency, why?",
        ]
        
        reagent_queries = [
            "What's the composition of TBE buffer?",
            "How do I prepare a 10X PBS solution?",
            "What reagents do I need for qPCR?",
            "How to make LB media for bacteria?",
            "What's the shelf life of Taq polymerase?",
        ]
        
        theory_queries = [
            "How does CRISPR-Cas9 work?",
            "Explain the mechanism of RNA interference",
            "What are the steps in PCR?",
            "How do restriction enzymes cut DNA?",
            "Explain the principle of western blotting",
        ]
        
        all_queries = protocol_queries + troubleshooting_queries + reagent_queries + theory_queries
        return random.choice(all_queries)