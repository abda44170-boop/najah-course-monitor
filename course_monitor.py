import requests
import smtplib
import time
import asyncio
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from datetime import datetime
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NajahCourseMonitor:
    def __init__(self, email_config, session_cookies):
        self.email_config = email_config
        self.session_cookies = session_cookies
        self.notified_sections = set()  # Track what we've already notified about
        
    def send_email(self, subject, body):
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['recipient_email']
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Gmail SMTP setup
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['app_password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['sender_email'], 
                          self.email_config['recipient_email'], text)
            server.quit()
            
            logger.info(f"✅ Email sent successfully: {subject}")
            
        except Exception as e:
            logger.error(f"❌ Error sending email: {e}")
    
    def check_course_sections(self, course_code, target_sections):
        """Check specific sections of a course for availability"""
        try:
            # Set up the request headers and data exactly like your browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://zajelbs.najah.edu',
                'Referer': 'https://zajelbs.najah.edu/servlet/materials',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1'
            }
            
            # Form data from your request
            data = {
                'b': 'num',
                'var': course_code,
                'flag': 'done'
            }
            
            # Make the POST request
            response = requests.post(
                'https://zajelbs.najah.edu/servlet/materials',
                headers=headers,
                cookies=self.session_cookies,
                data=data,
                timeout=15
            )
            
            response.raise_for_status()
            
            # Parse the HTML response
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the table with course sections
            available_sections = []
            
            # Look for table rows containing section information
            rows = soup.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:  # Make sure it's a data row
                    
                    # The section number is usually in the 3rd cell (index 2)
                    section_cell = None
                    section_num = None
                    
                    if len(cells) >= 3:
                        cell_text = cells[2].get_text(strip=True)
                        # Look for pattern like "2/10636594"
                        if f"/{course_code}" in cell_text:
                            section_match = re.search(r'(\d+)/' + str(course_code), cell_text)
                            if section_match:
                                section_num = section_match.group(1)
                                section_cell = cell_text
                            
                            # Check if this is one of our target sections
                            if section_num in target_sections:
                                # Check availability status
                                is_available = self.check_section_availability(row, section_num, course_code)
                                
                                if is_available:
                                    available_sections.append({
                                        'section': section_num,
                                        'course_code': course_code,
                                        'full_section': f"{section_num}/{course_code}",
                                        'row_data': self.extract_section_info(row)
                                    })
            
            return available_sections
            
        except Exception as e:
            logger.error(f"❌ Error checking course {course_code}: {e}")
            return []
    
    def check_section_availability(self, row, section_num, course_code):
        """
        Check if a section is available based on the status icon
        open.gif = Available, close.gif = Closed, stop.gif = Stopped
        """
        # Look for the status image in the first cell
        images = row.find_all('image')  # Note: it's <image> not <img> in this HTML
        
        for img in images:
            src = img.get('src', '').lower()
            
            # Check the specific status icons
            if 'open.gif' in src:
                return True  # Section is OPEN
            elif 'close.gif' in src:
                return False  # Section is CLOSED
            elif 'stop.gif' in src:
                return False  # Section is STOPPED/CANCELLED
        
        # If no status image found, assume closed for safety
        return False
    
    def extract_section_info(self, row):
        """Extract useful information from the section row based on An-Najah structure"""
        cells = row.find_all('td')
        info = {}
        
        try:
            if len(cells) >= 11:  # Based on the HTML structure you provided
                info['course_name'] = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                info['credit_hours'] = cells[4].get_text(strip=True) if len(cells) > 4 else ''
                info['days'] = cells[5].get_text(strip=True) if len(cells) > 5 else ''
                info['time'] = cells[6].get_text(strip=True) if len(cells) > 6 else ''
                info['room'] = cells[7].get_text(strip=True) if len(cells) > 7 else ''
                info['building'] = cells[8].get_text(strip=True) if len(cells) > 8 else ''
                info['instructor'] = cells[10].get_text(strip=True) if len(cells) > 10 else ''
        except Exception as e:
            logger.warning(f"⚠️ Error extracting section info: {e}")
                
        return info
    
    def monitor_courses(self, courses_to_monitor):
        """Monitor multiple courses and their specific sections - Railway 24/7 version"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"🔍 Checking courses at {timestamp}")
        
        any_new_sections_found = False
        
        for course in courses_to_monitor:
            course_code = course['course_code']
            target_sections = course['sections']
            course_name = course['name']
            
            logger.info(f"  📚 Checking {course_name} ({course_code}) - sections: {', '.join(target_sections)}")
            
            available_sections = self.check_course_sections(course_code, target_sections)
            
            for section_info in available_sections:
                section_key = f"{course_code}-{section_info['section']}"
                
                # Only send email if this is a NEW availability (not already notified)
                if section_key not in self.notified_sections:
                    any_new_sections_found = True
                    self.notified_sections.add(section_key)
                    
                    subject = f"🎉 Course Available! {course_name} Section {section_info['section']}"
                    
                    # Build detailed email body
                    body = f"""
🚨 COURSE SECTION IS NOW AVAILABLE! 🚨

📚 Course: {course_name}
🏷️  Course Code: {course_code}
📍 Section: {section_info['full_section']}

"""
                    
                    # Add section details if available
                    if section_info['row_data']:
                        if section_info['row_data'].get('instructor'):
                            body += f"👨‍🏫 Instructor: {section_info['row_data']['instructor']}\n"
                        if section_info['row_data'].get('time'):
                            body += f"⏰ Time: {section_info['row_data']['time']}\n"
                        if section_info['row_data'].get('days'):
                            body += f"📅 Days: {section_info['row_data']['days']}\n"
                        if section_info['row_data'].get('room'):
                            body += f"🏛️  Room: {section_info['row_data']['room']}\n"
                        if section_info['row_data'].get('building'):
                            body += f"🏢 Building: {section_info['row_data']['building']}\n"
                    
                    body += f"""

🚀 REGISTER NOW: https://zajelbs.najah.edu/servlet/materials

⚡ Detected at {timestamp}
🤖 This is an automated alert from your 24/7 course monitor

Good luck! 🍀
"""
                    
                    self.send_email(subject, body)
                    logger.info(f"  ✅ NEW availability found: Section {section_info['section']} - EMAIL SENT!")
                else:
                    logger.info(f"  📧 Section {section_info['section']} still available (already notified)")
            
            if not available_sections:
                # Remove this course's sections from notified set if none are available
                sections_to_remove = [key for key in self.notified_sections if key.startswith(f"{course_code}-")]
                for section_key in sections_to_remove:
                    self.notified_sections.remove(section_key)
                
                logger.info(f"  ❌ No target sections available for {course_name}")
        
        if any_new_sections_found:
            logger.info(f"🎉 Found NEW available sections! Email notifications sent.")
        else:
            logger.info(f"😴 No new sections available. Next check in 30 seconds.")

async def main():
    """Main async function that runs the monitoring loop"""
    logger.info("🚀 Najah Course Monitor - RAILWAY 24/7 VERSION")
    logger.info("=" * 60)
    logger.info("🔄 Running every 30 seconds until manually stopped")
    logger.info("=" * 60)
    
    # Get configuration from environment variables
    email_config = {
        'sender_email': os.getenv('SENDER_EMAIL', 'aloordabd2017@gmail.com'),
        'recipient_email': os.getenv('RECIPIENT_EMAIL', 'aloordabd2017@gmail.com'),
        'app_password': os.getenv('EMAIL_APP_PASSWORD', 'ndhz nlnw wocr tflt')
    }
    
    # Get session cookies from environment variables
    session_cookies = {
        'cf_clearance': os.getenv('CF_CLEARANCE', '.BJHakpQX8hDMHLSX12GcEDzlk7oblk4aMMlp5zk.I0-1749470680-1.2.1.1-6BIdLud3zAcj8teqWOznQMactmjVvgyvk0JmSGnGeFaGTtNQvNvSGUI6.2z624r4ZklwS0diT0GP7EEhi0tH8HKdOHFQk9AGrEfSo82cVHgqE9T6kwGXhnkcKtMELS4wQ7h3ZgSJcAy6shYME1koA_YRQGrn_3EEaipCKDv7RZihZ2eMjSzT0LnEnsfYDPRk0h0HJrhzMSLUTejpqWHuCWXJ2ZXUyq7ZOz7dyGvlGMefr3trY35MQiaV5w2r0hCVxYOjbax9cdErSKFlGx8CueHl5Eby76r42FRsm07cGAXEOQa8MAbUX19FZe1tjS4l4HX36WGK_YBOrAQQigxEQFQnhxnhXYCDEZNj7Xv4RJyfpg2rGOYAkCJ9K9SUUZJz'),
        '_ga_WZ87130T4C': os.getenv('GA_WZ87130T4C', 'GS1.1.1749160412.6.1.1749163484.48.0.0'),
        '_ga': os.getenv('GA', 'GA1.2.1633134789.1745908662'),
        '_ga_QHQT49TPWM': os.getenv('GA_QHQT49TPWM', 'GS1.1.1747221497.1.1.1747221858.0.0.0'),
        'cookiesession1': os.getenv('COOKIESESSION1', '678B2874131365EB8BBD4B0A96806B4F')
    }
    
    # Courses to monitor with specific sections
    courses_to_monitor = [
        {
            'name': 'مختبر تصميم دوائر رقمية 2ة',  # Networks Lab 
            'course_code': '10636391',
            'sections': ['1']
        },
        {
            'name': 'مختبر تصميم دوائر رقمية 2',  # AI
            'course_code': '10636391',
            'sections': ['2']
        },
        {
            'name': 'مختبر تصميم دوائر رقمية 2',  # Microprocessors Lab
            'course_code': '10636391',
            'sections': ['3']
        },{
            'name': 'مختبر المعالجات الدقيقة',  # Networks Lab 
            'course_code': '10636392',
            'sections': ['5']
        },
        {
            'name': 'مختبر المعالجات الدقيقة',  # AI
            'course_code': '10636392',
            'sections': ['4']
        },
        {
            'name': 'مختبر المعالجات الدقيقة',  # Microprocessors Lab
            'course_code': '10636392',
            'sections': ['3']
        }
    ]
    
    logger.info(f"📧 Email notifications: {email_config['recipient_email']}")
    logger.info("📚 Monitoring courses:")
    for course in courses_to_monitor:
        logger.info(f"   • {course['name']} ({course['course_code']}) - Sections: {', '.join(course['sections'])}")
    logger.info("=" * 60)
    
    # Create monitor instance
    monitor = NajahCourseMonitor(email_config, session_cookies)
    
    # Run monitoring loop
    while True:
        try:
            monitor.monitor_courses(courses_to_monitor)
            logger.info("⏳ Waiting 30 seconds until next check...")
            await asyncio.sleep(30)  # Wait 30 seconds
            
        except KeyboardInterrupt:
            logger.info("👋 Monitor stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Unexpected error in main loop: {e}")
            logger.info("⏳ Waiting 30 seconds before retry...")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
