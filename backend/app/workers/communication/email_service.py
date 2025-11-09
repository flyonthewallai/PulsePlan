"""
Email service for sending briefings and notifications using Resend
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os

try:
    import resend
    from resend import Emails
    resend.api_key = os.getenv("RESEND_API_KEY")
    if not resend.api_key:
        raise ValueError("RESEND_API_KEY environment variable is required")
except ImportError:
    resend = None
    Emails = None

from ..core.types import EmailData, BriefingData, WeeklyPulseData

logger = logging.getLogger(__name__)


class EmailService:
    """Email service using Resend API"""
    
    def __init__(self):
        if not resend or not Emails:
            raise ImportError("resend package is required. Install with: pip install resend")
        
        # resend.api_key is already set in the import block above
        self.resend = resend
        self.from_email = os.getenv("RESEND_FROM_EMAIL", "hello@pulseplan.app")
    
    async def send_email(self, email_data: EmailData) -> Dict[str, Any]:
        """Send email using Resend API"""
        try:
            response = Emails.send({
                "from": email_data.from_email or self.from_email,
                "to": email_data.to,
                "subject": email_data.subject,
                "html": email_data.html,
            })
            
            if hasattr(response, 'error') and response.error:
                logger.error(f"Resend API error: {response.error}")
                return {
                    "success": False, 
                    "error": response.error.get("message", "Unknown email error")
                }
            
            logger.info(f"Email sent successfully to {email_data.to}")
            return {
                "success": True,
                "message_id": getattr(response, 'id', None)
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {email_data.to}: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_daily_briefing(
        self, 
        to: str, 
        user_name: str, 
        briefing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send daily briefing email"""
        try:
            html_content = self._generate_daily_briefing_html(user_name, briefing_data)
            
            email_data = EmailData(
                to=to,
                subject=f"Your Daily Briefing - {datetime.now().strftime('%B %d, %Y')}",
                html=html_content
            )
            
            return await self.send_email(email_data)
            
        except Exception as e:
            logger.error(f"Failed to send daily briefing to {to}: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_weekly_pulse(
        self, 
        to: str, 
        user_name: str, 
        pulse_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send weekly pulse email"""
        try:
            html_content = self._generate_weekly_pulse_html(user_name, pulse_data)
            
            email_data = EmailData(
                to=to,
                subject=f"Your Weekly Pulse - Week of {datetime.now().strftime('%B %d, %Y')}",
                html=html_content
            )
            
            return await self.send_email(email_data)
            
        except Exception as e:
            logger.error(f"Failed to send weekly pulse to {to}: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_daily_briefing_html(self, user_name: str, data: Dict[str, Any]) -> str:
        """Generate HTML for daily briefing email"""
        # Debug logging to see what data we're receiving
        logger.info(f"Email service received data keys: {list(data.keys())}")
        if "briefing" in data:
            logger.info(f"Briefing data keys: {list(data['briefing'].keys())}")
            if "content_sections" in data["briefing"]:
                logger.info(f"Content sections keys: {list(data['briefing']['content_sections'].keys())}")
        
        # Extract briefing content from workflow output
        # The content is nested in content_sections.synthesized_content
        content_sections = data.get("briefing", {}).get("content_sections", {})
        briefing_content = content_sections.get("synthesized_content", content_sections)

        # Get sections from workflow
        greeting = briefing_content.get("greeting", "Good morning!")
        email_summary = briefing_content.get("email_summary", "No email updates")
        calendar_overview = briefing_content.get("calendar_overview", "No calendar events")
        task_status = briefing_content.get("task_status", "No tasks")
        priority_items = briefing_content.get("priority_items", [])
        recommendations = briefing_content.get("recommendations", [])
        
        # Extract tasks due today from priority_items for better formatting
        # Priority items are dictionaries with 'title', 'due', 'priority' fields
        tasks_due_today = []
        for item in priority_items:
            if isinstance(item, dict):
                # Check if task is due today
                due_text = item.get('due', '')
                if 'today' in str(due_text).lower():
                    tasks_due_today.append(item.get('title', 'Untitled Task'))
            elif isinstance(item, str) and "due today" in item.lower():
                tasks_due_today.append(item)

        # Format tasks due today with bullets
        if tasks_due_today:
            tasks_formatted = "<br/>".join([f"• {task}" for task in tasks_due_today])
            task_status_formatted = f"Tasks due today:<br/>{tasks_formatted}"
        else:
            task_status_formatted = task_status  # Use the summary from task_status
        
        # Debug logging to see extracted values
        logger.info(f"Extracted email_summary: {email_summary}")
        logger.info(f"Extracted calendar_overview: {calendar_overview}")
        logger.info(f"Extracted task_status: {task_status}")
        logger.info(f"Extracted priority_items: {priority_items}")
        logger.info(f"Extracted recommendations: {recommendations}")
        
        # Format priority items - handle both dict and string formats
        def format_priority_item(item):
            if isinstance(item, dict):
                title = item.get('title', 'Untitled')
                due = item.get('due', '')
                priority = item.get('priority', 'medium')
                return f"{title} (Due: {due})"
            return str(item)

        priority_1 = format_priority_item(priority_items[0]) if len(priority_items) > 0 else "Focus on your most important work"
        priority_2 = format_priority_item(priority_items[1]) if len(priority_items) > 1 else "Review and plan tomorrow"
        priority_3 = format_priority_item(priority_items[2]) if len(priority_items) > 2 else "Take breaks and stay hydrated"
        
        # Format recommendations
        recommendation_text = ""
        if recommendations:
            recommendation_text = "• " + "\\n• ".join(recommendations)
        else:
            recommendation_text = "• Stay focused and productive\\n• Take regular breaks\\n• Review your goals"
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Morning Briefing</title>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    max-width: 600px; 
                    margin: 0 auto; 
                    padding: 20px; 
                    background-color: #ffffff;
                    color: #333333;
                    line-height: 1.6;
                }}
                .container {{ 
                    background-color: white; 
                    padding: 0;
                }}
                .greeting {{ 
                    font-size: 16px; 
                    margin-bottom: 20px;
                    font-weight: normal;
                }}
                .section-title {{ 
                    font-size: 16px; 
                    font-weight: 600; 
                    margin: 30px 0 15px 0;
                    color: #333333;
                }}
                .content-block {{ 
                    margin: 15px 0;
                    padding: 0;
                }}
                .signature {{ 
                    margin: 40px 0 20px 0;
                    font-style: normal;
                }}
                .footer {{ 
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    font-size: 14px;
                    color: #6b7280;
                }}
                .footer a {{ 
                    color: #4F46E5;
                    text-decoration: none;
                }}
                .spacer {{ 
                    margin: 20px 0;
                }}
                .logo {{ 
                    text-align: left;
                    margin-bottom: 30px;
                }}
                .logo img {{ 
                    width: 48px;
                    height: 48px;
                    border-radius: 12px;
                }}
                @media (max-width: 480px) {{
                    .logo {{ 
                        text-align: center;
                        margin-bottom: 20px;
                    }}
                    .logo img {{ 
                        width: 40px;
                        height: 40px;
                        border-radius: 10px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <img src="https://www.pulseplan.app/assets/logo.png" alt="PulsePlan - AI Productivity Assistant" />
                </div>
                <div class="greeting" style="font-size: 24px; font-weight: bold; margin-bottom: 10px;">Good morning, {user_name.split()[0] if user_name else 'there'}!</div>
                
                <div>Here's your morning briefing</div>
                
                <div class="spacer"></div>
                
                <div><strong>{datetime.now().strftime("%A, %B %d, %Y")}</strong></div>
                
                <div class="spacer"></div>
                <div class="spacer"></div>
                
                <div class="section-title">📅 Calendar Events</div>
                <div class="content-block">{calendar_overview}</div>
                <div style="border-top: 1px solid #e5e7eb; margin: 15px 0;"></div>
                
                <div class="spacer"></div>
                
                <div class="section-title">✅ Tasks</div>
                <div class="content-block">{task_status_formatted}</div>
                <div style="border-top: 1px solid #e5e7eb; margin: 15px 0;"></div>
                
                <div class="spacer"></div>
                <div class="spacer"></div>
                
                <div class="section-title">🎯 Top Priorities for Today</div>
                
                <div class="spacer"></div>
                <div class="spacer"></div>
                
                <div class="content-block">{priority_1}</div>
                
                <div class="spacer"></div>
                
                <div class="content-block">{priority_2}</div>
                
                <div class="spacer"></div>
                
                <div class="content-block">{priority_3}</div>
                
                <div style="border-top: 1px solid #e5e7eb; margin: 15px 0;"></div>
                
                <div class="spacer"></div>
                
                <div class="section-title">💡 Recommendations</div>
                <div class="content-block">{recommendation_text}</div>
                <div style="border-top: 1px solid #e5e7eb; margin: 15px 0;"></div>
                
                <div class="spacer"></div>
                
                <div class="section-title">📧 Email Summary</div>
                <div class="content-block">{email_summary}</div>
                
                <div class="spacer"></div>
                <div class="spacer"></div>
                
                <div>Need to make adjustments or ask a question? Just reply - I've got your day covered.</div>
                
                <div class="signature">- Pulse</div>
                
                <div class="spacer"></div>
                <div class="spacer"></div>
                
                <div class="footer">
                    <div>You asked Pulse for morning briefings.</div>
                    <div>Want to take a break? <a href="#">Update your preferences</a></div>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def _generate_weekly_pulse_html(self, user_name: str, data: Dict[str, Any]) -> str:
        """Generate HTML for weekly pulse email"""
        # Extract data with fallbacks
        completed_tasks = data.get("completed_tasks", 0)
        total_tasks = data.get("total_tasks", 0) 
        productivity_score = data.get("productivity_score", 0)
        achievements = data.get("achievements", [])
        recommendations = data.get("next_week_recommendations", data.get("recommendations", []))
        
        completion_rate = round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        
        # Build dynamic sections
        achievements_html = ""
        if achievements:
            achievements_html = '''
                    <div class="section">
                        <h3>This Week's Achievements</h3>
                        ''' + "".join([f"<div class='achievement'>{achievement}</div>" for achievement in achievements]) + '''
                    </div>
                    '''
        
        recommendations_html = ""
        if recommendations:
            recommendations_html = '''
                    <div class="section">
                        <h3>Next Week's Focus</h3>
                        <ul class="recommendations">
                            ''' + "".join([f"<li>{rec}</li>" for rec in recommendations]) + '''
                        </ul>
                    </div>
                    '''
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Weekly Pulse</title>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    max-width: 600px; 
                    margin: 0 auto; 
                    padding: 20px; 
                    background-color: #f8fafc;
                }}
                .container {{ background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                .header {{ 
                    background: linear-gradient(135deg, #7C3AED 0%, #EC4899 100%); 
                    color: white; 
                    padding: 30px 20px; 
                    text-align: center; 
                }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 600; }}
                .header p {{ margin: 10px 0 0; opacity: 0.9; }}
                .content {{ padding: 30px 20px; }}
                .stats {{ 
                    display: grid; 
                    grid-template-columns: 1fr 1fr 1fr; 
                    gap: 15px; 
                    margin: 25px 0; 
                }}
                .stat {{ 
                    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); 
                    padding: 20px; 
                    border-radius: 12px; 
                    text-align: center;
                    border: 1px solid #e0f2fe;
                }}
                .stat-number {{ 
                    font-size: 32px; 
                    font-weight: 700; 
                    color: #7C3AED; 
                    margin: 0;
                }}
                .stat-label {{ 
                    font-size: 14px; 
                    color: #6b7280; 
                    margin: 5px 0 0;
                }}
                .section {{ margin: 25px 0; }}
                .section h3 {{ 
                    color: #1f2937; 
                    font-size: 18px; 
                    margin: 0 0 15px; 
                    padding-bottom: 8px;
                    border-bottom: 2px solid #e5e7eb; 
                }}
                .achievement {{ 
                    background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%); 
                    padding: 15px; 
                    margin: 10px 0; 
                    border-radius: 8px;
                    border-left: 4px solid #10b981; 
                }}
                .recommendations {{ list-style: none; padding: 0; }}
                .recommendations li {{ 
                    background: #fef3c7; 
                    padding: 12px 15px; 
                    margin: 8px 0; 
                    border-radius: 6px;
                    border-left: 3px solid #f59e0b;
                }}
                .footer {{ 
                    text-align: center; 
                    color: #6b7280; 
                    font-size: 14px; 
                    margin-top: 30px;
                    padding: 20px;
                    background: #f9fafb;
                    border-top: 1px solid #e5e7eb;
                }}
                .cta {{ 
                    text-align: center; 
                    margin: 25px 0; 
                }}
                .cta a {{ 
                    background: #7C3AED; 
                    color: white; 
                    padding: 12px 24px; 
                    text-decoration: none; 
                    border-radius: 6px;
                    font-weight: 500;
                }}
                .logo {{ 
                    text-align: left;
                    margin-bottom: 20px;
                }}
                .logo img {{ 
                    width: 40px;
                    height: 40px;
                    border-radius: 10px;
                }}
                @media (max-width: 480px) {{
                    .stats {{ grid-template-columns: 1fr; }}
                    .logo {{ 
                        text-align: center;
                        margin-bottom: 15px;
                    }}
                    .logo img {{ 
                        width: 36px;
                        height: 36px;
                        border-radius: 8px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <img src="https://www.pulseplan.app/assets/logo.png" alt="PulsePlan - AI Productivity Assistant" />
                </div>
                <div class="header">
                    <h1>Weekly Pulse</h1>
                    <p>Your productivity summary for {user_name}</p>
                    <p>Week of {datetime.now().strftime("%B %d, %Y")}</p>
                </div>
                
                <div class="content">
                    <div class="stats">
                        <div class="stat">
                            <div class="stat-number">{completed_tasks}</div>
                            <div class="stat-label">Tasks Completed</div>
                        </div>
                        <div class="stat">
                            <div class="stat-number">{completion_rate}%</div>
                            <div class="stat-label">Completion Rate</div>
                        </div>
                        <div class="stat">
                            <div class="stat-number">{productivity_score:.1f}</div>
                            <div class="stat-label">Productivity Score</div>
                        </div>
                    </div>
                    
                    {achievements_html}
                    
                    {recommendations_html}
                    
                    <div class="cta">
                        <a href="https://app.pulseplan.com" style="color: white;">View Full Analytics</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>Keep up the great work!</strong></p>
                    <p>PulsePlan - Your AI-Powered Productivity Assistant</p>
                    <p style="font-size: 12px; margin-top: 10px;">
                        You're receiving this because you have weekly pulse enabled. 
                        <a href="#" style="color: #7C3AED;">Manage preferences</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        '''


# Global email service instance
_email_service: Optional[EmailService] = None

def get_email_service() -> EmailService:
    """Get global email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service