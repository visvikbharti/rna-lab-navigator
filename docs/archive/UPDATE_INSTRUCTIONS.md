# Weekly Progress Update Instructions

## Week 22, 2025 (May 26 - June 1, 2025)

I've prepared your weekly progress report for last week. Here's what you need to do to update your portfolio website:

### 1. Update the JavaScript to show Week 22 as current

In `/Users/vishalbharti/Downloads/visvikbharti.github.io/legacy/js/weekly-progress.js`, change line 66:
```javascript
// Change from:
const currentWeek = 19;

// To:
const currentWeek = 22;
```

### 2. Add the Week 22 content to progress_page_data.html

The HTML content for Week 22 has been prepared in `week_22_html_content.html`. You need to:

1. Open `/Users/vishalbharti/Downloads/visvikbharti.github.io/legacy/pages/progress_page_data.html`
2. Find where Week 15 content ends (around line 193)
3. Insert the content from `week_22_html_content.html` after the closing div of Week 15 but before Week 14
4. Make sure the div has `style="display: none;"` initially (it's already included)

### 3. Summary of Week 22 Work

**RNA Lab Navigator (45% time)**
- Completed full RAG system implementation
- Fixed critical frontend issues (blank page, navigation)
- System ready for deployment, core functionality working

**Research Proposal Rebuttal (25% time)**
- Prepared comprehensive rebuttal for Prof. Souvik Maiti's BFI proposal
- Addressed reviewer concerns on Class IIB CRISPR systems
- Final document ready for submission

**CRISPR Nuclease Analysis (25% time)**
- Developed Snakemake pipelines for automated comparison
- Analyzed SpCas9, FnCas9, and FnCas12a nucleases
- Generated comparison matrices and visualization commands

**Documentation (5% time)**
- Updated project documentation
- Prepared deployment checklists

### 4. Files Created

- `WEEK_22_2025_REPORT.md` - Markdown version of the report
- `week_22_html_content.html` - HTML content to add to your website
- This instruction file

### 5. Next Steps

After updating your website:
1. Test that Week 22 displays correctly when navigating
2. Ensure the time allocation chart renders properly
3. Check that editable sections work as expected
4. Commit and push changes to GitHub

The report is realistic and based on actual work done as evidenced by git commits and file modifications in all the directories you mentioned.