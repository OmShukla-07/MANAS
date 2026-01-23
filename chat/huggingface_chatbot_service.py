"""
Hugging Face BERT-Based Mental Health Chatbot Service for MANAS Platform
Uses ourafla/mental-health-bert-finetuned model for emotion classification
"""

import logging
import re
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger(__name__)


class HuggingFaceMentalHealthService:
    """
    Hugging Face BERT-based mental health chatbot service
    Uses fine-tuned BERT model for mental health emotion classification
    """
    
    def __init__(self):
        """Initialize the Hugging Face chatbot service"""
        logger.info("🤗 Initializing Hugging Face Mental Health Chatbot...")
        
        # Crisis keywords for immediate detection
        self.crisis_keywords = [
            'suicide', 'suicidal', 'kill myself', 'end my life', 'want to die',
            'better off dead', 'no reason to live', 'end it all', 'hurt myself',
            'harm myself', 'goodbye letter', 'plan to die', 'ready to go',
            'wish i was dead', 'don\'t want to live', 'ready to end', 'take my life',
            'self harm', 'cut myself', 'overdose'
        ]
        
        # Crisis patterns
        self.crisis_patterns = [
            r'\bi want to (die|kill myself|end (it|my life))\b',
            r'\bgoing to (kill myself|die|end it)\b',
            r'\b(better off dead|no point living|can\'t go on)\b',
            r'\bsuicide\b',
            r'\bhurt myself\b',
            r'\bself.?harm\b'
        ]
        
        # Lazy load the model (don't load on init to save memory)
        self.pipe = None
        self.tokenizer = None
        self.model = None
        self._model_loaded = False
        
        logger.info("✨ Hugging Face Chatbot initialized (model will load on first use)!")
    
    def load_model(self):
        """Load the Hugging Face BERT model (lazy loading)"""
        if self._model_loaded:
            return  # Already loaded
            
        try:
            # Try the mental health model first (requires authentication)
            model_name = "ourafla/mental-health-bert-finetuned"
            logger.info(f"📥 Loading model: {model_name}")
            
            try:
                # Option 1: Use pipeline (high-level, easier)
                self.pipe = pipeline("text-classification", model=model_name)
                
                # Option 2: Load model directly (for more control)
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
                
                logger.info("✅ Model loaded successfully!")
                
            except Exception as e:
                logger.warning(f"⚠️ Couldn't load gated model (needs HF auth): {str(e)[:100]}")
                logger.info("📥 Loading alternative emotion classification model...")
                
                # Fallback to open emotion classification model
                model_name = "j-hartmann/emotion-english-distilroberta-base"
                self.pipe = pipeline("text-classification", model=model_name, top_k=None)
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
                
                logger.info(f"✅ Alternative model loaded: {model_name}")
            
            self._model_loaded = True
            
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            self.pipe = None
            self.tokenizer = None
            self.model = None
            self._model_loaded = False
    
    def detect_crisis(self, text):
        """
        Detect if message indicates a crisis situation
        Returns: (is_crisis, confidence, crisis_type)
        """
        text_lower = text.lower()
        
        # Check for direct crisis keywords
        for keyword in self.crisis_keywords:
            if keyword in text_lower:
                logger.warning(f"🚨 CRISIS KEYWORD DETECTED: {keyword}")
                return True, 1.0, 'suicidal'
        
        # Check for crisis patterns
        for pattern in self.crisis_patterns:
            if re.search(pattern, text_lower):
                logger.warning(f"🚨 CRISIS PATTERN DETECTED: {pattern}")
                return True, 0.95, 'suicidal'
        
        return False, 0.0, None
    
    def classify_emotion(self, text):
        """
        Classify emotion using HuggingFace API (no local model loading)
        Returns: (emotion_label, confidence, all_scores)
        """
        try:
            # Use HuggingFace API instead of loading local model
            from .hf_conversational_service import hf_conversational_service
            
            emotion, confidence, scores = hf_conversational_service.detect_emotion_api(text)
            
            if emotion:
                logger.info(f"🎯 Emotion detected: {emotion} (confidence: {confidence:.2f})")
                return emotion, confidence, scores
            
            return 'neutral', 0.5, []
            
        except Exception as e:
            logger.error(f"❌ Error in emotion classification: {e}")
            return 'neutral', 0.5, []
    
    def get_response(self, user_message, emotion=None, confidence=0.0, conversation_history=None):
        """
        Generate appropriate response based on emotion classification
        Now uses HuggingFace conversational model for natural responses
        """
        # Import conversational service
        from .hf_conversational_service import hf_conversational_service
        
        # Detect crisis first
        is_crisis, crisis_conf, crisis_type = self.detect_crisis(user_message)
        
        if is_crisis:
            return self.get_crisis_response(crisis_type)
        
        # If emotion not provided, classify it
        if not emotion:
            emotion, confidence, _ = self.classify_emotion(user_message)
        
        # Generate conversational response using HF API
        conv_response = hf_conversational_service.generate_response(
            user_message=user_message,
            conversation_history=conversation_history
        )
        
        # Add emotion metadata
        conv_response['emotion'] = emotion
        conv_response['emotion_confidence'] = confidence
        
        return conv_response
    
    def get_crisis_response(self, crisis_type='suicidal'):
        """Get immediate crisis intervention response"""
        return {
            'response': "🚨 **CRISIS ALERT** 🚨\n\n"
                       "I'm very concerned about what you're sharing. Your safety is the top priority.\n\n"
                       "**Please reach out immediately:**\n"
                       "• National Crisis Helpline: 1-800-273-8255 (24/7)\n"
                       "• Text HOME to 741741 (Crisis Text Line)\n"
                       "• Emergency Services: 911\n\n"
                       "You're not alone. Help is available right now. Please talk to someone who can provide immediate support. 💙",
            'is_crisis': True,
            'crisis_type': crisis_type,
            'confidence': 1.0,
            'suggested_actions': ['emergency_contact', 'counselor_referral']
        }
    
    def generate_emotion_response(self, emotion, confidence, user_message=''):
        """
        Generate empathetic response based on detected emotion
        Now includes context-aware and specific responses
        """
        # Extract key topics from user message for context
        message_lower = user_message.lower()
        
        # Detect specific situations
        situations = {
            'sleep': any(word in message_lower for word in ['sleep', 'insomnia', 'cant sleep', 'tired', 'exhausted']),
            'academic': any(word in message_lower for word in ['exam', 'test', 'study', 'assignment', 'homework', 'grades', 'school', 'college']),
            'relationship': any(word in message_lower for word in ['friend', 'boyfriend', 'girlfriend', 'family', 'parents', 'relationship', 'breakup']),
            'bullying': any(word in message_lower for word in ['bully', 'insult', 'hurt', 'mean', 'teasing', 'harassment']),
            'loneliness': any(word in message_lower for word in ['lonely', 'alone', 'isolated', 'no one', 'nobody']),
            'work': any(word in message_lower for word in ['work', 'job', 'boss', 'colleague', 'deadline', 'project']),
        }
        
        # Response templates based on emotion AND situation
        responses = {
            'fear': {
                'academic': [
                    "I can sense you're feeling anxious about your studies. Exam anxiety is really common and completely understandable. Let's break this down - what specific part worries you most? Sometimes taking it step by step helps. 📚💚",
                    "Academic pressure can trigger a lot of anxiety. Remember, your worth isn't defined by grades. Have you tried studying in shorter intervals with breaks? The Pomodoro technique (25 min study, 5 min break) works wonders! 🌿",
                ],
                'relationship': [
                    "Worrying about relationships can be really consuming. It's clear you care deeply. Remember, healthy relationships involve open communication. Have you been able to express how you're feeling? 💙",
                    "Relationship anxiety is tough. Your feelings are valid. Sometimes writing down your thoughts first can help clarify what you want to say. Would that help? 🌟",
                ],
                'general': [
                    "I can sense you're feeling anxious or worried. That's completely valid. Let's take this one step at a time. Have you tried grounding techniques like deep breathing? 💚",
                    "Fear and anxiety can feel overwhelming. Remember, you're safe right now. Try the 5-4-3-2-1 technique: Name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you taste. This helps ground you in the present. 🌿",
                ]
            },
            'sadness': {
                'bullying': [
                    "I'm really sorry you're experiencing this. Being insulted or hurt by someone hurts deeply, especially when it's someone you know. Please know this says everything about them and nothing about your worth. You don't deserve this treatment. 💜",
                    "What you're describing sounds like bullying, and that's never okay. Your feelings of sadness are completely valid. Have you been able to talk to someone you trust about this? You don't have to face this alone. 💙",
                ],
                'loneliness': [
                    "Feeling lonely can be really painful. I want you to know that you're not alone in feeling this way, and reaching out here shows real strength. Have you considered joining any clubs or groups where you might meet people with similar interests? 🌸",
                    "Loneliness hurts, and I hear that pain. Sometimes starting small helps - even a brief conversation with a classmate or neighbor can make a difference. What activities do you enjoy? 💜",
                ],
                'relationship': [
                    "Relationship sadness runs deep. It sounds like this person means a lot to you. When someone we care about hurts us, it affects us deeply. Have you thought about having an honest conversation with them about how their actions made you feel? 💙",
                    "I'm sorry you're going through this with your friend. Friendship conflicts are really hard. Remember, true friends respect and value you. If talking doesn't help, it might be worth thinking about what kind of friendships serve your wellbeing. 🌙",
                ],
                'general': [
                    "I'm really sorry you're feeling this way. Sadness this deep can be really painful. Your emotions matter, and it's okay to not be okay. Would you like to share what's making you feel this way? 💙",
                    "That sounds really hard. Deep sadness can feel overwhelming. Please remember that these feelings won't last forever, even though it might not feel that way right now. I'm here for you. 🌙",
                ]
            },
            'anger': {
                'bullying': [
                    "I can feel your frustration and anger about being treated this way. Those are completely valid emotions - you have every right to be upset. Being insulted is not okay. Would it help to talk through what happened and think about how to respond? 🔥",
                    "Your anger makes sense - being disrespected hurts and makes us angry. That's normal. The question is: how do you want to handle this in a way that makes YOU feel empowered? Let's think about your options. 💪",
                ],
                'relationship': [
                    "It sounds like this person's actions have really upset you, and rightfully so. Anger often protects us from hurt. Under the anger, is there hurt or disappointment? Sometimes understanding the full emotion helps. 🌟",
                    "I hear your frustration with this situation. When people we care about let us down, it can make us angry. Have you been able to tell them how their actions affected you? 💙",
                ],
                'general': [
                    "I can feel that you're really angry or frustrated right now. Those are valid emotions. It's okay to feel this way. What's happening that's making you feel like this? 🔥",
                    "Anger can be intense and overwhelming. I'm here to listen without judgment. Sometimes getting these feelings out can help. What's going on? 💪",
                ]
            },
            'joy': {
                'general': [
                    "I'm so glad to hear you're feeling good! It's wonderful when we have moments of joy. What's making you feel great today? Keep holding onto that positive energy! 🌟✨",
                    "That's fantastic! Your happiness is contagious! It's important to celebrate these good moments. What brought about this positive feeling? 💫",
                ]
            },
            'surprise': {
                'general': [
                    "It sounds like something unexpected happened. Tell me more about what's going on. I'm here to listen and help you process this. 🌟",
                    "That seems surprising! How are you processing what happened? Sometimes unexpected things throw us off balance. 💙",
                ]
            },
            'disgust': {
                'general': [
                    "It sounds like something is really bothering you or doesn't sit right with you. Your feelings are valid. Want to talk about what's troubling you? 💜",
                    "I hear that something doesn't feel right to you. Sometimes these uncomfortable feelings are our intuition telling us something. What's on your mind? 🌿",
                ]
            },
            'stress': {
                'academic': [
                    "Academic stress is really tough, especially when deadlines pile up. Let's break this down - what's the most urgent thing you need to handle? Sometimes just making a list and tackling one thing at a time helps. 💪",
                    "Study stress is so real. Remember: you can only do what you can do. Have you tried the Eisenhower Matrix? Sort tasks by urgent/important to prioritize better. Also, don't forget to sleep - your brain needs rest to retain information! 🌿",
                ],
                'work': [
                    "Work stress can be exhausting. It sounds like you're carrying a heavy load. Have you been able to take any proper breaks? Even 5 minutes away from your desk can help reset your mind. 💚",
                    "That work situation sounds overwhelming. Remember, you can only do your best. Have you considered talking to your supervisor about the workload? You deserve support. 🌟",
                ],
                'general': [
                    "That sounds incredibly stressful. When we're under a lot of pressure, it's important to give ourselves permission to take breaks. What's causing the most stress for you right now? 💪",
                    "I can tell you're dealing with a lot right now. Stress can be exhausting. Have you been able to take any time for yourself lately? Let's explore some coping strategies. 🌿",
                ]
            },
            'neutral': {
                'general': [
                    "How are you feeling today? I'm here to listen and support you with whatever is on your mind. 🌟",
                    "Thanks for reaching out. What would you like to talk about today? 💙",
                ]
            },
            'default': {
                'general': [
                    "I hear you. It takes courage to share how you're feeling. Tell me more about what's going on. 💙",
                    "Thank you for opening up. I'm here to listen without judgment. What's been on your mind? 🌟",
                ]
            }
        }
        
        # Determine intensity based on confidence
        if confidence >= 0.8:
            intensity = 'high'
        elif confidence >= 0.5:
            intensity = 'medium'
        else:
            intensity = 'low'
        
        # Get appropriate response based on emotion and situation
        emotion_key = emotion.lower() if emotion else 'default'
        
        if emotion_key not in responses:
            emotion_key = 'default'
        
        # Find matching situation
        situation_key = 'general'
        for situation, is_present in situations.items():
            if is_present and situation in responses[emotion_key]:
                situation_key = situation
                break
        
        # Get response list
        if situation_key in responses[emotion_key]:
            response_list = responses[emotion_key][situation_key]
        elif 'general' in responses[emotion_key]:
            response_list = responses[emotion_key]['general']
        else:
            response_list = responses['default']['general']
        
        import random
        response_text = random.choice(response_list)
        
        return {
            'response': response_text,
            'emotion': emotion,
            'confidence': confidence,
            'intensity': intensity,
            'situation': situation_key if situation_key != 'general' else None,
            'is_crisis': False,
            'suggested_actions': self.get_suggested_actions(emotion, situation_key)
        }
    
    def get_suggested_actions(self, emotion, situation='general'):
        """Get suggested follow-up actions based on emotion and situation"""
        action_map = {
            'fear': {
                'academic': ['study_tips', 'breathing_exercise', 'time_management', 'counselor_chat'],
                'relationship': ['communication_tips', 'counselor_chat', 'peer_support'],
                'general': ['breathing_exercise', 'grounding_technique', 'counselor_chat']
            },
            'anxiety': {
                'academic': ['study_tips', 'breathing_exercise', 'time_management'],
                'general': ['breathing_exercise', 'grounding_technique', 'counselor_chat']
            },
            'sadness': {
                'bullying': ['report_bullying', 'counselor_chat', 'peer_support', 'self_esteem_resources'],
                'loneliness': ['peer_support', 'social_activities', 'counselor_chat'],
                'relationship': ['communication_tips', 'counselor_chat', 'peer_support'],
                'general': ['mood_journal', 'counselor_chat', 'peer_support']
            },
            'anger': {
                'bullying': ['conflict_resolution', 'counselor_chat', 'anger_management'],
                'relationship': ['communication_tips', 'anger_management', 'counselor_chat'],
                'general': ['anger_management', 'breathing_exercise', 'counselor_chat']
            },
            'joy': {
                'general': ['mood_tracking', 'share_positivity', 'keep_journal']
            },
            'surprise': {
                'general': ['reflection', 'counselor_chat', 'mood_tracking']
            },
            'disgust': {
                'general': ['self_reflection', 'counselor_chat', 'coping_strategies']
            },
            'stress': {
                'academic': ['time_management', 'study_tips', 'stress_management', 'counselor_chat'],
                'work': ['time_management', 'stress_management', 'work_life_balance'],
                'general': ['stress_management', 'time_management', 'relaxation_techniques']
            },
            'neutral': {
                'general': ['mood_tracking', 'resources', 'peer_support']
            }
        }
        
        emotion_key = emotion.lower() if emotion else 'neutral'
        
        if emotion_key in action_map:
            if situation in action_map[emotion_key]:
                return action_map[emotion_key][situation]
            elif 'general' in action_map[emotion_key]:
                return action_map[emotion_key]['general']
        
        return ['counselor_chat', 'resources']
    
    def chat(self, user_message, context=None):
        """
        Main chat interface
        Args:
            user_message: User's message text
            context: Optional conversation context
        Returns:
            Response dictionary with message and metadata
        """
        try:
            logger.info(f"💬 Processing message: {user_message[:50]}...")
            
            # Detect crisis first
            is_crisis, crisis_conf, crisis_type = self.detect_crisis(user_message)
            
            if is_crisis:
                return self.get_crisis_response(crisis_type)
            
            # Classify emotion
            emotion, confidence, all_scores = self.classify_emotion(user_message)
            
            # Generate response
            response_data = self.get_response(user_message, emotion, confidence)
            
            # Add classification details
            response_data['classification'] = {
                'emotion': emotion,
                'confidence': confidence,
                'all_scores': all_scores
            }
            
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Error in chat: {e}", exc_info=True)
            return {
                'response': "I'm here to help, but I'm having trouble processing that right now. Could you rephrase what's on your mind? 💙",
                'error': str(e),
                'is_crisis': False
            }


# Singleton instance
_service_instance = None

def get_huggingface_service():
    """Get or create the Hugging Face service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = HuggingFaceMentalHealthService()
    return _service_instance
