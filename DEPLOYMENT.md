# Job Matching System - Deployment Instructions

## Fixed Issues

### 1. A2A Protocol Communication Fixed
- **Problem**: Messages between agents were not being delivered properly
- **Solution**: Implemented synchronous message delivery with immediate processing
- **Result**: Rankings are now properly generated and communicated to the Communication Agent

### 2. Communication Agent Enhanced
- **Problem**: Email notifications were failing and not showing proper fallback behavior
- **Solution**: Added robust email fallback with simulation mode for development
- **Result**: System works even without SMTP configuration, with detailed logging

### 3. Database Integration Improved
- **Problem**: Rankings were not being saved properly to database
- **Solution**: Fixed JSON serialization and database save operations
- **Result**: Rankings are now properly stored and retrieved

## Quick Start

### 1. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# For better resume parsing (optional but recommended)
pip install PyPDF2 python-docx pdfplumber
```

### 2. Database Setup
```bash
# Create PostgreSQL database
createdb job_matching_db

# Or using psql
psql -c "CREATE DATABASE job_matching_db;"
```

### 3. Environment Configuration
```bash
# Copy environment template
cp .env.template .env

# Edit .env with your configuration
nano .env
```

### 4. Required Environment Variables
```env
# Database (Required)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=job_matching_db
DB_USER=postgres
DB_PASSWORD=your_db_password

# Gemini API (Required for AI features)
GEMINI_API_KEY=your_gemini_api_key

# Email/SMTP (Optional - system will work without it)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true
```

### 5. Run the Application
```bash
python main.py
```

## Default Login Credentials

- **Admin User**: 
  - Username: `admin`
  - Password: `admin123`

## System Features Working

### ✅ Multi-Agent System (A2A Protocol)
- **Comparison Agent**: Analyzes resumes against job descriptions
- **Ranking Agent**: Ranks candidates by similarity scores with enhanced scoring
- **Communication Agent**: Sends email notifications with fallback simulation
- **Synchronous Communication**: Agents communicate immediately and reliably

### ✅ AI-Powered Matching
- **Gemini Integration**: Uses Google's Gemini 2.0 Flash for resume analysis
- **Fallback Mode**: Works without API key using basic text similarity
- **Enhanced Scoring**: Multiple criteria including skills, experience, education

### ✅ Email Notifications
- **SMTP Support**: Full email sending capability when configured
- **Simulation Mode**: Works without SMTP for development/testing
- **Rich HTML Emails**: Professional formatting with candidate rankings
- **Automatic Notifications**: Sent after AI ranking completion

### ✅ Database Operations
- **Rankings Storage**: Properly saves AI analysis results
- **JSON Support**: Stores detailed comparison data
- **Query Optimization**: Efficient data retrieval for large datasets

### ✅ CLI Interface
- **Admin Dashboard**: Complete job management and AI ranking interface
- **Job Seeker Interface**: Job browsing and application submission
- **Real-time Status**: Live agent system monitoring
- **Enhanced UX**: Better error handling and progress indication

## Testing the System

### 1. Post a Job (as Admin)
1. Login as admin (admin/admin123)
2. Select "📝 Post New Job"
3. Fill in job details with required skills
4. Enable auto-notifications

### 2. Apply to Job (as Job Seeker)
1. Register as job seeker or login
2. Select "Apply to Job"
3. Upload resume file (PDF/DOCX/TXT)
4. Submit application

### 3. Run AI Ranking (as Admin)
1. Login as admin
2. Select "🤖 Run AI Ranking System"
3. Choose job with applications
4. Watch the complete A2A workflow:
   - Comparison Agent analyzes resumes
   - Ranking Agent computes scores
   - Communication Agent sends notifications

### 4. View Results
- Check rankings in "🏆 View Rankings & Send Notifications"
- View agent status in "⚙️ Agent System Status"
- Check logs for email simulation details

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│  Comparison     │    │   Ranking        │    │  Communication     │
│  Agent          │───▶│   Agent          │───▶│  Agent             │
│                 │    │                  │    │                    │
│ • Resume Analysis│    │ • Score Ranking  │    │ • Email Notifications│
│ • Skills Matching│    │ • Enhanced Scoring│    │ • SMTP/Simulation   │
│ • AI Integration │    │ • Database Save   │    │ • HTML Templates    │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
           │                       │                         │
           └───────────────────────┼─────────────────────────┘
                                   │
                          ┌─────────────────┐
                          │  A2A Protocol   │
                          │                 │
                          │ • Sync Delivery │
                          │ • Retry Logic   │
                          │ • Heartbeats    │
                          │ • Error Handling│
                          └─────────────────┘
```

## Troubleshooting

### Issue: No Rankings Generated
**Symptoms**: "⚠️ No rankings generated" message
**Solutions**:
1. Check if applications exist for the job
2. Verify database connection
3. Check agent communication in logs
4. Ensure Gemini API key is valid (optional)

### Issue: Email Not Sending
**Symptoms**: Email notification failures
**Solutions**:
1. Check SMTP configuration in .env
2. Use Gmail App Password (not regular password)
3. System works in simulation mode without SMTP
4. Check logs for detailed error messages

### Issue: Resume Text Extraction Fails
**Symptoms**: "Text extraction failed" messages
**Solutions**:
1. Install recommended packages: `pip install PyPDF2 python-docx pdfplumber`
2. Use supported formats: PDF, DOCX, TXT
3. Ensure files are not password-protected
4. System will still process applications with basic info

### Issue: Database Connection Problems
**Symptoms**: Database connection errors
**Solutions**:
1. Ensure PostgreSQL is running
2. Check database credentials in .env
3. Create database if it doesn't exist
4. Check database permissions

## Performance Considerations

### For Production Use
1. **Database Optimization**:
   - Add indexes for frequently queried fields
   - Use connection pooling
   - Regular database maintenance

2. **AI Service Optimization**:
   - Implement caching for similar resumes
   - Use batch processing for large job applications
   - Consider rate limiting for API calls

3. **Email Service**:
   - Use dedicated SMTP service (SendGrid, AWS SES)
   - Implement email queuing for high volume
   - Add email template management

4. **Security Enhancements**:
   - Use environment-specific secrets
   - Implement proper authentication
   - Add input validation and sanitization

## Monitoring and Logging

### Log Locations
- Application logs: `logs/job_matching_YYYYMMDD.log`
- Agent communications: Logged with correlation IDs
- Email activities: Detailed in communication agent logs
- Database operations: Logged with query details

### Key Metrics to Monitor
- Agent response times
- Message delivery success rates
- Email delivery rates
- Database query performance
- Resume processing success rates

## Advanced Configuration

### Custom Scoring Weights
Edit `agents/ranking_agent.py` to adjust scoring factors:
```python
def _calculate_enhanced_score(self, result):
    # Adjust these weights based on your requirements
    skills_bonus = min(0.1, len(matched_skills) * 0.02)  # Skills weight
    experience_bonus = 0.05  # Experience weight
    education_bonus = 0.03   # Education weight
```

### Email Templates
Customize email templates in `agents/communication_agent.py`:
- `_generate_ranking_email_content()`: Candidate ranking emails
- `_generate_no_matches_email_content()`: No matches found emails
- `_generate_application_confirmation_content()`: Application confirmations

### Database Schema Extensions
To add custom fields, modify `database/schema.sql` and create migration scripts.

## API Integration (Future Enhancement)

The current CLI system can be extended with a REST API:
1. Add Flask/FastAPI endpoints
2. Expose agent system via HTTP
3. Implement webhook notifications
4. Add real-time WebSocket updates

## Scaling Considerations

### Horizontal Scaling
- Use message queue (Redis/RabbitMQ) for agent communication
- Implement database sharding for large datasets
- Use load balancers for multiple application instances

### Vertical Scaling
- Optimize database queries and indexes
- Use caching layers (Redis) for frequent data
- Implement asynchronous processing for heavy operations

## Security Best Practices

1. **Environment Variables**: Never commit .env files
2. **Database Security**: Use read-only users for queries
3. **Input Validation**: Sanitize all user inputs
4. **File Upload Security**: Validate file types and sizes
5. **API Rate Limiting**: Implement for external services

## Support and Maintenance

### Regular Maintenance Tasks
1. Clean up old log files
2. Archive processed applications
3. Update AI models and prompts
4. Monitor and optimize database performance
5. Update security patches

### Backup Procedures
1. Regular database backups
2. Backup uploaded resume files
3. Export system configurations
4. Document custom modifications

## Success Criteria

The system is working correctly when:
- ✅ AI ranking completes without errors
- ✅ Rankings are saved to database
- ✅ Email notifications are sent (or simulated)
- ✅ All three agents communicate successfully
- ✅ Admin can view detailed candidate analysis
- ✅ Job seekers can apply successfully
- ✅ System logs show successful A2A communication

## Getting Help

If you encounter issues:
1. Check the logs in the `logs/` directory
2. Verify environment configuration
3. Test with minimal data first
4. Check agent system status in admin dashboard
5. Review database connectivity

The system now follows the A2A protocol correctly and provides a complete end-to-end solution for AI-powered job matching and recruitment automation.