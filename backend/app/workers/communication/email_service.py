"""
Email service for sending briefings and notifications using Resend
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os

try:
    import resend
    resend.api_key = os.getenv("RESEND_API_KEY")
    if not resend.api_key:
        raise ValueError("RESEND_API_KEY environment variable is required")
except ImportError:
    resend = None

from ..core.types import EmailData, BriefingData, WeeklyPulseData

logger = logging.getLogger(__name__)


class EmailService:
    """Email service using Resend API"""
    
    def __init__(self):
        if not resend:
            raise ImportError("resend package is required. Install with: pip install resend")
        
        # resend.api_key is already set in the import block above
        self.resend = resend
        self.from_email = os.getenv("RESEND_FROM_EMAIL", "hello@pulseplan.app")
    
    async def send_email(self, email_data: EmailData) -> Dict[str, Any]:
        """Send email using Resend API"""
        try:
            response = self.resend.emails.send({
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
        # Extract data with fallbacks
        summary = data.get("summary", "Your briefing is ready!")
        tasks = data.get("todays_tasks", data.get("tasks", []))
        events = data.get("upcoming_events", data.get("events", []))
        recommendations = data.get("recommendations", [])
        weather = data.get("weather", {})
        
        # Convert agent data to expected format
        formatted_tasks = []
        if isinstance(tasks, list):
            for task in tasks:
                if isinstance(task, dict):
                    formatted_tasks.append({
                        "title": task.get("title", str(task)),
                        "due_time": task.get("due_date", task.get("due_time"))
                    })
                else:
                    formatted_tasks.append({"title": str(task)})
        
        formatted_events = []
        if isinstance(events, list):
            for event in events:
                if isinstance(event, dict):
                    formatted_events.append({
                        "title": event.get("title", str(event)),
                        "start_time": event.get("start_time", event.get("start"))
                    })
                else:
                    formatted_events.append({"title": str(event)})
        
        # Get first task
        first_task = formatted_tasks[0]["title"] if formatted_tasks else "No tasks scheduled"
        
        # Get meeting summary
        meetings = [event for event in formatted_events if "meeting" in event.get("title", "").lower()]
        meeting_summary = f"{len(meetings)} meetings scheduled" if meetings else "No meetings today"
        
        # Get free time blocks (simplified)
        free_time_blocks = data.get("free_time_blocks", "Morning: 9-11 AM, Afternoon: 2-4 PM")
        
        # Get top 3 priorities
        priorities = formatted_tasks[:3] if len(formatted_tasks) >= 3 else formatted_tasks
        priority_1 = priorities[0]["title"] if len(priorities) > 0 else "Focus on your most important work"
        priority_2 = priorities[1]["title"] if len(priorities) > 1 else "Review and plan tomorrow"
        priority_3 = priorities[2]["title"] if len(priorities) > 2 else "Take breaks and stay hydrated"
        
        # Get reschedule summary
        reschedule_summary = data.get("reschedule_summary", "No changes to your schedule today.")
        
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
            </style>
        </head>
        <body>
            <div class="container">
                <div class="greeting">Good morning, {user_name.split()[0] if user_name else 'there'}</div>
                
                <div>Here's your morning briefing</div>
                
                <div class="spacer"></div>
                
                <div><strong>{datetime.now().strftime("%A, %B %d, %Y")}</strong></div>
                
                <div class="spacer"></div>
                <div class="spacer"></div>
                
                <div class="section-title">Today's Schedule</div>
                
                <div class="spacer"></div>
                <div class="spacer"></div>
                
                <div class="content-block">
                    <strong>First task:</strong> {first_task}
                </div>
                
                <div class="spacer"></div>
                
                <div class="content-block">
                    <strong>Meetings:</strong> {meeting_summary}
                </div>
                
                <div class="spacer"></div>
                
                <div class="content-block">
                    <strong>Free time blocks:</strong> {free_time_blocks}
                </div>
                
                <div class="spacer"></div>
                
                <div style="font-style: italic;">(Want to restructure your day? Just ask!)</div>
                
                <div class="spacer"></div>
                <div class="spacer"></div>
                
                <div class="section-title">Top Priorities for Today</div>
                
                <div class="spacer"></div>
                <div class="spacer"></div>
                
                <div class="content-block">{priority_1}</div>
                
                <div class="spacer"></div>
                
                <div class="content-block">{priority_2}</div>
                
                <div class="spacer"></div>
                
                <div class="content-block">{priority_3}</div>
                
                <div class="spacer"></div>
                <div class="spacer"></div>
                
                <div class="section-title">Changes to Your Plan</div>
                
                <div class="content-block">{reschedule_summary}</div>
                <div style="font-style: italic;">(All changes are already reflected in your dashboard.)</div>
                
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
                @media (max-width: 480px) {{
                    .stats {{ grid-template-columns: 1fr; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
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