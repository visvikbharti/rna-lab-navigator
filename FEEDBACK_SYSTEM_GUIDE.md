# RNA Lab Navigator Feedback System Guide

## Overview

The RNA Lab Navigator includes a comprehensive feedback system that helps improve answer quality over time. This guide explains how feedback works and where it goes.

## How Feedback Works

### 1. Submitting Feedback

When you receive an answer from the system, you can provide feedback in several ways:

- **Quick Feedback**: Click 👍 Helpful, 😐 Neutral, or 👎 Not Helpful
- **Detailed Feedback**: Expand the form to provide:
  - Specific issues (e.g., "Incorrect information", "Missing sources")
  - Detailed ratings for relevance, accuracy, completeness, clarity, and citations
  - Comments and suggestions
  - Incorrect sections and suggested corrections

### 2. Where Feedback Goes

All feedback is stored in the PostgreSQL database in the `EnhancedFeedback` table with the following information:

- **Query ID**: Links feedback to the specific query/answer
- **Rating**: thumbs_up, neutral, or thumbs_down
- **Category**: relevance, accuracy, completeness, clarity, citations, or general
- **Comments**: Free-text feedback
- **Specific Issues**: Tagged problems
- **Detailed Ratings**: 1-5 star ratings for various aspects
- **Timestamp**: When feedback was submitted
- **User Info**: Optional user identification

### 3. Feedback Visibility

The system now includes a **FeedbackTracker** component that shows:

- **Community Feedback Bar**: Visual representation of positive/neutral/negative feedback
- **Feedback Counts**: Number of each type of feedback
- **Recent Comments**: Actual user comments (anonymized)
- **Percentage Breakdown**: How the community rates this answer

### 4. How Feedback is Used

#### Immediate Uses:
1. **Answer Ranking**: Answers with better feedback are prioritized in future searches
2. **Model Selection**: The system learns which models provide better answers for specific query types
3. **Cache Management**: Poorly-rated cached answers can be refreshed

#### Analytics Dashboard (Admin):
- View feedback trends over time
- Identify problematic answer patterns
- Track improvement metrics
- Export feedback for analysis

#### Future Improvements:
1. **Automatic Re-ranking**: Answers with consistent negative feedback are deprioritized
2. **Model Fine-tuning**: Feedback data used to improve answer generation
3. **Source Quality**: Identify and prioritize high-quality document sources

### 5. Privacy and Anonymity

- Feedback can be submitted anonymously
- No personal information is required
- IP addresses are not stored
- Comments are reviewed before being shown publicly

### 6. Feedback Review Process

1. **Automated Review**: System flags feedback with specific keywords for review
2. **Admin Review**: Lab administrators can review feedback through the admin panel
3. **Action Items**: Feedback marked as "actioned" includes system improvements made

## Technical Implementation

### Backend Components:
- `/api/feedback/feedback/` - Main feedback endpoint
- `EnhancedFeedback` model - Stores all feedback data
- `FeedbackAnalysis` - Automated analysis of feedback patterns
- Admin dashboard at `/admin/api/enhancedfeedback/`

### Frontend Components:
- `EnhancedFeedbackForm` - Submission interface
- `FeedbackTracker` - Display existing feedback
- `FeedbackAnalyticsDashboard` - Admin analytics

### Database Schema:
```sql
EnhancedFeedback:
- id (UUID)
- query_id (ForeignKey)
- rating (choices: thumbs_up, neutral, thumbs_down)
- category (ForeignKey)
- comment (TextField)
- specific_issues (JSONField)
- relevance_rating (1-5)
- accuracy_rating (1-5)
- completeness_rating (1-5)
- clarity_rating (1-5)
- citation_rating (1-5)
- created_at (DateTime)
- status (pending, reviewed, actioned)
```

## Best Practices for Users

1. **Be Specific**: Instead of just clicking 👎, explain what was wrong
2. **Suggest Improvements**: If you know the correct answer, share it
3. **Rate Multiple Aspects**: Use the detailed ratings for comprehensive feedback
4. **Report Serious Issues**: Use specific issue tags for critical problems

## For Administrators

### Viewing Feedback:
1. Navigate to Django Admin (`/admin/`)
2. Go to "Enhanced Feedback" section
3. Filter by rating, date, or status
4. Export data for analysis

### Acting on Feedback:
1. Review feedback regularly (weekly recommended)
2. Mark feedback as "reviewed" after reading
3. Add "action notes" when making system improvements
4. Use feedback themes to identify patterns

### Analytics:
- Access the feedback analytics dashboard
- Monitor answer quality trends
- Identify top-performing and poorly-performing content
- Generate reports for stakeholders

## Future Enhancements

1. **Real-time Notifications**: Alert admins to critical feedback
2. **Automated Retraining**: Use feedback to retrain models
3. **Community Moderation**: Allow trusted users to help review feedback
4. **Feedback Rewards**: Gamification for quality feedback providers

## Troubleshooting

### Common Issues:

1. **"Failed to submit feedback"**
   - Check internet connection
   - Ensure query_id is present
   - Try refreshing the page

2. **Feedback not showing**
   - May take a moment to appear
   - Check if feedback was submitted successfully
   - Ensure you have the right permissions

3. **Can't see feedback analytics**
   - Admin permissions required
   - Contact system administrator

## Contact

For questions about the feedback system:
- Technical issues: Create a GitHub issue
- Feedback about feedback: Use the general feedback form
- Urgent matters: Contact the lab administrator