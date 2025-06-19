"""
Automated Paper Ingestion System - Start Simple, Scale Smart
This can be implemented TODAY and scaled up over time
"""

import feedparser
import requests
from datetime import datetime, timedelta
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import openai

# Configuration
BIORXIV_RSS_FEEDS = {
    'molecular_biology': 'http://connect.biorxiv.org/biorxiv_xml.php?subject=molecular_biology',
    'bioinformatics': 'http://connect.biorxiv.org/biorxiv_xml.php?subject=bioinformatics',
    'genetics': 'http://connect.biorxiv.org/biorxiv_xml.php?subject=genetics'
}

# Lab-specific keywords (customize these!)
LAB_KEYWORDS = [
    'RNA modification', 'RNA biology', 'CRISPR', 'Cas9', 'FnCas9',
    'DNA repair', 'NHEJ', 'HDR', 'gene editing', 'PAF1',
    'embryonic stem cells', 'RNA splicing', 'pseudouridine',
    'm6A', 'RNA methylation', 'CRISPR diagnostics'
]

# High-priority keywords that trigger immediate alerts
URGENT_KEYWORDS = [
    'FnCas9', 'FELUDA', 'RNA Lab IGIB', 'Chakraborty'  # Your lab's specific work
]

# Competing labs to monitor closely
COMPETITOR_AUTHORS = [
    'Jennifer Doudna', 'Feng Zhang', 'David Liu',  # Add your specific competitors
]

class PaperMonitor:
    """Simple but smart paper monitoring system"""
    
    def __init__(self):
        self.openai_client = openai
        self.openai_client.api_key = settings.OPENAI_API_KEY
    
    def fetch_recent_papers(self, hours=24):
        """Fetch papers from the last N hours"""
        all_papers = []
        
        for category, feed_url in BIORXIV_RSS_FEEDS.items():
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Parse publication date
                    pub_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %Z')
                    
                    # Only get recent papers
                    if datetime.now() - pub_date < timedelta(hours=hours):
                        paper = {
                            'title': entry.title,
                            'authors': entry.author,
                            'abstract': entry.summary,
                            'link': entry.link,
                            'doi': entry.get('dc_identifier', ''),
                            'published': pub_date,
                            'category': category,
                            'source': 'bioRxiv'
                        }
                        all_papers.append(paper)
                        
            except Exception as e:
                print(f"Error fetching {category}: {e}")
        
        return all_papers
    
    def score_relevance(self, paper):
        """Score paper relevance to lab's research"""
        score = 0
        reasons = []
        
        # Check title and abstract for keywords
        text = (paper['title'] + ' ' + paper['abstract']).lower()
        
        # Basic keyword matching
        for keyword in LAB_KEYWORDS:
            if keyword.lower() in text:
                score += 10
                reasons.append(f"Contains '{keyword}'")
        
        # Urgent keywords get higher score
        for keyword in URGENT_KEYWORDS:
            if keyword.lower() in text:
                score += 50
                reasons.append(f"URGENT: Contains '{keyword}'")
        
        # Check for competitor labs
        authors_text = paper['authors'].lower()
        for author in COMPETITOR_AUTHORS:
            if author.lower() in authors_text:
                score += 30
                reasons.append(f"Competitor lab: {author}")
        
        # Bonus for RNA + CRISPR combination
        if 'rna' in text and 'crispr' in text:
            score += 20
            reasons.append("RNA + CRISPR combination")
        
        paper['relevance_score'] = score
        paper['relevance_reasons'] = reasons
        
        return score
    
    def generate_smart_summary(self, paper):
        """Generate intelligent summary with lab context"""
        
        prompt = f"""
        Analyze this paper for a lab specializing in RNA biology, CRISPR, and gene editing:
        
        Title: {paper['title']}
        Authors: {paper['authors']}
        Abstract: {paper['abstract'][:1000]}...
        
        Provide:
        1. One-sentence summary of the key finding
        2. Why this matters to an RNA/CRISPR lab (2-3 sentences)
        3. One specific experiment they could try based on this paper
        4. Any potential contradictions with established knowledge
        
        Format as a brief, actionable summary.
        """
        
        try:
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Faster and cheaper for summaries
                messages=[
                    {"role": "system", "content": "You are a research advisor who provides actionable insights from papers."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            # Fallback to simple summary
            return f"Key finding: {paper['title']}\nRelevance: Contains keywords {', '.join(paper['relevance_reasons'])}"
    
    def process_papers(self, papers):
        """Process and categorize papers"""
        urgent = []
        relevant = []
        monitoring = []
        
        for paper in papers:
            score = self.score_relevance(paper)
            
            if score >= 80:
                paper['summary'] = self.generate_smart_summary(paper)
                urgent.append(paper)
            elif score >= 40:
                paper['summary'] = self.generate_smart_summary(paper)
                relevant.append(paper)
            elif score >= 20:
                monitoring.append(paper)
        
        return {
            'urgent': urgent,
            'relevant': relevant,
            'monitoring': monitoring,
            'total_processed': len(papers)
        }
    
    def format_email_digest(self, categorized_papers):
        """Format papers for email digest"""
        
        html_content = """
        <h2>🧬 RNA Lab Navigator - Paper Intelligence Report</h2>
        """
        
        if categorized_papers['urgent']:
            html_content += "<h3>🚨 URGENT - Immediate Attention Required</h3>"
            for paper in categorized_papers['urgent']:
                html_content += f"""
                <div style="border: 2px solid red; padding: 10px; margin: 10px 0;">
                    <h4>{paper['title']}</h4>
                    <p><b>Authors:</b> {paper['authors']}</p>
                    <p><b>Why this matters:</b> {', '.join(paper['relevance_reasons'])}</p>
                    <div style="background: #f0f0f0; padding: 10px; margin: 10px 0;">
                        {paper['summary']}
                    </div>
                    <a href="{paper['link']}">Read Full Paper</a>
                </div>
                """
        
        if categorized_papers['relevant']:
            html_content += "<h3>📚 Relevant to Your Research</h3>"
            for paper in categorized_papers['relevant'][:5]:  # Top 5
                html_content += f"""
                <div style="border: 1px solid #ccc; padding: 10px; margin: 10px 0;">
                    <h4>{paper['title']}</h4>
                    <p><b>Relevance:</b> {', '.join(paper['relevance_reasons'])}</p>
                    <p>{paper['summary']}</p>
                    <a href="{paper['link']}">Read More</a>
                </div>
                """
        
        html_content += f"""
        <hr>
        <p><i>Processed {categorized_papers['total_processed']} papers. 
        {len(categorized_papers['monitoring'])} additional papers are being monitored.</i></p>
        <p><a href="http://localhost:8000/papers/dashboard">View All in RNA Lab Navigator</a></p>
        """
        
        return html_content
    
    def send_notifications(self, categorized_papers):
        """Send appropriate notifications"""
        
        # Email digest for relevant papers
        if categorized_papers['urgent'] or categorized_papers['relevant']:
            send_mail(
                subject=f"🧬 Paper Alert: {len(categorized_papers['urgent'])} urgent, {len(categorized_papers['relevant'])} relevant papers",
                message="View in HTML",
                html_message=self.format_email_digest(categorized_papers),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['lab@example.com'],  # Configure your lab email
                fail_silently=False
            )
        
        # For urgent papers, could also send Slack/WhatsApp
        for paper in categorized_papers['urgent']:
            # Implement Slack/WhatsApp notification here
            print(f"URGENT ALERT: {paper['title']}")


# Celery Tasks
@shared_task
def check_new_papers():
    """Celery task to check for new papers"""
    monitor = PaperMonitor()
    
    # Fetch papers from last 24 hours
    papers = monitor.fetch_recent_papers(hours=24)
    
    # Process and categorize
    categorized = monitor.process_papers(papers)
    
    # Send notifications
    monitor.send_notifications(categorized)
    
    # Store in database for web viewing
    for category, papers_list in categorized.items():
        if category != 'total_processed':
            for paper in papers_list:
                # Store in your Paper model
                # Paper.objects.create(...)
                pass
    
    return f"Processed {categorized['total_processed']} papers"


@shared_task
def weekly_intelligence_report():
    """Generate weekly intelligence report with deeper analysis"""
    monitor = PaperMonitor()
    
    # Get papers from last week
    papers = monitor.fetch_recent_papers(hours=168)  # 7 days
    
    # More sophisticated analysis for weekly report
    # Include trend analysis, citation predictions, etc.
    
    # This is where you'd add the advanced intelligence features


# Quick test function
def test_paper_monitor():
    """Test the paper monitoring system"""
    monitor = PaperMonitor()
    
    # Fetch recent papers
    papers = monitor.fetch_recent_papers(hours=48)
    print(f"Found {len(papers)} papers")
    
    # Process them
    categorized = monitor.process_papers(papers)
    
    print(f"Urgent: {len(categorized['urgent'])}")
    print(f"Relevant: {len(categorized['relevant'])}")
    print(f"Monitoring: {len(categorized['monitoring'])}")
    
    # Show top urgent paper
    if categorized['urgent']:
        paper = categorized['urgent'][0]
        print(f"\nTop Urgent Paper:")
        print(f"Title: {paper['title']}")
        print(f"Score: {paper['relevance_score']}")
        print(f"Reasons: {paper['relevance_reasons']}")
        print(f"Summary: {paper['summary']}")


# Add to your celery beat schedule
# CELERY_BEAT_SCHEDULE = {
#     'check-new-papers': {
#         'task': 'api.papers.auto_ingest.check_new_papers',
#         'schedule': crontab(hour='*/6'),  # Every 6 hours
#     },
#     'weekly-intelligence': {
#         'task': 'api.papers.auto_ingest.weekly_intelligence_report',
#         'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Monday 9 AM
#     },
# }