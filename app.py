from flask import Flask, request, jsonify, send_file
from groq import Groq
import json
from fpdf import FPDF
import io
import textwrap
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from datetime import datetime

app = Flask(__name__)
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

def load_resume_data():
    with open('my resume data.txt', 'r', encoding='utf-8') as file:
        return file.read()

def get_name_from_resume():
    resume_data = load_resume_data()
    # Get the first line which contains the name
    return resume_data.split('\n')[0].strip()

@app.errorhandler(Exception)
def handle_error(error):
    print(f"Error: {str(error)}")
    return jsonify({"error": str(error)}), 500

@app.route('/tailor-resume', methods=['POST'])
def tailor_resume():
    job_description = request.json.get('job_description')
    resume_data = load_resume_data()
    
    prompt = f"""As an expert resume writer, create a highly targeted ATS-optimized resume based on this job description:

{job_description}

Using this background information:
{resume_data}

Instructions for processing (do not include these in output):
1. Analyze the job description for key requirements and skills
2. Rewrite all content to match job requirements
3. Prioritize relevant experiences and skills
4. Include metrics and achievements
5. Use job-specific keywords
6. Remove irrelevant information

Output the resume in exactly this format without any notes or brackets:

ABED KWASMI
[Relevant title matching job]
+90-552-676-25-94 Abedalrahmanqwasmi@gmail.com https://www.linkedin.com/in/abed-kwasmi/ istanbul/turkey

SUMMARY
[Direct professional summary]

EXPERIENCE
[Company and role details]
• [Achievement with metrics]
• [Achievement with metrics]
• [Achievement with metrics]

EDUCATION
[Education details]

TECHNICAL SKILLS
[Relevant grouped skills]

CERTIFICATIONS
[Relevant certifications]

LANGUAGES
[Language list]"""

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.7,
    )
    
    return jsonify({"tailored_resume": response.choices[0].message.content})

@app.route('/create-cover-letter', methods=['POST'])
def create_cover_letter():
    job_description = request.json.get('job_description')
    company_name = request.json.get('company_name')
    resume_data = load_resume_data()
    
    prompt = f"""Write a compelling cover letter for {company_name} based on:
    Job Description: {job_description}
    My Background: {resume_data}
    Make it professional, personalized, and highlight relevant experiences."""
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.7,
    )
    
    return jsonify({"cover_letter": response.choices[0].message.content})

@app.route('/download/<doc_type>', methods=['POST'])
def download_document(doc_type):
    content = request.json.get('content')
    
    if 'format' in request.args and request.args.get('format') == 'txt':
        buffer = io.BytesIO()
        buffer.write(content.encode('utf-8'))
        buffer.seek(0)
        filename = "abed_resume.txt"
        return send_file(
            buffer,
            mimetype='text/plain',
            as_attachment=True,
            download_name=filename
        )
    else:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.4*inch,
            bottomMargin=0.4*inch,
            showBoundary=0,  # Remove page boundary
            allowSplitting=1  # Better content flow
        )

        styles = getSampleStyleSheet()
        
        # Enhanced styles for better organization
        name_style = ParagraphStyle(
            'NameStyle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            spaceAfter=2,
            textColor=colors.black,
            alignment=1  # Center alignment
        )
        
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Normal'],
            fontSize=14,
            leading=16,
            spaceAfter=8,
            textColor=colors.HexColor('#2c3e50'),
            alignment=1  # Center alignment
        )
        
        contact_style = ParagraphStyle(
            'ContactStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            spaceAfter=12,
            alignment=1  # Center alignment
        )
        
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontSize=12,
            leading=14,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.black,
            borderColor=colors.black,
            borderPadding=(0, 0, 0, 0),  # Remove padding
            underlineWidth=1,  # Add underline
            underlineGap=2,  # Gap between text and underline
            underlineOffset=-6  # Position of underline
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            leading=13,
            spaceBefore=1,
            spaceAfter=1
        )
        
        bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=styles['Normal'],
            fontSize=10,
            leading=13,
            leftIndent=20,
            bulletIndent=10,
            spaceBefore=2,
            spaceAfter=2
        )

        # Process content with improved formatting
        story = []
        lines = content.split('\n')
        current_section = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.lower().startswith('powered by'):  # Skip powered by line
                continue
            if line.startswith('www.'):  # Skip website references
                continue
            if not line:
                story.append(Spacer(1, 4))
            elif i < 3:  # Special handling for name and title
                if i == 0:  # Name
                    story.append(Paragraph(line, name_style))
                elif i == 1:  # Title
                    story.append(Paragraph(line, title_style))
                else:  # Contact info
                    story.append(Paragraph(line, contact_style))
            elif line.isupper() and len(line) > 1:  # Section headers
                current_section = line
                story.append(Paragraph(line, section_style))
                story.append(Spacer(1, 2))  # Small space after the line
            elif line.startswith('•'):  # Bullet points
                story.append(Paragraph(line, bullet_style))
            elif current_section == 'SKILLS' and ':' in line:  # Skills section
                category, skills = line.split(':', 1)
                story.append(Paragraph(
                    f'<b>{category}:</b> {skills.strip()}', 
                    normal_style
                ))
            else:  # Normal text
                story.append(Paragraph(line, normal_style))

        filename = "abed_resume.pdf"
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

if __name__ == '__main__':
    app.run(debug=True)
