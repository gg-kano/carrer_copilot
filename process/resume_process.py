import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from prompt.extract_resume import generate_resume_extraction_prompt
from typing import List, Dict
import re
import json
import google.generativeai as genai
    
class ResumePreprocessor:
    def __init__(self, api_key = "AIzaSyDMeVeMSCuAPI2YZV9K1bVo8faadFPT9HQ"):
        genai.configure(api_key=api_key)
        self.llm_client = genai.GenerativeModel("gemini-2.5-flash")
        #self.llm_client = genai.Client(api_key=api_key)
        
    def normalize_text(self, text: str) -> str:
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'http[s]?://\S+', '[URL]', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def parse_with_llm(self, resume_text: str) -> Dict[str, str]:
        prompt = generate_resume_extraction_prompt(resume_text)

        response = self.llm_client.generate_content(prompt)
        response_text = response.text.strip()
        try:
       
            data = json.loads(response_text)
        except json.JSONDecodeError:
    
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            data = json.loads(match.group()) if match else {}
        
        for key, val in data.items():
            data[key] = self.normalize_text(val or "")

        data["full_text"] = self.normalize_text(resume_text)
        return data

    def generate_resume_chunks(self, extracted_data, resume_id):
        chunks = []
        
        # Chunk 1: Skills + Experience
        skills_experience = f"""
        Skills: {extracted_data['skills']}
        
        Work Experience:
        {extracted_data['experience']}
        """.strip()
        
        chunks.append({
            "chunk_id": f"{resume_id}_skills_experience",
            "field": "skills_experience",
            "content": skills_experience,
            "metadata": {
                "document_id": resume_id,
                "document_type": "resume",
                "field": "skills_experience"
            }
        })
        
        # Chunk 2: Education + Certifications
        education_certs = f"""
        Education: {extracted_data['education']}
        
        Certifications:
        {extracted_data['certifications']}
        """.strip()
        
        chunks.append({
            "chunk_id": f"{resume_id}_education_certifications",
            "field": "education_certifications",
            "content": education_certs,
            "metadata": {
                "document_id": resume_id,
                "document_type": "resume",
                "field": "education_certifications"
            }
        })
        
        # Chunk 3: Projects + Achievements
        projects_achievements = f"""
        Projects:
        {extracted_data['projects']}
        
        Achievements:
        {extracted_data['achievements']}
        """.strip()
        
        chunks.append({
            "chunk_id": f"{resume_id}_projects_achievements",
            "field": "projects_achievements",
            "content": projects_achievements,
            "metadata": {
                "document_id": resume_id,
                "document_type": "resume",
                "field": "projects_achievements"
            }
        })
        
        return chunks
        
    def preprocess_resume(self, resume_text: str, resume_id: str = None) -> List[Dict[str, str]]:
        try:
            sections = self.parse_with_llm(resume_text) 
            print(f"Extracted sections: {sections}")
            print(f"Using resume ID: {resume_id}")
            return self.generate_resume_chunks(sections, resume_id)
        except Exception as e:
            print(f"Error during resume preprocessing: {e}")
            return []
  
import uuid      
if __name__ == "__main__":
    sample_resume = """
Name: Alex Chen

Professional Summary:
Results-driven AI Engineer with 5+ years of experience designing, training, and deploying machine learning systems in production. Skilled in computer vision, model optimization, and scalable inference pipelines. Proven ability to lead cross-functional teams and deliver business impact in fintech and identity verification domains.

Experience:
AI Engineer | WiseAI | 2020 – Present

Designed and deployed OCR and face recognition models for eKYC verification, improving accuracy by 18%.

Led migration of model serving to a Dockerized microservice architecture using FastAPI and Kubernetes.

Mentored 3 junior engineers on model tuning and performance profiling.

Machine Learning Engineer | VisionX Labs | 2018 – 2020

Developed a real-time image quality scoring model using PyTorch and ONNX.

Implemented model quantization reducing latency by 35% on edge devices.

Collaborated with product managers to integrate ML outputs into customer dashboards.

Education:
B.Eng. in Computer Engineering — National University of Singapore (2018)

Skills:
Machine learning, computer vision, model deployment, project leadership, system design

Tools & Technologies:
Python, PyTorch, TensorFlow, Docker, FastAPI, Kubernetes, AWS, OpenCV, Git

Certifications & Achievements:

AWS Certified Machine Learning – Specialty (2023)

Published “Improving Face Image Quality Assessment for eKYC” at CVPR 2022 Workshop

Led a team that won 1st place in the FinTech Innovation Hackathon (2021)
"""
    processor = ResumePreprocessor(api_key="AIzaSyDMeVeMSCuAPI2YZV9K1bVo8faadFPT9HQ")
    chunks = processor.preprocess_resume(sample_resume)
    for chunk in chunks:
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Field: {chunk['field']}")
        print(f"Content: {chunk['content']}\n")