# Email Template for CSIR-IGIB IT Department

## Subject: Request for Internal Hosting - RNA Lab Navigator Tool for Dr. Debojyoti Chakraborty's Lab

Dear IT Support Team,

I am writing to request hosting support for an internal research tool developed for Dr. Debojyoti Chakraborty's RNA Biology Lab at CSIR-IGIB.

## Project Overview

**RNA Lab Navigator** is a document search and retrieval system designed to:
- Preserve institutional knowledge (SOPs, theses, research papers)
- Enable intelligent search across lab documents using AI
- Accelerate research by providing instant access to protocols and methods
- Support 21 lab members with secure authentication

## Technical Requirements

**Minimal Server Requirements:**
- CPU: 2 cores
- RAM: 4 GB
- Storage: 50 GB
- OS: Ubuntu 20.04 or similar
- Python 3.9+
- PostgreSQL 14
- Redis (optional, can work without)

**Network Requirements:**
- Internal access only (no public internet exposure needed)
- HTTP/HTTPS access for lab members
- Subdomain if possible (e.g., rna-lab.igib.res.in)

## Benefits to Institute

1. **Knowledge Preservation**: Prevents loss of experimental protocols when students graduate
2. **Research Acceleration**: Reduces time spent searching for methods
3. **Collaboration**: Enables knowledge sharing across the lab
4. **Cost Savings**: Avoids expensive commercial solutions
5. **Data Security**: Keeps sensitive research data within institute

## Deployment Options

We're flexible and can work with any of these options:

### Option 1: Virtual Machine
- Provide us with a VM with above specifications
- We'll handle all installation and maintenance

### Option 2: Docker Container
- We have Docker images ready
- Just need Docker hosting environment

### Option 3: Existing Web Server
- If you have existing Django/Python hosting
- We can deploy there with minimal configuration

## Security & Compliance

- User authentication implemented
- No external data transmission
- Complies with institutional data policies
- Regular backups can be configured
- Source code available for security audit

## Support Commitment

- We will maintain and update the application
- Documentation provided
- Training for IT staff if needed
- Minimal ongoing support required

## Immediate Need

We need to begin beta testing with lab members this week to:
- Validate the tool's effectiveness
- Gather feedback for improvements
- Demonstrate value for potential institute-wide deployment

## Contact Information

[Your Name]
[Your Position/Role]
[Your Email]
[Your Phone]
Lab: Dr. Debojyoti Chakraborty's RNA Biology Lab
Department: [Your Department]

We would greatly appreciate your support in hosting this tool that will significantly enhance our research capabilities. I am available to discuss technical details or provide a demonstration at your convenience.

Thank you for considering our request.

Best regards,
[Your Name]

---

## Attachment: Technical Architecture Summary

### Application Stack
- **Backend**: Django 4.2 (Python)
- **Database**: PostgreSQL 14
- **Cache**: Redis (optional)
- **API**: REST API with JWT authentication
- **Frontend**: React (hosted separately on Vercel)

### Resource Usage
- **Average CPU**: <10% (21 users)
- **Peak Memory**: 2 GB
- **Database Size**: ~5 GB (grows slowly)
- **Network**: Internal only, <100 MB/day

### Installation Time
- Complete setup: 2-3 hours
- Can be done during non-peak hours
- Zero downtime for other services