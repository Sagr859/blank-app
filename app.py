import streamlit as st
import openai
import PyPDF2
import json
import os
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from dotenv import load_dotenv

# Configure page
st.set_page_config(
    page_title="AI Resume Assessment & PDF Builder",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern design
st.markdown("""
<style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Hero section */
    .hero-container {
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        margin-bottom: 3rem;
        color: white;
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        line-height: 1.2;
    }
    
    .hero-subtitle {
        font-size: 1.4rem;
        opacity: 0.9;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Upload section */
    .upload-container {
        background: white;
        border: 3px dashed #e0e7ff;
        border-radius: 20px;
        padding: 3rem 2rem;
        text-align: center;
        margin: 2rem 0;
        transition: all 0.3s ease;
    }
    
    .upload-container:hover {
        border-color: #667eea;
        background: #f8faff;
    }
    
    .upload-icon {
        font-size: 4rem;
        color: #9ca3af;
        margin-bottom: 1rem;
    }
    
    /* Feature cards */
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        text-align: center;
        margin: 1rem 0;
        border: 1px solid #f3f4f6;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    }
    
    .feature-icon {
        width: 60px;
        height: 60px;
        background: #667eea;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem;
        font-size: 1.5rem;
        color: white;
    }
    
    .feature-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #1f2937;
    }
    
    .feature-description {
        color: #6b7280;
        line-height: 1.6;
    }
    
    /* Progress steps */
    .progress-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2rem 0;
        padding: 1rem;
        background: #f8faff;
        border-radius: 15px;
    }
    
    .progress-step {
        display: flex;
        align-items: center;
        margin: 0 1rem;
    }
    
    .step-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    
    .step-active {
        background: #667eea;
        color: white;
    }
    
    .step-completed {
        background: #10b981;
        color: white;
    }
    
    .step-pending {
        background: #e5e7eb;
        color: #6b7280;
    }
    
    /* Form styling */
    .stTextArea textarea {
        border-radius: 10px !important;
        border: 2px solid #e5e7eb !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    .stSelectbox > div > div {
        border-radius: 10px !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: #667eea !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background: #5a67d8 !important;
        transform: translateY(-2px) !important;
    }
    
    /* Download buttons */
    .download-container {
        background: #f8faff;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        text-align: center;
    }
    
    /* Success messages */
    .success-container {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 2rem 0;
    }
    
    /* Metrics styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        text-align: center;
        margin: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .metric-label {
        color: #6b7280;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()

class ResumeAssessmentSystem:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def extract_text_from_pdf(self, file):
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    def assess_resume(self, resume_text):
        """Analyze resume and provide comprehensive assessment"""
        prompt = f"""
        Analyze the following resume and provide a comprehensive assessment:

        Resume Text:
        {resume_text}

        Please provide:
        1. Overall assessment score (1-10)
        2. Key strengths identified
        3. Areas for improvement
        4. Missing sections or information
        5. Industry-specific skills mentioned
        6. Recommended skills to add
        7. Experience level assessment
        8. Format and presentation feedback

        Return the response as a JSON object with the following structure:
        {{
            "overall_score": 0,
            "strengths": [],
            "improvements": [],
            "missing_sections": [],
            "current_skills": [],
            "recommended_skills": [],
            "experience_level": "",
            "format_feedback": ""
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            return {"error": f"Assessment failed: {str(e)}"}
    
    def generate_skill_questions(self, skills, experience_level):
        """Generate skill-based interview questions"""
        prompt = f"""
        Based on the following skills and experience level, generate 10 relevant technical and behavioral questions:
        
        Skills: {', '.join(skills)}
        Experience Level: {experience_level}
        
        Return as JSON array with question objects:
        {{
            "questions": [
                {{
                    "question": "Question text here",
                    "type": "technical/behavioral",
                    "skill_area": "relevant skill"
                }}
            ]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            return {"error": f"Question generation failed: {str(e)}"}
    
    def parse_and_improve_resume(self, resume_text, assessment, additional_info=""):
        """Parse resume and create improved structured version"""
        prompt = f"""
        Parse and improve the following resume based on assessment feedback:

        Original Resume:
        {resume_text}

        Assessment Feedback:
        - Score: {assessment.get('overall_score', 'N/A')}/10
        - Strengths: {', '.join(assessment.get('strengths', []))}
        - Areas for improvement: {', '.join(assessment.get('improvements', []))}
        - Recommended skills: {', '.join(assessment.get('recommended_skills', []))}
        - Missing sections: {', '.join(assessment.get('missing_sections', []))}

        Additional Information:
        {additional_info}

        Create an improved, structured resume with the following sections. Return as JSON:
        {{
            "personal_info": {{
                "name": "Full Name",
                "email": "email@example.com",
                "phone": "Phone Number",
                "location": "City, State",
                "linkedin": "LinkedIn URL (optional)",
                "portfolio": "Website URL (optional)"
            }},
            "professional_summary": "A compelling 2-3 sentence professional summary with strong action words and quantified achievements",
            "experience": [
                {{
                    "title": "Job Title",
                    "company": "Company Name",
                    "location": "City, State",
                    "duration": "MM/YYYY - MM/YYYY",
                    "achievements": [
                        "• Achievement 1 with quantified results",
                        "• Achievement 2 with strong action verbs",
                        "• Achievement 3 showing impact"
                    ]
                }}
            ],
            "education": [
                {{
                    "degree": "Degree Type and Major",
                    "institution": "University Name",
                    "location": "City, State",
                    "graduation": "MM/YYYY",
                    "gpa": "GPA (if 3.5+, otherwise omit)",
                    "honors": "Honors/Awards (optional)"
                }}
            ],
            "skills": {{
                "technical": ["Technical Skill 1", "Technical Skill 2"],
                "languages": ["Language 1", "Language 2"],
                "tools": ["Tool 1", "Tool 2"]
            }},
            "projects": [
                {{
                    "name": "Project Name",
                    "description": "Brief description with technologies used and impact",
                    "link": "GitHub/Demo link (optional)"
                }}
            ],
            "certifications": ["Certification 1", "Certification 2"],
            "achievements": ["Award 1", "Award 2"]
        }}

        Ensure all content is improved with:
        - Strong action verbs (Led, Implemented, Achieved, Optimized, etc.)
        - Quantified results where possible
        - Professional language
        - ATS-friendly formatting
        - Industry-relevant keywords
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=3000
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            return {"error": f"Assessment failed: {str(e)}"}
    
    def create_ats_optimized_resume(self, resume_text, assessment, user_responses):
        """Create ATS-optimized resume combining assessment and user input"""
        prompt = f"""
        Create an ATS-optimized, professional resume combining the original resume, assessment feedback, and user responses:

        ORIGINAL RESUME:
        {resume_text}

        ASSESSMENT RESULTS:
        - Overall Score: {assessment.get('overall_score', 'N/A')}/10
        - Experience Level: {assessment.get('experience_level', '')}
        - Current Skills: {', '.join(assessment.get('current_skills', []))}
        - Recommended Skills: {', '.join(assessment.get('recommended_skills', []))}
        - Areas for Improvement: {', '.join(assessment.get('improvements', []))}
        - Missing Sections: {', '.join(assessment.get('missing_sections', []))}

        USER RESPONSES:
        - Career Objective: {user_responses.get('career_objective', '')}
        - Key Achievements: {user_responses.get('achievements', '')}
        - Additional Skills: {user_responses.get('skills_to_add', '')}
        - Recent Projects: {user_responses.get('recent_projects', '')}
        - Target Industry: {user_responses.get('target_industry', '')}
        - Target Level: {user_responses.get('target_level', '')}
        - Company Size Preference: {user_responses.get('company_size', '')}

        Create an ATS-optimized resume with these requirements:
        1. Use industry-specific keywords for {user_responses.get('target_industry', 'Technology')}
        2. Format for {user_responses.get('target_level', 'Mid Level')} positions
        3. Include quantified achievements from user responses
        4. Use strong action verbs and measurable results
        5. Ensure ATS-friendly formatting with clear section headers
        6. Incorporate both existing and recommended skills strategically
        7. Create compelling professional summary targeting the user's objective

        Return as JSON with this exact structure:
        {{
            "personal_info": {{
                "name": "Full Name",
                "email": "email@example.com",
                "phone": "Phone Number",
                "location": "City, State",
                "linkedin": "LinkedIn URL (if available)",
                "portfolio": "Website URL (if available)"
            }},
            "professional_summary": "2-3 sentence compelling summary with keywords for {user_responses.get('target_industry', 'Technology')} industry and {user_responses.get('target_level', 'Mid Level')} level",
            "experience": [
                {{
                    "title": "Job Title",
                    "company": "Company Name",
                    "location": "City, State",
                    "duration": "MM/YYYY - MM/YYYY",
                    "achievements": [
                        "• Enhanced achievement with quantified results and strong action verbs",
                        "• Another achievement showing impact and using industry keywords",
                        "• Third achievement demonstrating skills relevant to target role"
                    ]
                }}
            ],
            "education": [
                {{
                    "degree": "Degree Type and Major",
                    "institution": "University Name",
                    "location": "City, State",
                    "graduation": "MM/YYYY",
                    "gpa": "GPA (if 3.5+)",
                    "honors": "Relevant honors/awards"
                }}
            ],
            "skills": {{
                "technical": ["Priority technical skills for target role"],
                "tools": ["Industry-relevant tools and platforms"],
                "languages": ["Programming/spoken languages if relevant"],
                "certifications": ["Relevant certifications"]
            }},
            "projects": [
                {{
                    "name": "Project Name",
                    "description": "Description emphasizing technologies and impact with measurable results",
                    "link": "GitHub/Demo link (if available)"
                }}
            ],
            "achievements": [
                "Key career achievements with quantified results",
                "Awards, recognitions, or notable accomplishments"
            ]
        }}

        CRITICAL ATS OPTIMIZATION REQUIREMENTS:
        - Use exact keywords from target industry and role level
        - Include metrics and numbers wherever possible
        - Use standard section headers (EXPERIENCE, EDUCATION, SKILLS, etc.)
        - Avoid graphics, tables, or complex formatting
        - Front-load important keywords in job descriptions
        - Include both hard and soft skills relevant to target role
        - Ensure 70%+ keyword match for {user_responses.get('target_industry', 'Technology')} {user_responses.get('target_level', 'Mid Level')} positions
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Lower temperature for more consistent, professional output
                max_tokens=3500
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            return {"error": f"ATS resume creation failed: {str(e)}"}
    
    def generate_cover_letter(self, resume_data, user_responses, job_description="", company_name=""):
        """Generate a personalized cover letter"""
        prompt = f"""
        Create a professional, compelling cover letter based on the following information:

        RESUME DATA:
        - Name: {resume_data.get('personal_info', {}).get('name', 'Candidate')}
        - Professional Summary: {resume_data.get('professional_summary', '')}
        - Experience: {[exp.get('title', '') + ' at ' + exp.get('company', '') for exp in resume_data.get('experience', [])]}
        - Skills: {', '.join([skill for category in resume_data.get('skills', {}).values() for skill in (category if isinstance(category, list) else [])])}

        USER GOALS:
        - Career Objective: {user_responses.get('career_objective', '')}
        - Target Industry: {user_responses.get('target_industry', 'Technology')}
        - Target Level: {user_responses.get('target_level', 'Mid Level')}
        - Key Achievements: {user_responses.get('achievements', '')}
        - Company Size Preference: {user_responses.get('company_size', '')}

        JOB DETAILS:
        - Company Name: {company_name if company_name else 'the company'}
        - Job Description: {job_description if job_description else 'the position'}

        Create a cover letter that:
        1. Has a strong opening that grabs attention
        2. Demonstrates knowledge of the company/role (if provided)
        3. Highlights relevant experience and achievements with specific examples
        4. Shows enthusiasm for the target industry and role
        5. Includes a compelling call to action
        6. Is 3-4 paragraphs long
        7. Uses industry-appropriate language and keywords
        8. Shows personality while maintaining professionalism

        Format as a complete cover letter with proper structure:
        - Date
        - Recipient (Dear Hiring Manager or specific name if provided)
        - Body paragraphs
        - Professional closing
        - Signature line

        Make it compelling and personalized, not generic.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,  # Slightly higher for more personality
                max_tokens=1500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Cover letter generation failed: {str(e)}"
    
    def generate_portfolio_website(self, resume_data, user_responses):
        """Generate a complete HTML/CSS/JS portfolio website"""
        try:
            # Extract data from resume
            personal_info = resume_data.get('personal_info', {})
            name = personal_info.get('name', 'Your Name')
            email = personal_info.get('email', 'email@example.com')
            phone = personal_info.get('phone', 'Phone Number')
            location = personal_info.get('location', 'Location')
            linkedin = personal_info.get('linkedin', '')
            portfolio = personal_info.get('portfolio', '')
            
            summary = resume_data.get('professional_summary', 'Professional summary goes here.')
            experience = resume_data.get('experience', [])
            education = resume_data.get('education', [])
            skills = resume_data.get('skills', {})
            projects = resume_data.get('projects', [])
            achievements = resume_data.get('achievements', [])
            
            # Generate color scheme based on industry
            industry = user_responses.get('target_industry', 'Technology')
            color_schemes = {
                'Technology': {'primary': '#667eea', 'secondary': '#764ba2', 'accent': '#f093fb'},
                'Healthcare': {'primary': '#11998e', 'secondary': '#38ef7d', 'accent': '#73c8a9'},
                'Finance': {'primary': '#2c3e50', 'secondary': '#3498db', 'accent': '#85c1e5'},
                'Education': {'primary': '#8e44ad', 'secondary': '#3498db', 'accent': '#bb6bd9'},
                'Marketing': {'primary': '#e74c3c', 'secondary': '#f39c12', 'accent': '#f8b500'},
                'Consulting': {'primary': '#34495e', 'secondary': '#95a5a6', 'accent': '#bdc3c7'}
            }
            colors = color_schemes.get(industry, color_schemes['Technology'])
            
            # Create HTML content
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - Portfolio</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
            overflow-x: hidden;
        }}
        
        /* Header and Navigation */
        .navbar {{
            position: fixed;
            top: 0;
            width: 100%;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 1rem 2rem;
            z-index: 1000;
            transition: all 0.3s ease;
        }}
        
        .nav-container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .logo {{
            font-size: 1.5rem;
            font-weight: bold;
            color: {colors['primary']};
        }}
        
        .nav-links {{
            display: flex;
            list-style: none;
            gap: 2rem;
        }}
        
        .nav-links a {{
            color: #333;
            text-decoration: none;
            transition: color 0.3s ease;
        }}
        
        .nav-links a:hover {{
            color: {colors['primary']};
        }}
        
        /* Hero Section */
        .hero {{
            height: 100vh;
            background: linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: white;
            position: relative;
        }}
        
        .hero-content h1 {{
            font-size: 3.5rem;
            margin-bottom: 1rem;
            animation: fadeInUp 1s ease;
        }}
        
        .hero-content p {{
            font-size: 1.3rem;
            margin-bottom: 2rem;
            animation: fadeInUp 1s ease 0.2s both;
        }}
        
        .cta-button {{
            display: inline-block;
            padding: 12px 30px;
            background: {colors['accent']};
            color: white;
            text-decoration: none;
            border-radius: 50px;
            transition: transform 0.3s ease;
            animation: fadeInUp 1s ease 0.4s both;
        }}
        
        .cta-button:hover {{
            transform: translateY(-3px);
        }}
        
        /* Sections */
        .section {{
            padding: 80px 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .section h2 {{
            text-align: center;
            font-size: 2.5rem;
            margin-bottom: 3rem;
            color: {colors['primary']};
        }}
        
        /* About Section */
        .about-content {{
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 3rem;
            align-items: center;
        }}
        
        .profile-image {{
            width: 300px;
            height: 300px;
            border-radius: 50%;
            background: linear-gradient(135deg, {colors['primary']}, {colors['secondary']});
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 6rem;
            color: white;
            margin: 0 auto;
        }}
        
        /* Skills Section */
        .skills-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }}
        
        .skill-category {{
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .skill-category:hover {{
            transform: translateY(-5px);
        }}
        
        .skill-category h3 {{
            color: {colors['primary']};
            margin-bottom: 1rem;
        }}
        
        .skill-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        
        .skill-tag {{
            background: {colors['primary']};
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
        }}
        
        /* Experience Section */
        .timeline {{
            position: relative;
            padding-left: 2rem;
        }}
        
        .timeline::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            height: 100%;
            width: 2px;
            background: {colors['primary']};
        }}
        
        .timeline-item {{
            position: relative;
            margin-bottom: 3rem;
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-left: 2rem;
        }}
        
        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -3rem;
            top: 2rem;
            width: 12px;
            height: 12px;
            background: {colors['primary']};
            border-radius: 50%;
        }}
        
        .job-title {{
            font-size: 1.3rem;
            font-weight: bold;
            color: {colors['primary']};
        }}
        
        .company {{
            color: {colors['secondary']};
            margin-bottom: 0.5rem;
        }}
        
        .duration {{
            color: #666;
            font-style: italic;
            margin-bottom: 1rem;
        }}
        
        /* Projects Section */
        .projects-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }}
        
        .project-card {{
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .project-card:hover {{
            transform: translateY(-5px);
        }}
        
        .project-header {{
            background: linear-gradient(135deg, {colors['primary']}, {colors['secondary']});
            color: white;
            padding: 1.5rem;
        }}
        
        .project-body {{
            padding: 1.5rem;
        }}
        
        /* Contact Section */
        .contact {{
            background: #f8f9fa;
            text-align: center;
        }}
        
        .contact-info {{
            display: flex;
            justify-content: center;
            gap: 3rem;
            margin-top: 2rem;
            flex-wrap: wrap;
        }}
        
        .contact-item {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .contact-item i {{
            font-size: 1.5rem;
            color: {colors['primary']};
        }}
        
        /* Animations */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .fade-in {{
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.6s ease;
        }}
        
        .fade-in.visible {{
            opacity: 1;
            transform: translateY(0);
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            .hero-content h1 {{
                font-size: 2.5rem;
            }}
            
            .about-content {{
                grid-template-columns: 1fr;
                text-align: center;
            }}
            
            .nav-links {{
                display: none;
            }}
            
            .contact-info {{
                flex-direction: column;
                gap: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">{name}</div>
            <ul class="nav-links">
                <li><a href="#about">About</a></li>
                <li><a href="#skills">Skills</a></li>
                <li><a href="#experience">Experience</a></li>
                <li><a href="#projects">Projects</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero">
        <div class="hero-content">
            <h1>{name}</h1>
            <p>{user_responses.get('career_objective', 'Professional seeking new opportunities')}</p>
            <a href="#contact" class="cta-button">Get In Touch</a>
        </div>
    </section>

    <!-- About Section -->
    <section id="about" class="section">
        <h2>About Me</h2>
        <div class="about-content">
            <div class="profile-image">
                <i class="fas fa-user"></i>
            </div>
            <div>
                <p style="font-size: 1.1rem; margin-bottom: 1.5rem;">{summary}</p>
                <p><strong>Location:</strong> {location}</p>
                <p><strong>Industry Focus:</strong> {user_responses.get('target_industry', 'Technology')}</p>
                <p><strong>Experience Level:</strong> {user_responses.get('target_level', 'Professional')}</p>
            </div>
        </div>
    </section>

    <!-- Skills Section -->
    <section id="skills" class="section">
        <h2>Skills & Expertise</h2>
        <div class="skills-grid">"""
            
            # Add skills categories
            if isinstance(skills, dict):
                for category, skill_list in skills.items():
                    if skill_list:
                        category_title = category.replace('_', ' ').title()
                        html_content += f"""
            <div class="skill-category fade-in">
                <h3>{category_title}</h3>
                <div class="skill-tags">"""
                        for skill in skill_list:
                            html_content += f'<span class="skill-tag">{skill}</span>'
                        html_content += """
                </div>
            </div>"""
            
            html_content += """
        </div>
    </section>

    <!-- Experience Section -->
    <section id="experience" class="section">
        <h2>Professional Experience</h2>
        <div class="timeline">"""
            
            # Add experience items
            for exp in experience:
                html_content += f"""
            <div class="timeline-item fade-in">
                <div class="job-title">{exp.get('title', 'Job Title')}</div>
                <div class="company">{exp.get('company', 'Company Name')}</div>
                <div class="duration">{exp.get('duration', 'Duration')}</div>
                <div class="description">"""
                
                if exp.get('achievements'):
                    html_content += "<ul>"
                    for achievement in exp['achievements']:
                        html_content += f"<li>{achievement.replace('•', '').strip()}</li>"
                    html_content += "</ul>"
                
                html_content += """
                </div>
            </div>"""
            
            html_content += """
        </div>
    </section>

    <!-- Projects Section -->
    <section id="projects" class="section">
        <h2>Featured Projects</h2>
        <div class="projects-grid">"""
            
            # Add projects
            for i, project in enumerate(projects):
                html_content += f"""
            <div class="project-card fade-in">
                <div class="project-header">
                    <h3>{project.get('name', f'Project {i+1}')}</h3>
                </div>
                <div class="project-body">
                    <p>{project.get('description', 'Project description goes here.')}</p>"""
                    
                if project.get('link'):
                    html_content += f'<a href="{project["link"]}" target="_blank" style="color: {colors["primary"]};">View Project →</a>'
                    
                html_content += """
                </div>
            </div>"""
            
            # Add achievements as projects if no projects exist
            if not projects and achievements:
                for i, achievement in enumerate(achievements):
                    html_content += f"""
            <div class="project-card fade-in">
                <div class="project-header">
                    <h3>Achievement {i+1}</h3>
                </div>
                <div class="project-body">
                    <p>{achievement}</p>
                </div>
            </div>"""
            
            html_content += """
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="section contact">
        <h2>Let's Connect</h2>
        <p style="font-size: 1.1rem; margin-bottom: 2rem;">Ready to collaborate? I'd love to hear from you!</p>
        <div class="contact-info">
            <div class="contact-item">
                <i class="fas fa-envelope"></i>
                <span>{email}</span>
            </div>
            <div class="contact-item">
                <i class="fas fa-phone"></i>
                <span>{phone}</span>
            </div>"""
            
            if linkedin:
                html_content += f"""
            <div class="contact-item">
                <i class="fab fa-linkedin"></i>
                <a href="{linkedin}" target="_blank" style="color: {colors['primary']};">LinkedIn</a>
            </div>"""
            
            if portfolio:
                html_content += f"""
            <div class="contact-item">
                <i class="fas fa-globe"></i>
                <a href="{portfolio}" target="_blank" style="color: {colors['primary']};">Portfolio</a>
            </div>"""
            
            html_content += f"""
        </div>
    </section>

    <!-- JavaScript -->
    <script>
        // Smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{
                        behavior: 'smooth',
                        block: 'start'
                    }});
                }}
            }});
        }});

        // Fade in animation on scroll
        const observerOptions = {{
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        }};

        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.classList.add('visible');
                }}
            }});
        }}, observerOptions);

        // Observe all fade-in elements
        document.querySelectorAll('.fade-in').forEach(el => {{
            observer.observe(el);
        }});

        // Navbar background on scroll
        window.addEventListener('scroll', () => {{
            const navbar = document.querySelector('.navbar');
            if (window.scrollY > 100) {{
                navbar.style.background = 'rgba(255, 255, 255, 0.98)';
                navbar.style.boxShadow = '0 2px 20px rgba(0,0,0,0.1)';
            }} else {{
                navbar.style.background = 'rgba(255, 255, 255, 0.95)';
                navbar.style.boxShadow = 'none';
            }}
        }});

        // Add typing effect to hero text
        const heroTitle = document.querySelector('.hero-content h1');
        const originalText = heroTitle.textContent;
        heroTitle.textContent = '';
        
        let i = 0;
        const typeWriter = () => {{
            if (i < originalText.length) {{
                heroTitle.textContent += originalText.charAt(i);
                i++;
                setTimeout(typeWriter, 100);
            }}
        }};
        
        setTimeout(typeWriter, 1000);
    </script>
</body>
</html>"""
            
            return html_content
            
        except Exception as e:
            return f"Portfolio generation failed: {str(e)}"


def create_resume_pdf(resume_data, assessment_data=None):
    """Create a professional PDF resume"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=6,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2C3E50')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=6,
        spaceBefore=12,
        textColor=colors.HexColor('#2C3E50'),
        borderWidth=1,
        borderColor=colors.HexColor('#3498DB'),
        borderPadding=3
    )
    
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        alignment=TA_JUSTIFY
    )
    
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=3,
        leftIndent=20,
        bulletIndent=10
    )
    
    story = []
    
    # Header - Name
    personal_info = resume_data.get('personal_info', {})
    name = personal_info.get('name', 'Your Name')
    story.append(Paragraph(name, title_style))
    
    # Contact Information
    contact_parts = []
    if personal_info.get('email'):
        contact_parts.append(personal_info['email'])
    if personal_info.get('phone'):
        contact_parts.append(personal_info['phone'])
    if personal_info.get('location'):
        contact_parts.append(personal_info['location'])
    if personal_info.get('linkedin'):
        contact_parts.append(f"LinkedIn: {personal_info['linkedin']}")
    if personal_info.get('portfolio'):
        contact_parts.append(f"Portfolio: {personal_info['portfolio']}")
    
    if contact_parts:
        contact_line = " | ".join(contact_parts)
        story.append(Paragraph(contact_line, contact_style))
    
    story.append(Spacer(1, 12))
    
    # Professional Summary
    if resume_data.get('professional_summary'):
        story.append(Paragraph("PROFESSIONAL SUMMARY", heading_style))
        story.append(Paragraph(resume_data['professional_summary'], body_style))
        story.append(Spacer(1, 6))
    
    # Experience
    if resume_data.get('experience'):
        story.append(Paragraph("PROFESSIONAL EXPERIENCE", heading_style))
        
        for exp in resume_data['experience']:
            # Job title and company
            title_company = f"<b>{exp.get('title', 'Job Title')}</b> | {exp.get('company', 'Company Name')}"
            if exp.get('location'):
                title_company += f" | {exp['location']}"
            story.append(Paragraph(title_company, body_style))
            
            # Duration
            if exp.get('duration'):
                story.append(Paragraph(f"<i>{exp['duration']}</i>", body_style))
            
            # Achievements
            if exp.get('achievements'):
                for achievement in exp['achievements']:
                    story.append(Paragraph(achievement, bullet_style))
            
            story.append(Spacer(1, 8))
    
    # Education
    if resume_data.get('education'):
        story.append(Paragraph("EDUCATION", heading_style))
        
        for edu in resume_data['education']:
            edu_line = f"<b>{edu.get('degree', 'Degree')}</b>"
            if edu.get('institution'):
                edu_line += f" | {edu['institution']}"
            if edu.get('location'):
                edu_line += f" | {edu['location']}"
            if edu.get('graduation'):
                edu_line += f" | {edu['graduation']}"
            
            story.append(Paragraph(edu_line, body_style))
            
            if edu.get('gpa'):
                story.append(Paragraph(f"GPA: {edu['gpa']}", body_style))
            if edu.get('honors'):
                story.append(Paragraph(f"Honors: {edu['honors']}", body_style))
            
            story.append(Spacer(1, 6))
    
    # Skills
    if resume_data.get('skills'):
        story.append(Paragraph("TECHNICAL SKILLS", heading_style))
        skills = resume_data['skills']
        
        if isinstance(skills, dict):
            for category, skill_list in skills.items():
                if skill_list:
                    category_title = category.replace('_', ' ').title()
                    skills_text = f"<b>{category_title}:</b> {', '.join(skill_list)}"
                    story.append(Paragraph(skills_text, body_style))
        else:
            # Handle simple list format
            skills_text = ", ".join(skills)
            story.append(Paragraph(skills_text, body_style))
        
        story.append(Spacer(1, 6))
    
    # Projects
    if resume_data.get('projects'):
        story.append(Paragraph("PROJECTS", heading_style))
        
        for project in resume_data['projects']:
            project_title = f"<b>{project.get('name', 'Project Name')}</b>"
            story.append(Paragraph(project_title, body_style))
            
            if project.get('description'):
                story.append(Paragraph(project['description'], body_style))
            
            if project.get('link'):
                story.append(Paragraph(f"Link: {project['link']}", body_style))
            
            story.append(Spacer(1, 6))
    
    # Certifications
    if resume_data.get('certifications'):
        story.append(Paragraph("CERTIFICATIONS", heading_style))
        for cert in resume_data['certifications']:
            story.append(Paragraph(f"• {cert}", bullet_style))
        story.append(Spacer(1, 6))
    
    # Achievements
    if resume_data.get('achievements'):
        story.append(Paragraph("ACHIEVEMENTS", heading_style))
        for achievement in resume_data['achievements']:
            story.append(Paragraph(f"• {achievement}", bullet_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def create_assessment_report_pdf(assessment_data, questions_data=None):
    """Create PDF assessment report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        fontSize=20,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph("Resume Assessment Report", title_style))
    story.append(Spacer(1, 20))
    
    # Assessment Results
    story.append(Paragraph("ASSESSMENT RESULTS", styles['Heading2']))
    
    # Score
    score_text = f"Overall Score: <b>{assessment_data.get('overall_score', 'N/A')}/10</b>"
    story.append(Paragraph(score_text, styles['Normal']))
    
    experience_text = f"Experience Level: <b>{assessment_data.get('experience_level', 'Not specified')}</b>"
    story.append(Paragraph(experience_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Strengths
    if assessment_data.get('strengths'):
        story.append(Paragraph("Key Strengths:", styles['Heading3']))
        for strength in assessment_data['strengths']:
            story.append(Paragraph(f"• {strength}", styles['Normal']))
        story.append(Spacer(1, 12))
    
    # Improvements
    if assessment_data.get('improvements'):
        story.append(Paragraph("Areas for Improvement:", styles['Heading3']))
        for improvement in assessment_data['improvements']:
            story.append(Paragraph(f"• {improvement}", styles['Normal']))
        story.append(Spacer(1, 12))
    
    # Recommended Skills
    if assessment_data.get('recommended_skills'):
        story.append(Paragraph("Recommended Skills to Add:", styles['Heading3']))
        for skill in assessment_data['recommended_skills']:
            story.append(Paragraph(f"• {skill}", styles['Normal']))
        story.append(Spacer(1, 12))
    
    # Questions
    if questions_data and questions_data.get('questions'):
        story.append(Paragraph("INTERVIEW PREPARATION QUESTIONS", styles['Heading2']))
        
        for i, q in enumerate(questions_data['questions'], 1):
            question_text = f"<b>Q{i}: {q['question']}</b>"
            story.append(Paragraph(question_text, styles['Normal']))
            story.append(Paragraph(f"Type: {q['type']} | Skill Area: {q['skill_area']}", styles['Normal']))
            story.append(Spacer(1, 8))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

@st.cache_resource
def get_assessment_system():
    return ResumeAssessmentSystem()

def main():
    # Initialize session state
    if 'resume_text' not in st.session_state:
        st.session_state.resume_text = ""
    if 'assessment' not in st.session_state:
        st.session_state.assessment = None
    if 'questions_answered' not in st.session_state:
        st.session_state.questions_answered = False
    if 'user_responses' not in st.session_state:
        st.session_state.user_responses = {}
    if 'improved_resume' not in st.session_state:
        st.session_state.improved_resume = None
    if 'interview_questions' not in st.session_state:
        st.session_state.interview_questions = None

    assessment_system = get_assessment_system()
    
    # Hero Section
    if not st.session_state.resume_text:
        st.markdown("""
        <div class="hero-container">
            <h1 class="hero-title">Assess Your Resume</h1>
            <p class="hero-subtitle">Upload your resume for a comprehensive AI-powered assessment and get an ATS-optimized version that lands more interviews.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Extended content in hero section
        st.markdown("""
        <div style="text-align: center; margin: 3rem 0;">
            <h2 style="color: #374151; margin-bottom: 2rem;">How It Works</h2>
            <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; margin-bottom: 3rem;">
                <div style="background: white; padding: 1.5rem; border-radius: 12px; max-width: 200px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📤</div>
                    <h4 style="margin: 0.5rem 0; color: #374151;">Upload</h4>
                    <p style="margin: 0; color: #6b7280; font-size: 0.9rem;">Upload your PDF resume securely</p>
                </div>
                <div style="background: white; padding: 1.5rem; border-radius: 12px; max-width: 200px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
                    <h4 style="margin: 0.5rem 0; color: #374151;">Analyze</h4>
                    <p style="margin: 0; color: #6b7280; font-size: 0.9rem;">AI analyzes your resume content</p>
                </div>
                <div style="background: white; padding: 1.5rem; border-radius: 12px; max-width: 200px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📝</div>
                    <h4 style="margin: 0.5rem 0; color: #374151;">Customize</h4>
                    <p style="margin: 0; color: #6b7280; font-size: 0.9rem;">Answer questions about your goals</p>
                </div>
                <div style="background: white; padding: 1.5rem; border-radius: 12px; max-width: 200px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📄</div>
                    <h4 style="margin: 0.5rem 0; color: #374151;">Download</h4>
                    <p style="margin: 0; color: #6b7280; font-size: 0.9rem;">Get your optimized resume PDF</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # What Makes Our AI Special section - separate from above
        st.markdown("""
        <div style="background: #f8faff; padding: 2rem; border-radius: 15px; margin: 2rem 0; text-align: center;">
            <h3 style="color: #374151; margin-bottom: 1rem;">✨ What Makes Our AI Special</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Create columns for AI features
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 12px; margin: 0.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <h5 style="color: #667eea; margin-bottom: 0.5rem;">🎯 ATS Optimization</h5>
                <p style="color: #6b7280; margin: 0; font-size: 0.9rem;">Formats your resume to pass Applicant Tracking Systems used by 99% of companies</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 12px; margin: 0.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <h5 style="color: #667eea; margin-bottom: 0.5rem;">📊 Data-Driven</h5>
                <p style="color: #6b7280; margin: 0; font-size: 0.9rem;">Emphasizes quantified achievements that hiring managers actually look for</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 12px; margin: 0.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <h5 style="color: #667eea; margin-bottom: 0.5rem;">🏢 Industry-Specific</h5>
                <p style="color: #6b7280; margin: 0; font-size: 0.9rem;">Tailors keywords and format based on your target industry and role level</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 12px; margin: 0.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <h5 style="color: #667eea; margin-bottom: 0.5rem;">🔄 Instant Results</h5>
                <p style="color: #6b7280; margin: 0; font-size: 0.9rem;">Get your improved resume in minutes, not days or weeks</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Features Section (moved outside of upload condition)
        st.markdown("""
        <div style="margin: 4rem 0;">
            <h2 style="text-align: center; color: #374151; margin-bottom: 3rem;">Why Choose Our AI Resume Assessment</h2>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🔍</div>
                <h3 class="feature-title">In-Depth Analysis</h3>
                <p class="feature-description">Get comprehensive feedback on your resume's strengths, weaknesses, and areas for improvement with detailed scoring.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">📋</div>
                <h3 class="feature-title">Actionable Feedback</h3>
                <p class="feature-description">Receive specific, actionable recommendations to enhance your resume's impact and effectiveness in your industry.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🎯</div>
                <h3 class="feature-title">Improve Your Chances</h3>
                <p class="feature-description">Get an ATS-optimized resume that increases your chances of landing interviews and advancing your career.</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Progress indicators
    def show_progress(current_step):
        steps = ["Upload", "Assess", "Questions", "Optimize", "Download"]
        progress_html = '<div class="progress-container">'
        
        for i, step in enumerate(steps):
            if i < current_step:
                circle_class = "step-completed"
            elif i == current_step:
                circle_class = "step-active"
            else:
                circle_class = "step-pending"
            
            progress_html += f"""
            <div class="progress-step">
                <div class="step-circle {circle_class}">{i+1}</div>
                <span>{step}</span>
            </div>
            """
            
            if i < len(steps) - 1:
                progress_html += '<div style="width: 40px; height: 2px; background: #e5e7eb; margin: 0 1rem;"></div>'
        
        progress_html += '</div>'
        st.markdown(progress_html, unsafe_allow_html=True)
    
    # Step 1: Upload Resume
    if not st.session_state.resume_text:
        show_progress(0)
        
        uploaded_file = st.file_uploader(
            "Choose your PDF resume file", 
            type=['pdf'],
            help="Upload a PDF file containing your resume",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            with st.spinner("📄 Extracting text from your PDF resume..."):
                resume_text = assessment_system.extract_text_from_pdf(uploaded_file)
                st.session_state.resume_text = resume_text
                
            st.markdown("""
            <div class="success-container">
                <h3>✅ Resume Uploaded Successfully!</h3>
                <p>Your resume has been processed and is ready for analysis.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Automatically start assessment
            with st.spinner("🤖 AI is analyzing your resume..."):
                assessment = assessment_system.assess_resume(st.session_state.resume_text)
                st.session_state.assessment = assessment
                
            st.rerun()
    
    # Step 2: Show Assessment Results
    elif st.session_state.assessment and "error" not in st.session_state.assessment and not st.session_state.questions_answered:
        show_progress(1)
        
        st.markdown("""
        <div class="success-container">
            <h2>📊 Resume Analysis Complete</h2>
            <p>Here's what our AI found about your resume</p>
        </div>
        """, unsafe_allow_html=True)
        
        assessment = st.session_state.assessment
        
        # Metrics in a nice layout
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{assessment['overall_score']}/10</div>
                <div class="metric-label">Overall Score</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(assessment.get('strengths', []))}</div>
                <div class="metric-label">Key Strengths</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(assessment.get('current_skills', []))}</div>
                <div class="metric-label">Skills Found</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{assessment.get('experience_level', 'Unknown')}</div>
                <div class="metric-label">Experience Level</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Assessment details
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="feature-card" style="text-align: left;">
                <h4 style="color: #10b981; margin-bottom: 1rem;">✅ Strengths Identified</h4>
            """, unsafe_allow_html=True)
            for strength in assessment['strengths'][:5]:
                st.write(f"• {strength}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card" style="text-align: left;">
                <h4 style="color: #f59e0b; margin-bottom: 1rem;">🎯 Skills Detected</h4>
            """, unsafe_allow_html=True)
            for skill in assessment['current_skills'][:8]:
                st.write(f"• {skill}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Step 3: User Questions
        show_progress(2)
        
        st.markdown("""
        <div style="background: #f8faff; padding: 2rem; border-radius: 15px; margin: 2rem 0;">
            <h2 style="text-align: center; color: #374151; margin-bottom: 1rem;">Tell Us More About You</h2>
            <p style="text-align: center; color: #6b7280;">Answer these questions to create your optimized resume</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("user_questions_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                career_objective = st.text_area(
                    "🎯 What is your career objective?",
                    placeholder="e.g., Seeking a Senior Software Engineer position in AI/ML...",
                    height=120
                )
                
                skills_to_add = st.text_area(
                    "💻 Additional skills to highlight?",
                    placeholder="e.g., Python, AWS, Machine Learning, Leadership...",
                    height=100
                )
                
                target_industry = st.selectbox(
                    "🏢 Target Industry",
                    ["Technology", "Healthcare", "Finance", "Education", "Consulting", 
                     "Marketing", "Sales", "Manufacturing", "Non-profit", "Government", "Other"]
                )
                
                company_size = st.selectbox(
                    "🏭 Company Size Preference",
                    ["Startup (1-50)", "Small (51-200)", "Medium (201-1000)", 
                     "Large (1000+)", "Enterprise (5000+)", "No preference"]
                )
            
            with col2:
                achievements = st.text_area(
                    "🏆 Top career achievements with numbers",
                    placeholder="e.g., Led team of 8 developers, increased performance by 40%...",
                    height=120
                )
                
                recent_projects = st.text_area(
                    "🚀 Recent projects you're proud of",
                    placeholder="e.g., Built recommendation system that increased engagement by 25%...",
                    height=100
                )
                
                target_level = st.selectbox(
                    "📈 Target Position Level",
                    ["Entry Level", "Mid Level", "Senior Level", "Lead/Principal", "Management", "Executive"]
                )
            
            submit_questions = st.form_submit_button("✨ Create My Optimized Resume", type="primary", use_container_width=True)
            
            if submit_questions:
                if career_objective and achievements:
                    st.session_state.user_responses = {
                        'career_objective': career_objective,
                        'achievements': achievements,
                        'skills_to_add': skills_to_add,
                        'recent_projects': recent_projects,
                        'target_industry': target_industry,
                        'target_level': target_level,
                        'company_size': company_size
                    }
                    st.session_state.questions_answered = True
                    
                    # Automatically generate improved resume
                    with st.spinner("🚀 Creating your ATS-optimized resume..."):
                        improved_resume = assessment_system.create_ats_optimized_resume(
                            st.session_state.resume_text,
                            st.session_state.assessment,
                            st.session_state.user_responses
                        )
                        st.session_state.improved_resume = improved_resume
                        
                    # Generate interview questions
                    with st.spinner("🎯 Generating personalized interview questions..."):
                        interview_questions = assessment_system.generate_skill_questions(
                            st.session_state.assessment['current_skills'] + 
                            st.session_state.user_responses['skills_to_add'].split(','),
                            st.session_state.assessment['experience_level']
                        )
                        st.session_state.interview_questions = interview_questions
                        
                    st.success("✅ Your optimized resume is ready!")
                    
                    # Generate cover letter automatically
                    with st.spinner("📝 Creating your personalized cover letter..."):
                        cover_letter = assessment_system.generate_cover_letter(
                            st.session_state.improved_resume,
                            st.session_state.user_responses
                        )
                        st.session_state.cover_letter = cover_letter
                        
                    st.rerun()
                else:
                    st.error("⚠️ Please fill in at least the career objective and achievements fields.")
    
    # Step 4: Show Results and Download
    elif st.session_state.questions_answered and st.session_state.improved_resume:
        if "error" not in st.session_state.improved_resume:
            show_progress(4)
            
            st.markdown("""
            <div class="success-container">
                <h1>🎉 Your Optimized Resume is Ready!</h1>
                <p style="font-size: 1.2rem;">Download your ATS-friendly resume and assessment report</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Improvement highlights
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="feature-card" style="text-align: left;">
                    <h4 style="color: #10b981;">📈 Improvements Made</h4>
                    <ul style="color: #374151;">
                        <li>✅ ATS-optimized formatting</li>
                        <li>✅ Industry-specific keywords</li>
                        <li>✅ Quantified achievements</li>
                        <li>✅ Professional summary enhancement</li>
                        <li>✅ Skills optimization</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                st.markdown("""
                <div class="feature-card" style="text-align: left;">
                    <h4 style="color: #667eea;">📦 What You Get</h4>
                    <ul style="color: #374151;">
                        <li>📄 Professional resume PDF</li>
                        <li>📊 Detailed assessment report</li>
                        <li>❓ Personalized interview questions</li>
                        <li>💡 Career improvement tips</li>
                        <li>🎯 ATS-friendly formatting</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            # Download section
            st.markdown("""
            <h2 style="text-align: center; margin: 2rem 0; color: #374151;">Download Your Documents</h2>
            """, unsafe_allow_html=True)
            
            # Cover Letter Customization Section
            st.markdown("""
            <div style="background: #f8faff; padding: 2rem; border-radius: 15px; margin: 2rem 0;">
                <h3 style="text-align: center; color: #374151; margin-bottom: 1rem;">📝 Customize Your Cover Letter</h3>
                <p style="text-align: center; color: #6b7280;">Optionally provide job details for a more targeted cover letter</p>
            </div>
            """, unsafe_allow_html=True)
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                company_name = st.text_input(
                    "🏢 Company Name (Optional)",
                    placeholder="e.g., Google, Microsoft, Apple...",
                    help="Enter the company name for a more personalized cover letter"
                )
            
            with col_right:
                regenerate_cover_letter = st.button("🔄 Generate Targeted Cover Letter", use_container_width=True)
            
            job_description = st.text_area(
                "📋 Job Description (Optional)",
                placeholder="Paste the job description here to create a highly targeted cover letter...",
                height=100,
                help="Paste the job posting details for maximum relevance"
            )
            
            if regenerate_cover_letter:
                if company_name or job_description:
                    with st.spinner("📝 Creating your targeted cover letter..."):
                        targeted_cover_letter = assessment_system.generate_cover_letter(
                            st.session_state.improved_resume,
                            st.session_state.user_responses,
                            job_description,
                            company_name
                        )
                        st.session_state.cover_letter = targeted_cover_letter
                        st.success("✅ Targeted cover letter generated!")
                        st.rerun()
                else:
                    st.warning("⚠️ Please provide either a company name or job description for targeting.")
            
            # Downloads
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.markdown("""
                <div class="download-container">
                    <h4 style="color: #374151;">📄 Resume PDF</h4>
                    <p style="color: #6b7280;">ATS-optimized resume</p>
                </div>
                """, unsafe_allow_html=True)
                
                pdf_buffer = create_resume_pdf(st.session_state.improved_resume)
                
                st.download_button(
                    label="📥 Resume",
                    data=pdf_buffer.getvalue(),
                    file_name=f"resume_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            with col2:
                st.markdown("""
                <div class="download-container">
                    <h4 style="color: #374151;">📝 Cover Letter</h4>
                    <p style="color: #6b7280;">Personalized cover letter</p>
                </div>
                """, unsafe_allow_html=True)
                
                if hasattr(st.session_state, 'cover_letter'):
                    st.download_button(
                        label="📥 Cover Letter",
                        data=st.session_state.cover_letter,
                        file_name=f"cover_letter_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                else:
                    st.write("Cover letter will be available after resume generation")
            
            with col3:
                st.markdown("""
                <div class="download-container">
                    <h4 style="color: #374151;">📊 Assessment Report</h4>
                    <p style="color: #6b7280;">Detailed feedback</p>
                </div>
                """, unsafe_allow_html=True)
                
                report_buffer = create_assessment_report_pdf(
                    st.session_state.assessment,
                    st.session_state.interview_questions
                )
                
                st.download_button(
                    label="📥 Report",
                    data=report_buffer.getvalue(),
                    file_name=f"assessment_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            with col4:
                st.markdown("""
                <div class="download-container">
                    <h4 style="color: #374151;">🌐 Portfolio Website</h4>
                    <p style="color: #6b7280;">Complete HTML site</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🚀 Generate", use_container_width=True):
                    with st.spinner("Creating your portfolio website..."):
                        portfolio_html = assessment_system.generate_portfolio_website(
                            st.session_state.improved_resume,
                            st.session_state.user_responses
                        )
                        st.session_state.portfolio_html = portfolio_html
                        st.success("Portfolio created!")
                
                if hasattr(st.session_state, 'portfolio_html'):
                    st.download_button(
                        label="📥 Portfolio",
                        data=st.session_state.portfolio_html,
                        file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.html",
                        mime="text/html",
                        use_container_width=True
                    )
            
            with col5:
                st.markdown("""
                <div class="download-container">
                    <h4 style="color: #374151;">🔄 Start Over</h4>
                    <p style="color: #6b7280;">New assessment</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🆕 New Resume", type="secondary", use_container_width=True):
                    # Clear all session state
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
            
            # Preview Sections
            if hasattr(st.session_state, 'cover_letter'):
                with st.expander("📝 Preview Your Cover Letter"):
                    st.text_area("Cover Letter Content", st.session_state.cover_letter, height=400)
            
            # Portfolio Preview
            if hasattr(st.session_state, 'portfolio_html'):
                with st.expander("🌐 Preview Your Portfolio Website"):
                    st.components.v1.html(st.session_state.portfolio_html, height=600, scrolling=True)
            
            # Expandable sections for preview
            with st.expander("👀 Preview Your Optimized Resume Data"):
                st.json(st.session_state.improved_resume)
            
            # Show interview questions
            if st.session_state.interview_questions and "questions" in st.session_state.interview_questions:
                with st.expander("❓ Your Personalized Interview Questions"):
                    for i, q in enumerate(st.session_state.interview_questions['questions'], 1):
                        st.markdown(f"""
                        <div style="padding: 1rem; margin: 0.5rem 0; background: #f8faff; border-radius: 10px;">
                            <strong>Q{i}: {q['question']}</strong><br>
                            <em style="color: #6b7280;">Type: {q['type']} | Focus: {q['skill_area']}</em>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Error handling
    if st.session_state.assessment and "error" in st.session_state.assessment:
        st.error(f"⚠️ Assessment failed: {st.session_state.assessment['error']}")
        st.info("Please check your OpenAI API key and try again.")
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #6b7280; border-top: 1px solid #e5e7eb; margin-top: 3rem;">
        🤖 Powered by OpenAI GPT-4 | ATS-Optimized Professional Resumes
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()