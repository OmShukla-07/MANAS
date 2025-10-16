"""
Crisis Detection Service for MANAS Platform
Detects crisis keywords and triggers immediate interventions
"""

import logging
import re
from datetime import datetime
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from crisis.models import CrisisAlert, CrisisType

User = get_user_model()
logger = logging.getLogger(__name__)


class CrisisDetectionService:
    """
    Service for detecting crisis situations in chat messages
    """
    
    # Crisis keywords categorized by severity - Expanded with Hindi/Hinglish support
    SEVERE_CRISIS_KEYWORDS = [
        # Suicide ideation
        r'\b(kill myself|end my life|suicide|suicidal|want to die|going to die)\b',
        r'\b(no reason to live|better off dead|can\'t go on|ending it all)\b',
        r'\b(take my life|don\'t want to live|tired of living|done with life)\b',
        r'\b(goodbye world|this is my last|final message|leaving forever)\b',
        
        # Self-harm
        r'\b(cut myself|hurt myself|harm myself|self harm|self-harm|cutting)\b',
        r'\b(slash my wrists|slit my wrists|hurt my body)\b',
        
        # Methods
        r'\b(overdose|pills to end|jump off|hang myself|hanging myself)\b',
        r'\b(knife to|gun to|poison myself|drown myself)\b',
        
        # Final goodbyes
        r'\b(goodbye forever|this is goodbye|final goodbye|suicide note|last words)\b',
        r'\b(saying goodbye|won\'t see you again|this is the end)\b',
        
        # Direct expressions
        r'\b(kill me|death wish|ready to die|planning suicide)\b',
        r'\b(end it all|finish it|can\'t live|won\'t survive)\b',
        
        # Hindi/Hinglish terms
        r'\b(marna chahta|mar jaana chahta|zinda nahi rehna|khud ko khatam)\b',
        r'\b(suicide kar lunga|maar dalunga khud ko)\b',
    ]
    
    MODERATE_CRISIS_KEYWORDS = [
        # Hopelessness
        r'\b(hopeless|no hope|nothing matters|pointless|worthless|useless)\b',
        r'\b(life is meaningless|no purpose|empty inside|hollow)\b',
        
        # Despair
        r'\b(give up|giving up|can\'t take it|too much pain|unbearable)\b',
        r'\b(can\'t cope|breaking down|falling apart|lost all hope)\b',
        
        # Isolation
        r'\b(everyone hates me|nobody cares|all alone|so alone|completely alone)\b',
        r'\b(no one understands|nobody loves me|isolated|lonely|abandoned)\b',
        
        # Self-deprecation
        r'\b(want to disappear|wish I was dead|wish I wasn\'t born)\b',
        r'\b(burden to everyone|better without me|shouldn\'t exist)\b',
        r'\b(hate myself|disgusted with myself|failure|worthless person)\b',
        
        # Desperation
        r'\b(can\'t go on|can\'t continue|can\'t handle|too difficult)\b',
        r'\b(want it to stop|make it stop|end the pain|escape this)\b',
        
        # Academic/social pressure
        r'\b(failed everything|ruined my life|destroyed everything|no future)\b',
        r'\b(disappointed everyone|let everyone down|can\'t face anyone)\b',
        
        # Hindi/Hinglish terms
        r'\b(koi umeed nahi|sab khatam|jeena mushkil|bardaasht nahi)\b',
        r'\b(koi parwaah nahi|akela hun|koi nahi samajhta)\b',
    ]
    
    LOW_CRISIS_KEYWORDS = [
        # Distress
        r'\b(depressed|very sad|extremely sad|feeling down|really low)\b',
        r'\b(anxious|stressed out|overwhelmed|can\'t sleep|sleepless)\b',
        r'\b(panic attack|anxiety attack|breaking point|edge)\b',
        
        # Emotional pain
        r'\b(hurting so much|in pain|suffering|aching|broken)\b',
        r'\b(crying all day|can\'t stop crying|tears won\'t stop)\b',
        
        # Warning signs
        r'\b(losing interest|don\'t care anymore|numb|empty|void)\b',
        r'\b(tired of trying|exhausted|drained|burnt out)\b',
    ]
    
    # Compile regex patterns for efficiency
    SEVERE_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in SEVERE_CRISIS_KEYWORDS]
    MODERATE_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in MODERATE_CRISIS_KEYWORDS]
    LOW_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in LOW_CRISIS_KEYWORDS]
    
    @classmethod
    def detect_crisis(cls, message_text):
        """
        Detect crisis level in message text
        
        Returns:
            dict: {
                'is_crisis': bool,
                'crisis_level': int (0-10),
                'severity': str ('none', 'low', 'moderate', 'severe'),
                'keywords_detected': list,
                'requires_immediate_intervention': bool
            }
        """
        message_text = message_text.lower().strip()
        detected_keywords = []
        crisis_level = 0
        severity = 'none'
        
        # Check severe crisis keywords (Level 8-10)
        for pattern in cls.SEVERE_PATTERNS:
            matches = pattern.findall(message_text)
            if matches:
                detected_keywords.extend(matches)
                crisis_level = max(crisis_level, 9)
                severity = 'severe'
        
        # Check moderate crisis keywords (Level 5-7)
        if crisis_level < 8:
            for pattern in cls.MODERATE_PATTERNS:
                matches = pattern.findall(message_text)
                if matches:
                    detected_keywords.extend(matches)
                    crisis_level = max(crisis_level, 6)
                    severity = 'moderate'
        
        # Check low crisis keywords (Level 2-4)
        if crisis_level < 5:
            for pattern in cls.LOW_PATTERNS:
                matches = pattern.findall(message_text)
                if matches:
                    detected_keywords.extend(matches)
                    crisis_level = max(crisis_level, 3)
                    severity = 'low'
        
        is_crisis = crisis_level >= 3
        requires_immediate_intervention = crisis_level >= 8
        
        return {
            'is_crisis': is_crisis,
            'crisis_level': crisis_level,
            'severity': severity,
            'keywords_detected': list(set(detected_keywords)),  # Remove duplicates
            'requires_immediate_intervention': requires_immediate_intervention
        }
    
    @classmethod
    def create_crisis_alert(cls, user, session, message, detection_result):
        """
        Create a crisis alert and notify admin/counselors
        
        Args:
            user: User model instance
            session: ChatSession instance
            message: Message instance
            detection_result: dict from detect_crisis()
        """
        try:
            # Get or create crisis type
            crisis_type, _ = CrisisType.objects.get_or_create(
                name="Mental Health Crisis",
                defaults={
                    'description': 'AI-detected mental health crisis',
                    'severity_level': detection_result['crisis_level'],
                    'trigger_keywords': detection_result['keywords_detected'],
                    'immediate_response': 'Contact student immediately',
                    'escalation_criteria': 'Severity level >= 8',
                    'requires_immediate_intervention': True
                }
            )
            
            # Create crisis alert using existing model
            alert = CrisisAlert.objects.create(
                user=user,
                crisis_type=crisis_type,
                chat_session=session,
                message=message,
                status=CrisisAlert.AlertStatus.ACTIVE,
                source=CrisisAlert.AlertSource.AI_DETECTION,
                severity_level=detection_result['crisis_level'],
                confidence_score=0.85,  # High confidence from keyword matching
                description=f"AI detected crisis keywords in chat message",
                detected_keywords=detection_result['keywords_detected'],
                context_data={
                    'severity': detection_result['severity'],
                    'message_preview': message.content[:200],
                    'session_id': str(session.id)
                }
            )
            
            # Update session crisis tracking
            session.crisis_level = max(session.crisis_level, detection_result['crisis_level'])
            session.crisis_keywords_detected = list(set(
                session.crisis_keywords_detected + detection_result['keywords_detected']
            ))
            session.requires_intervention = True
            
            if detection_result['requires_immediate_intervention']:
                session.status = 'crisis_escalated'
            
            session.save()
            
            # Notify admin and counselors
            cls.notify_staff(alert, user)
            
            logger.warning(
                f"Crisis detected - User: {user.username}, Level: {detection_result['crisis_level']}, "
                f"Severity: {detection_result['severity']}"
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Error creating crisis alert: {str(e)}")
            return None
    
    @classmethod
    def notify_staff(cls, alert, user):
        """
        Notify admin and counselors about crisis alert
        """
        try:
            # Get all admins and counselors
            staff_users = User.objects.filter(
                role__in=['admin', 'counselor'],
                is_active=True
            )
            
            # Prepare notification
            subject = f"🚨 CRISIS ALERT - {alert.severity_level}/10 - Student: {user.get_full_name()}"
            
            message = f"""
CRISIS ALERT NOTIFICATION

Severity Level: {alert.severity_level}/10
Crisis Type: {alert.crisis_type.name}
Student: {user.get_full_name()} ({user.username})
Email: {user.email}
Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Detected Keywords: {', '.join(alert.detected_keywords)}

Message Preview:
"{alert.context_data.get('message_preview', 'N/A')}"

{"⚠️ REQUIRES IMMEDIATE INTERVENTION" if alert.severity_level >= 8 else ""}

Action Required:
1. Review the full conversation in the admin panel
2. Contact the student immediately if severe
3. Follow crisis intervention protocols
4. Document all actions taken

Admin Panel: {settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'}/admin/crisis/crisisalert/{alert.id}/

--
MANAS Mental Health Platform
Automated Crisis Detection System
            """
            
            # Send email to staff
            recipient_emails = [u.email for u in staff_users if u.email]
            
            if recipient_emails:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipient_emails,
                    fail_silently=True  # Don't break if email fails
                )
                
                logger.info(f"Crisis alert notifications sent to {len(recipient_emails)} staff members")
            
            # Create in-app notifications (if notification system exists)
            try:
                from core.models import Notification
                for staff_user in staff_users:
                    Notification.objects.create(
                        user=staff_user,
                        title=f"🚨 Crisis Alert - {alert.get_severity_display()}",
                        message=f"Student {user.get_full_name()} needs immediate attention. Crisis level: {alert.crisis_level}/10",
                        notification_type='crisis_alert',
                        link=f'/admin/chat/crisisalert/{alert.id}/',
                        priority='urgent'
                    )
            except:
                pass  # Notification system might not exist
                
        except Exception as e:
            logger.error(f"Error notifying staff about crisis: {str(e)}")
    
    @classmethod
    def get_helpline_numbers(cls):
        """
        Get India-centric crisis helpline numbers
        """
        return {
            'icall': {
                'number': '9152987821',
                'label': 'iCall Psychosocial Helpline',
                'description': 'Mon-Sat, 8 AM - 10 PM (English, Hindi, Marathi)',
                'availability': 'Mon-Sat, 8 AM - 10 PM'
            },
            'kiran': {
                'number': '1800-599-0019',
                'label': 'KIRAN Mental Health Helpline',
                'description': '24/7 toll-free support (Multiple Indian languages)',
                'availability': '24/7 Toll-Free'
            },
            'vandrevala': {
                'number': '9999666555',
                'label': 'Vandrevala Foundation Helpline',
                'description': '24/7 mental health support (English, Hindi)',
                'availability': '24/7'
            },
            'aasra': {
                'number': '9820466726',
                'label': 'AASRA (Mumbai)',
                'description': '24/7 crisis helpline for emotional support',
                'availability': '24/7'
            },
            'sneha': {
                'number': '044-24640050',
                'label': 'SNEHA (Chennai)',
                'description': '24/7 suicide prevention helpline',
                'availability': '24/7'
            },
            'emergency': {
                'number': '112',
                'label': 'Emergency Services (India)',
                'description': 'Police, Ambulance, Fire - Immediate danger',
                'availability': '24/7 Emergency'
            }
        }
