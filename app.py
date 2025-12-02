import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import json
from typing import List, Dict
import PyPDF2
import io
import os
from pathlib import Path
import base64

# Import your existing modules
from database.chroma_db import ChromaDBStorage
from process.resume_process import ResumePreprocessor
from process.jd_process import JDPreprocessor
from match.resume_jd_matcher import ResumeJDMatcher

class ResumeManagerApp:
    def __init__(self):
        if 'db' not in st.session_state:
            st.session_state.db = ChromaDBStorage(persist_directory="./chroma_db")
        if 'processor' not in st.session_state:
            st.session_state.processor = ResumePreprocessor()
        if 'jd_processor' not in st.session_state:
            st.session_state.jd_processor = JDPreprocessor()
        if 'matcher' not in st.session_state:
            st.session_state.matcher = ResumeJDMatcher()

    def extract_text_from_pdf(self, pdf_file):
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading PDF: {str(e)}")
            return None

    def generate_resume_id_from_name(self, name: str, existing_ids: set = None) -> str:
        """Generate a valid resume ID from a person's name"""
        if not name or name.lower() == "unknown":
            return f"resume_{uuid.uuid4().hex[:8]}"

        # Clean the name: remove special characters, convert to lowercase, replace spaces with underscores
        import re
        clean_name = re.sub(r'[^\w\s-]', '', name)  # Remove special chars except spaces and hyphens
        clean_name = re.sub(r'\s+', '_', clean_name.strip())  # Replace spaces with underscores
        clean_name = clean_name.lower()

        # If name is empty after cleaning, use UUID
        if not clean_name:
            return f"resume_{uuid.uuid4().hex[:8]}"

        # Handle duplicates by adding a number suffix
        base_id = clean_name
        resume_id = base_id
        counter = 1

        if existing_ids:
            while resume_id in existing_ids or st.session_state.db.get_document(resume_id):
                resume_id = f"{base_id}_{counter}"
                counter += 1
        else:
            while st.session_state.db.get_document(resume_id):
                resume_id = f"{base_id}_{counter}"
                counter += 1

        return resume_id

    def _format_resume_summary(self, resume_data: dict) -> str:
        """Format resume JSON data into a readable summary with newlines"""
        summary_parts = []

        # Name
        name = resume_data.get('name', 'Unknown')
        summary_parts.append(f"**👤 Name:** {name}")

        # Skills (top 10)
        skills = resume_data.get('skills', [])
        if skills:
            top_skills = skills[:10]
            skills_str = ', '.join(top_skills)
            if len(skills) > 10:
                skills_str += f" ... (+{len(skills) - 10} more)"
            summary_parts.append(f"**💻 Skills:** {skills_str}")

        # Experience summary
        experience = resume_data.get('experience', [])
        if experience:
            exp_count = len(experience)
            latest_exp = experience[0] if experience else {}
            title = latest_exp.get('title', '')
            company = latest_exp.get('company', '')
            if title and company:
                summary_parts.append(f"**💼 Latest Role:** {title} at {company}")
            summary_parts.append(f"**📊 Total Experience:** {exp_count} position(s)")

        # Education
        education = resume_data.get('education', [])
        if education:
            latest_edu = education[0]
            degree = latest_edu.get('degree', '')
            school = latest_edu.get('school', '')
            if degree:
                edu_str = f"{degree}"
                if school:
                    edu_str += f" from {school}"
                summary_parts.append(f"**🎓 Education:** {edu_str}")

        # Projects count
        projects = resume_data.get('projects', [])
        if projects:
            summary_parts.append(f"**🚀 Projects:** {len(projects)} project(s)")

        return "\n\n".join(summary_parts)

    def display_pdf(self, pdf_bytes: bytes, height: int = 800):
        """Display PDF using base64 encoding and iframe"""
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'''
            <iframe
                src="data:application/pdf;base64,{base64_pdf}"
                width="100%"
                height="{height}px"
                type="application/pdf"
                style="border: 1px solid #ddd; border-radius: 5px;">
            </iframe>
        '''
        st.markdown(pdf_display, unsafe_allow_html=True)

    def process_batch_upload(self, folder_path: str, user_id: str = "", skip_existing: bool = True, use_filename_as_id: bool = True):
        """Process all PDF files in a folder and upload them to the database"""
        try:
            # Find all PDF files in the folder
            pdf_files = list(Path(folder_path).glob("*.pdf"))

            if not pdf_files:
                st.warning(f"⚠️ No PDF files found in folder: {folder_path}")
                return

            st.info(f"📊 Found {len(pdf_files)} PDF file(s) in folder")

            # Statistics
            success_count = 0
            skip_count = 0
            error_count = 0
            results = []
            processed_ids = set()  # Track IDs in this batch to handle duplicates

            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Process each PDF file
            for idx, pdf_path in enumerate(pdf_files):
                filename = pdf_path.stem  # Filename without extension
                status_text.text(f"Processing {idx + 1}/{len(pdf_files)}: {pdf_path.name}")

                try:
                    # Read PDF file as bytes
                    with open(pdf_path, 'rb') as pdf_file:
                        pdf_bytes = pdf_file.read()

                    # Also extract text for storage (fallback)
                    with open(pdf_path, 'rb') as pdf_file:
                        resume_text = self.extract_text_from_pdf(pdf_file)

                    if not resume_text:
                        resume_text = ""  # Use empty string if extraction fails

                    # Use LLM to extract resume information directly from PDF
                    resume_data = st.session_state.processor.parse_with_llm(pdf_bytes, is_pdf=True)

                    # Extract name from LLM response
                    candidate_name = resume_data.get('name', 'Unknown')

                    # Generate resume ID from name
                    if use_filename_as_id:
                        # Use filename if option is checked
                        resume_id = filename
                        # Still check for duplicates
                        if resume_id in processed_ids:
                            base_id = resume_id
                            counter = 1
                            while f"{base_id}_{counter}" in processed_ids:
                                counter += 1
                            resume_id = f"{base_id}_{counter}"
                    else:
                        # Use name extracted by LLM
                        resume_id = self.generate_resume_id_from_name(candidate_name, processed_ids)

                    # Check if already exists in database
                    if skip_existing:
                        existing = st.session_state.db.get_document(resume_id)
                        if existing:
                            skip_count += 1
                            results.append({
                                'file': pdf_path.name,
                                'name': candidate_name,
                                'resume_id': resume_id,
                                'status': 'skipped',
                                'reason': 'Already exists'
                            })
                            progress_bar.progress((idx + 1) / len(pdf_files))
                            continue

                    # Generate chunks from the already-parsed data
                    chunks = st.session_state.processor.generate_resume_chunks(resume_data, resume_id)

                    if not chunks:
                        error_count += 1
                        results.append({
                            'file': pdf_path.name,
                            'name': candidate_name,
                            'resume_id': resume_id,
                            'status': 'error',
                            'reason': 'Failed to process resume'
                        })
                        progress_bar.progress((idx + 1) / len(pdf_files))
                        continue

                    # Optimize chunk sizes (same as in preprocess_resume)
                    from utils.chunk_size_manager import validate_and_split_chunks
                    optimized_chunks = validate_and_split_chunks(chunks)

                    # Store in database (with PDF file and resume JSON as summary)
                    st.session_state.db.store_document(
                        document_id=resume_id,
                        document_type="resume",
                        raw_text=resume_text,
                        user_id=user_id if user_id else None,
                        pdf_bytes=pdf_bytes,  # Store the original PDF
                        summary=json.dumps(resume_data)  # Store the complete resume JSON
                    )

                    st.session_state.db.store_chunks(optimized_chunks)

                    # Track this ID
                    processed_ids.add(resume_id)

                    success_count += 1
                    results.append({
                        'file': pdf_path.name,
                        'name': candidate_name,
                        'resume_id': resume_id,
                        'status': 'success',
                        'chunks': len(optimized_chunks)
                    })

                except Exception as e:
                    error_count += 1
                    results.append({
                        'file': pdf_path.name,
                        'name': candidate_name if 'candidate_name' in locals() else 'N/A',
                        'resume_id': resume_id if 'resume_id' in locals() else 'unknown',
                        'status': 'error',
                        'reason': str(e)
                    })

                # Update progress
                progress_bar.progress((idx + 1) / len(pdf_files))

            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

            # Display summary
            st.markdown("---")
            st.subheader("📊 Batch Upload Summary")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("✅ Success", success_count)

            with col2:
                st.metric("⏭️ Skipped", skip_count)

            with col3:
                st.metric("❌ Errors", error_count)

            with col4:
                st.metric("📄 Total", len(pdf_files))

            # Detailed results
            st.markdown("---")
            st.subheader("📋 Detailed Results")

            # Create DataFrame for better display
            df = pd.DataFrame(results)
            if not df.empty:
                # Color code by status
                def highlight_status(row):
                    if row['status'] == 'success':
                        return ['background-color: #d4edda'] * len(row)
                    elif row['status'] == 'skipped':
                        return ['background-color: #fff3cd'] * len(row)
                    else:
                        return ['background-color: #f8d7da'] * len(row)

                st.dataframe(df, use_container_width=True)

                # Show errors in detail if any
                error_results = [r for r in results if r['status'] == 'error']
                if error_results:
                    with st.expander("❌ Error Details"):
                        for err in error_results:
                            st.error(f"**{err['file']}**: {err.get('reason', 'Unknown error')}")

            if success_count > 0:
                st.success(f"🎉 Successfully uploaded {success_count} resume(s) to the database!")

        except Exception as e:
            st.error(f"❌ Batch upload error: {str(e)}")
            import traceback
            st.error(traceback.format_exc())

    def run(self):
        st.set_page_config(
            page_title="Resume Manager",
            page_icon="📄",
            layout="wide"
        )
        
        st.title("📄 Career Copilot Database Manager")
        st.markdown("---")
        
        # Sidebar for navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.radio(
            "Go to:",
            ["Dashboard",  "View Details", "Match Resumes", "Search & Filter"],
            label_visibility="collapsed"
        )

        if page == "Dashboard":
            self.show_dashboard()
        elif page == "Match Resumes":
            self.show_matching_page()
        elif page == "Search & Filter":
            self.show_search_page()
        elif page == "View Details":
            self.show_details_page()
    
    def show_dashboard(self):
        st.title("🏠 Career Copilot Dashboard")
        st.caption("Your AI-powered recruitment assistant")

        # Get statistics
        all_resumes = st.session_state.db.list_all_documents("resume")
        all_jds = st.session_state.db.list_all_documents("job_description")

        # === SECTION 1: Statistics Overview ===
        st.markdown("### 📊 Statistics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Resumes", len(all_resumes))

        with col2:
            st.metric("Job Descriptions", len(all_jds))

        with col3:
            total_chunks = sum(len(st.session_state.db.get_chunks_by_document(doc['id']))
                             for doc in all_resumes + all_jds)
            st.metric("Total Chunks", total_chunks)

        with col4:
            all_docs = all_resumes + all_jds
            if all_docs:
                latest = max(all_docs, key=lambda x: x['metadata'].get('created_at', ''))
                latest_date = latest['metadata'].get('created_at', 'Unknown')
                if latest_date != 'Unknown':
                    latest_date = latest_date.split()[0]
                st.metric("Last Upload", latest_date)
            else:
                st.metric("Last Upload", "None")

        st.markdown("---")

        # === SECTION 2: Upload Section with Tabs ===
        st.markdown("### 📤 Upload Documents")

        # Create tabs for Resume and JD uploads
        resume_tab, jd_tab = st.tabs(["📄 Upload Resume", "💼 Upload Job Description"])

        # ========== RESUME TAB ==========
        with resume_tab:
            upload_method = st.radio(
                "Choose upload method:",
                ["Single PDF Upload", "Text Input", "Batch Folder Upload"],
                key="resume_upload_method",
                horizontal=True
            )

            if upload_method == "Single PDF Upload":
                self._show_single_resume_upload()
            elif upload_method == "Text Input":
                self._show_text_resume_upload()
            else:  # Batch Folder Upload
                self._show_batch_resume_upload()

        # ========== JD TAB ==========
        with jd_tab:
            upload_method_jd = st.radio(
                "Choose upload method:",
                ["File Upload", "Text Input"],
                key="jd_upload_method",
                horizontal=True
            )

            if upload_method_jd == "File Upload":
                self._show_file_jd_upload()
            else:  # Text Input
                self._show_text_jd_upload()

        st.markdown("---")

        # === SECTION 3: Recent Activity ===
        st.markdown("### 📋 Recent Activity")

        all_docs = []
        for resume in all_resumes:
            metadata = resume['metadata']
            all_docs.append({
                'ID': resume['id'],
                'Type': '📄 Resume',
                'Created At': metadata.get('created_at', 'Unknown'),
                'Chunks': len(st.session_state.db.get_chunks_by_document(resume['id']))
            })

        for jd in all_jds:
            metadata = jd['metadata']
            all_docs.append({
                'ID': jd['id'],
                'Type': '💼 JD',
                'Created At': metadata.get('created_at', 'Unknown'),
                'Chunks': len(st.session_state.db.get_chunks_by_document(jd['id']))
            })

        if all_docs:
            all_docs.sort(key=lambda x: x['Created At'], reverse=True)
            df = pd.DataFrame(all_docs[:10])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("📭 No documents yet. Upload resumes or job descriptions using the tabs above!")

        st.markdown("---")

        # === SECTION 4: Cache Management ===
        st.markdown("### 💾 Cache Management")

        try:
            from utils.cache_manager import create_text_cache
            cache = create_text_cache(cache_dir="./cache/resume_extractions")
            stats = cache.get_stats()

            # Display cache info in compact format
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Cached Files", stats['total_files'])

            with col2:
                st.metric("Cache Size", f"{stats['total_size_mb']:.1f} MB")

            # Clear cache button
            if stats['total_files'] > 0:
                with col3:
                    st.write('')
                    if st.button("🗑️ Clear Cache", type="secondary", use_container_width=True):
                        count = cache.clear_all()
                        st.success(f"✅ Cleared {count} files!")
                        st.rerun()

        except Exception as e:
            st.warning(f"⚠️ Cache not accessible: {str(e)}")

    # ========== Resume Upload Methods ==========
    def _show_single_resume_upload(self):
        """Single PDF resume upload"""
        uploaded_file = st.file_uploader(
            "Choose PDF file",
            type=['pdf'],
            key="single_resume_pdf"
        )

        if uploaded_file:
            st.success(f"📄 Loaded: {uploaded_file.name}")

            col1, col2 = st.columns(2)
            with col1:
                resume_id = st.text_input(
                    "Resume ID (optional)",
                    placeholder="Leave empty for auto-extraction from name",
                    key="single_resume_id"
                )
            with col2:
                user_id = st.text_input(
                    "User ID (optional)",
                    placeholder="e.g., recruiter_name",
                    key="single_resume_user_id"
                )

            if st.button("💾 Save Resume", type="primary", use_container_width=True, key="save_single_resume"):
                self._process_single_resume_upload(uploaded_file, resume_id, user_id)

    def _show_text_resume_upload(self):
        """Text input resume upload"""
        resume_text = st.text_area(
            "Paste Resume Text",
            height=300,
            placeholder="Paste the resume text here...",
            key="text_resume_content"
        )

        col1, col2 = st.columns(2)
        with col1:
            resume_id = st.text_input(
                "Resume ID",
                placeholder="e.g., john_smith",
                key="text_resume_id"
            )
        with col2:
            user_id = st.text_input(
                "User ID (optional)",
                placeholder="e.g., recruiter_name",
                key="text_resume_user_id"
            )

        if st.button("💾 Save Resume", type="primary", use_container_width=True, key="save_text_resume"):
            if not resume_text.strip():
                st.error("❌ Please provide resume text!")
                return
            if not resume_id.strip():
                st.error("❌ Please provide a resume ID!")
                return

            self._process_text_resume_upload(resume_text, resume_id, user_id)

    def _show_batch_resume_upload(self):
        """Batch folder resume upload"""
        st.info("💡 Upload all PDF files from a folder")

        folder_path = st.text_input(
            "Folder Path",
            placeholder=r"e.g., C:\Users\Documents\Resumes",
            key="batch_folder_path"
        )

        col1, col2 = st.columns(2)
        with col1:
            user_id = st.text_input(
                "User ID for all (optional)",
                placeholder="e.g., batch_2024",
                key="batch_user_id"
            )
        with col2:
            skip_existing = st.checkbox("Skip existing", value=True, key="batch_skip")

        use_filename = st.checkbox(
            "Use filename as ID (otherwise use candidate name)",
            value=False,
            key="batch_use_filename"
        )

        if st.button("📁 Start Batch Upload", type="primary", use_container_width=True, key="start_batch"):
            if not folder_path.strip():
                st.error("❌ Please provide folder path!")
            elif not os.path.exists(folder_path):
                st.error(f"❌ Folder not found: {folder_path}")
            else:
                self.process_batch_upload(folder_path, user_id, skip_existing, use_filename)

    # ========== JD Upload Methods ==========
    def _show_file_jd_upload(self):
        """File upload for JD"""
        uploaded_file = st.file_uploader(
            "Choose file",
            type=['pdf', 'txt', 'md'],
            key="file_jd_upload"
        )

        if uploaded_file:
            st.success(f"📄 Loaded: {uploaded_file.name}")

            col1, col2 = st.columns(2)
            with col1:
                jd_id = st.text_input(
                    "JD ID",
                    value=uploaded_file.name.split('.')[0],
                    key="file_jd_id"
                )
            with col2:
                user_id = st.text_input(
                    "User ID (optional)",
                    placeholder="e.g., hr_team",
                    key="file_jd_user_id"
                )

            if st.button("💾 Save JD", type="primary", use_container_width=True, key="save_file_jd"):
                self._process_file_jd_upload(uploaded_file, jd_id, user_id)

    def _show_text_jd_upload(self):
        """Text input for JD"""
        jd_text = st.text_area(
            "Paste Job Description",
            height=300,
            placeholder="Paste the job description here...",
            key="text_jd_content"
        )

        col1, col2 = st.columns(2)
        with col1:
            jd_id = st.text_input(
                "JD ID",
                placeholder="e.g., senior_developer",
                key="text_jd_id"
            )
        with col2:
            user_id = st.text_input(
                "User ID (optional)",
                placeholder="e.g., hr_team",
                key="text_jd_user_id"
            )

        if st.button("💾 Save JD", type="primary", use_container_width=True, key="save_text_jd"):
            if not jd_text.strip():
                st.error("❌ Please provide JD text!")
                return
            if not jd_id.strip():
                st.error("❌ Please provide a JD ID!")
                return

            self._process_text_jd_upload(jd_text, jd_id, user_id)

    # ========== Resume Processing Methods ==========
    def _process_single_resume_upload(self, uploaded_file, resume_id_input: str, user_id: str):
        """Process single PDF resume upload"""
        try:
            with st.spinner("⚡ Processing resume..."):
                # Read PDF bytes
                pdf_bytes = uploaded_file.read()
                uploaded_file.seek(0)

                # Extract text
                resume_text = self.extract_text_from_pdf(uploaded_file)
                if not resume_text:
                    resume_text = ""

                # Extract data using LLM
                resume_data = st.session_state.processor.parse_with_llm(pdf_bytes, is_pdf=True)
                candidate_name = resume_data.get('name', 'Unknown')

                # Generate ID
                if resume_id_input.strip():
                    resume_id = resume_id_input.strip()
                else:
                    resume_id = self.generate_resume_id_from_name(candidate_name)

                # Check exists
                if st.session_state.db.get_document(resume_id):
                    st.error(f"❌ Resume '{resume_id}' already exists!")
                    return

                # Generate chunks
                chunks = st.session_state.processor.generate_resume_chunks(resume_data, resume_id)
                from utils.chunk_size_manager import validate_and_split_chunks
                optimized_chunks = validate_and_split_chunks(chunks)

                # Store
                st.session_state.db.store_document(
                    document_id=resume_id,
                    document_type="resume",
                    raw_text=resume_text,
                    user_id=user_id if user_id else None,
                    pdf_bytes=pdf_bytes,
                    summary=json.dumps(resume_data)
                )
                st.session_state.db.store_chunks(optimized_chunks)

                st.success(f"✅ Resume saved: **{resume_id}** ({candidate_name})")
                st.success(f"📊 {len(optimized_chunks)} chunks generated")

                # Clear file uploader state
                if 'single_resume_pdf' in st.session_state:
                    del st.session_state['single_resume_pdf']

                st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

    def _process_text_resume_upload(self, resume_text: str, resume_id: str, user_id: str):
        """Process text resume upload"""
        try:
            with st.spinner("⚡ Processing resume..."):
                # Check exists
                if st.session_state.db.get_document(resume_id):
                    st.error(f"❌ Resume '{resume_id}' already exists!")
                    return

                # Process resume
                chunks, resume_data = st.session_state.processor.preprocess_resume(resume_text, resume_id, is_pdf=False)

                if not chunks:
                    st.error("❌ Failed to process resume")
                    return

                # Store
                st.session_state.db.store_document(
                    document_id=resume_id,
                    document_type="resume",
                    raw_text=resume_text,
                    user_id=user_id if user_id else None,
                    summary=json.dumps(resume_data)
                )
                st.session_state.db.store_chunks(chunks)

                st.success(f"✅ Resume saved: **{resume_id}**")
                st.success(f"📊 {len(chunks)} chunks generated")

                # Clear text input state
                if 'text_resume_content' in st.session_state:
                    del st.session_state['text_resume_content']
                if 'text_resume_id' in st.session_state:
                    del st.session_state['text_resume_id']

                st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

    # ========== JD Processing Methods ==========
    def _process_file_jd_upload(self, uploaded_file, jd_id: str, user_id: str):
        """Process file JD upload"""
        try:
            with st.spinner("⚡ Processing JD..."):
                file_extension = uploaded_file.name.split('.')[-1].lower()

                # Read content
                if file_extension == 'pdf':
                    pdf_bytes = uploaded_file.read()
                    uploaded_file.seek(0)
                    jd_text = self.extract_text_from_pdf(uploaded_file)
                    if not jd_text:
                        jd_text = ""
                else:
                    jd_text = str(uploaded_file.read(), "utf-8")
                    pdf_bytes = None

                if not jd_text.strip():
                    st.error("❌ No text content found!")
                    return

                # Check exists
                if st.session_state.db.get_document(jd_id):
                    st.error(f"❌ JD '{jd_id}' already exists!")
                    return

                # Extract structured data using LLM
                jd_data = st.session_state.jd_processor.parse_with_llm(jd_text)

                # Generate chunks from the parsed data
                chunks = st.session_state.jd_processor.generate_hybrid_chunks(jd_data, jd_id)

                if not chunks:
                    st.error("❌ Failed to process JD")
                    return

                # Optimize chunk sizes
                from utils.chunk_size_manager import validate_and_split_chunks
                optimized_chunks = validate_and_split_chunks(chunks)

                # Store
                st.session_state.db.store_document(
                    document_id=jd_id,
                    document_type="job_description",
                    raw_text=jd_text,
                    user_id=user_id if user_id else None,
                    pdf_bytes=pdf_bytes,
                    summary=json.dumps(jd_data)
                )
                st.session_state.db.store_chunks(optimized_chunks)

                st.success(f"✅ JD saved: **{jd_id}**")
                st.success(f"📊 {len(optimized_chunks)} chunks generated")

                # Clear file uploader state
                if 'file_jd_upload' in st.session_state:
                    del st.session_state['file_jd_upload']

                st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

    def _process_text_jd_upload(self, jd_text: str, jd_id: str, user_id: str):
        """Process text JD upload"""
        try:
            with st.spinner("⚡ Processing JD..."):
                # Check exists
                if st.session_state.db.get_document(jd_id):
                    st.error(f"❌ JD '{jd_id}' already exists!")
                    return

                # Extract structured data using LLM
                jd_data = st.session_state.jd_processor.parse_with_llm(jd_text)

                # Generate chunks from the parsed data
                chunks = st.session_state.jd_processor.generate_hybrid_chunks(jd_data, jd_id)

                if not chunks:
                    st.error("❌ Failed to process JD")
                    return

                # Optimize chunk sizes
                from utils.chunk_size_manager import validate_and_split_chunks
                optimized_chunks = validate_and_split_chunks(chunks)

                # Store
                st.session_state.db.store_document(
                    document_id=jd_id,
                    document_type="job_description",
                    raw_text=jd_text,
                    user_id=user_id if user_id else None,
                    summary=json.dumps(jd_data)
                )
                st.session_state.db.store_chunks(optimized_chunks)

                st.success(f"✅ JD saved: **{jd_id}**")
                st.success(f"📊 {len(optimized_chunks)} chunks generated")

                # Clear text input state
                if 'text_jd_content' in st.session_state:
                    del st.session_state['text_jd_content']
                if 'text_jd_id' in st.session_state:
                    del st.session_state['text_jd_id']

                st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

    def show_matching_page(self):
        st.header("🎯 Match Resumes with Job Description")

        # Get all documents
        all_resumes = st.session_state.db.list_all_documents("resume")
        all_jds = st.session_state.db.list_all_documents("job_description")

        if not all_jds:
            st.warning("⚠️ No job descriptions available. Please upload a job description first.")
            return

        if not all_resumes:
            st.warning("⚠️ No resumes available. Please upload resumes first.")
            return

        # Create two-column layout: Left for configuration, Right for JD preview
        config_col, preview_col = st.columns([1.5, 1])

        with config_col:
            # Step 1: Select Matching Mode
            st.markdown("### 1️⃣ Matching Mode")
            matching_mode = st.selectbox(
                "Choose mode:",
                [
                    "⚡ Rough Mode - Fast vector similarity (seconds)",
                    "🚀 Hybrid Mode - Smart filter + AI analysis (recommended)",
                    "🎯 Precise Mode - Deep AI evaluation (thorough)"
                ],
                index=1,
                label_visibility="collapsed"
            )

            is_rough_mode = matching_mode.startswith("⚡")
            is_hybrid_mode = matching_mode.startswith("🚀")
            is_precise_mode = matching_mode.startswith("🎯")

            st.markdown("---")

            # Step 2: Select Job Description
            st.markdown("### 2️⃣ Job Description")
            jd_options = [jd['id'] for jd in all_jds]
            selected_jd = st.selectbox(
                "Select JD:",
                jd_options,
                label_visibility="collapsed"
            )

            st.markdown("---")

            # Step 3: Configuration
            st.markdown("### 3️⃣ Configuration")

            if is_rough_mode:
                top_k = st.slider(
                    "Top chunks to retrieve:",
                    min_value=10,
                    max_value=200,
                    value=50,
                    step=10
                )
                selected_resumes = None
                precise_top_n = None
                st.caption(f"📊 Will search across all {len(all_resumes)} resumes")

            elif is_hybrid_mode:
                rough_top_k = st.slider(
                    "Rough filter chunks:",
                    min_value=20,
                    max_value=200,
                    value=50,
                    step=10
                )
                precise_top_n = st.slider(
                    "Top N for AI analysis:",
                    min_value=3,
                    max_value=20,
                    value=10,
                    step=1
                )
                top_k = rough_top_k
                selected_resumes = None
                st.caption(f"📊 Filter {len(all_resumes)} resumes → Analyze top {precise_top_n}")

            else:  # Precise mode
                select_all = st.checkbox("Select all resumes", value=True)

                if select_all:
                    selected_resumes = [resume['id'] for resume in all_resumes]
                    st.caption(f"📊 Selected {len(selected_resumes)} resumes")
                else:
                    resume_options = [resume['id'] for resume in all_resumes]
                    selected_resumes = st.multiselect(
                        "Choose resumes:",
                        resume_options,
                        default=[]
                    )
                top_k = None
                precise_top_n = None

            st.markdown("---")

            # Run Button
            match_button = st.button(
                "🚀 Run Matching Analysis",
                type="primary",
                use_container_width=True
            )

        # Right column: JD Preview
        with preview_col:
            st.markdown("### 📄 Job Description Preview")

            # Get JD document
            jd_doc = st.session_state.db.get_document(selected_jd)

            if jd_doc:
                raw_text = jd_doc.get('raw_text', 'No content available')

                # Display in a box
                with st.container():
                    st.markdown(f"**ID:** `{selected_jd}`")

                    # Show preview in expander
                    with st.expander("View Full Content", expanded=False):
                        st.text_area(
                            "Content",
                            raw_text,
                            height=400,
                            disabled=True,
                            label_visibility="collapsed"
                        )

                    # Show summary
                    preview_text = raw_text[:300] + "..." if len(raw_text) > 300 else raw_text
                    st.markdown("**Preview:**")
                    st.info(preview_text)

                    # Show metadata
                    chunks = st.session_state.db.get_chunks_by_document(selected_jd)
                    st.caption(f"📊 {len(chunks)} chunks | {len(raw_text)} characters")
            else:
                st.warning("⚠️ Could not load JD")

        # Matching logic (outside columns)
        st.markdown("---")

        if match_button:
            if is_precise_mode and not selected_resumes:
                st.error("❌ Please select at least one resume to match!")
                return

            try:
                # Get JD document and chunks (needed for all modes)
                jd_doc = st.session_state.db.get_document(selected_jd)
                if not jd_doc:
                    st.error("❌ Job description not found!")
                    return

                jd_text = jd_doc.get('raw_text', '')
                jd_chunks = st.session_state.db.get_chunks_by_document(selected_jd)

                if is_rough_mode:
                    # Rough Mode: Use semantic search only
                    with st.spinner(f"⚡ Running rough matching across all resumes..."):
                        if not jd_text:
                            st.error("❌ Job description has no text!")
                            return

                        results = st.session_state.matcher.rough_match_resumes(
                            db_storage=st.session_state.db,
                            jd_text=jd_text,
                            top_k=top_k
                        )

                        st.session_state.match_results = results
                        st.session_state.matching_mode = 'rough'

                elif is_hybrid_mode:
                    # Hybrid Mode: Rough filter + Precise analysis on top N
                    with st.spinner(f"🚀 Running hybrid matching (filter all, analyze top {precise_top_n})..."):
                        if not jd_text:
                            st.error("❌ Job description has no text!")
                            return

                        if not jd_chunks:
                            st.error("❌ No chunks found for selected job description!")
                            return

                        results = st.session_state.matcher.hybrid_match_resumes(
                            db_storage=st.session_state.db,
                            jd_text=jd_text,
                            jd_chunks=jd_chunks,
                            rough_top_k=top_k,
                            precise_top_n=precise_top_n
                        )

                        st.session_state.match_results = results
                        st.session_state.matching_mode = 'hybrid'

                else:
                    # Precise Mode: LLM analysis on all selected
                    with st.spinner(f"🎯 Running precise matching for {len(selected_resumes)} resumes..."):
                        if not jd_chunks:
                            st.error("❌ No chunks found for selected job description!")
                            return

                        # Prepare resume chunks list
                        resume_chunks_list = []
                        for resume_id in selected_resumes:
                            resume_chunks = st.session_state.db.get_chunks_by_document(resume_id)
                            if resume_chunks:
                                resume_chunks_list.append((resume_id, resume_chunks))

                        results = st.session_state.matcher.batch_match_resumes(
                            resume_chunks_list,
                            jd_chunks
                        )

                        st.session_state.match_results = results
                        st.session_state.matching_mode = 'precise'

            except Exception as e:
                st.error(f"❌ Matching error: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
                return

        # Display Results
        if 'match_results' in st.session_state and st.session_state.match_results:
            results = st.session_state.match_results
            display_mode = st.session_state.get('matching_mode', 'precise')

            # Results Header
            st.markdown("---")
            st.markdown("## 📊 Matching Results")

            # Mode indicator with metrics in one row
            col_mode, col1, col2, col3, col4 = st.columns([2, 1, 1, 1, 1])

            with col_mode:
                if display_mode == 'rough':
                    st.markdown("**Mode:** ⚡ Rough (Vector Similarity)")
                elif display_mode == 'hybrid':
                    st.markdown("**Mode:** 🚀 Hybrid (Filter + AI)")
                    precise_count = sum(1 for r in results if r.get('matching_mode') == 'hybrid')
                    rough_only_count = sum(1 for r in results if r.get('matching_mode') == 'hybrid_rough_only')
                    st.caption(f"{precise_count} AI analyzed | {rough_only_count} filtered")
                else:
                    st.markdown("**Mode:** 🎯 Precise (AI Analysis)")

            with col1:
                qualified_count = sum(1 for r in results if r.get('qualified', False))
                st.metric("Qualified", qualified_count)

            with col2:
                avg_score = sum(r.get('match_score', 0) for r in results) / len(results)
                st.metric("Avg Score", f"{avg_score:.0f}")

            with col3:
                strong_matches = sum(1 for r in results if r.get('recommendation') == 'STRONG_MATCH')
                st.metric("Strong", strong_matches)

            with col4:
                st.metric("Total", len(results))

            st.markdown("---")

            # Individual Results - Compact view
            for idx, result in enumerate(results, 1):
                resume_id = result.get('resume_id', 'Unknown')
                match_score = result.get('match_score', 0)
                recommendation = result.get('recommendation', 'N/A')
                summary = result.get('summary', 'No summary available')

                
                rec_emojis = {
                    'STRONG_MATCH': '🟢',
                    'GOOD_MATCH': '🟡',
                    'PARTIAL_MATCH': '🟠',
                    'NOT_MATCH': '🔴'
                }
                rec_emoji = rec_emojis.get(recommendation, '⚪')

                # Compact header with key info
                with st.expander(
                    f"{rec_emoji} #{idx}. {resume_id} • Score: {match_score}/100 • {recommendation}",
                    expanded=(idx <= 3)
                ):
                    # Summary in info box
                    st.info(f"💡 {summary}")

                    st.markdown("---")

                    # Display based on mode and result type
                    result_mode = result.get('matching_mode', display_mode)

                    if result_mode in ['rough', 'hybrid_rough_only']:
                        # Rough mode or hybrid rough-only: Show matching statistics and chunks
                        if result_mode == 'hybrid_rough_only':
                            st.warning("⚠️ " + result.get('note', 'Filtered out in rough matching'))

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Matching Chunks", result.get('matching_chunks_count', 0))

                        with col2:
                            st.metric("Avg Similarity", f"{result.get('average_similarity', 0):.2f}")

                        with col3:
                            st.metric("Total Similarity", f"{result.get('total_similarity', 0):.2f}")

                        # Show top matching chunks
                        st.markdown("---")
                        st.markdown("### 🔍 Top Matching Chunks")

                        top_chunks = result.get('top_matching_chunks', [])
                        if top_chunks:
                            for i, chunk in enumerate(top_chunks, 1):
                                with st.expander(f"Chunk #{i} - {chunk.get('field', 'unknown')} (Similarity: {chunk.get('similarity', 0):.2f})"):
                                    st.write(f"**Chunk ID:** {chunk.get('chunk_id')}")
                                    st.write(f"**Field:** {chunk.get('field')}")
                                    st.write(f"**Content Preview:**")
                                    st.write(chunk.get('content', 'N/A'))
                        else:
                            st.info("No chunk details available")

                    else:
                        # Precise or hybrid mode: Show detailed analysis
                        if result_mode == 'hybrid':
                            # Show rough matching info for hybrid
                            st.info(f"🔍 Rough Filter Results: Score {result.get('rough_match_score', 0):.1f} | "
                                   f"Similarity {result.get('rough_similarity', 0):.2f} | "
                                   f"{result.get('rough_matching_chunks', 0)} chunks")
                            st.markdown("---")

                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("### 💪 Strengths")
                            strengths = result.get('strengths', [])
                            if strengths:
                                for strength in strengths:
                                    st.markdown(f"• {strength}")
                            else:
                                st.info("No strengths listed")

                        with col2:
                            st.markdown("### ⚠️ Weaknesses")
                            weaknesses = result.get('weaknesses', [])
                            if weaknesses:
                                for weakness in weaknesses:
                                    st.markdown(f"• {weakness}")
                            else:
                                st.info("No weaknesses listed")

                        # Detailed Analysis
                        st.markdown("---")
                        st.markdown("### 📊 Detailed Analysis")

                        detailed = result.get('detailed_analysis', {})

                        if detailed:
                            col1, col2, col3, col4 = st.columns(4)

                            with col1:
                                skills = detailed.get('skills_match', {})
                                st.metric("Skills", f"{skills.get('score', 0)}/100")
                                with st.expander("Details"):
                                    st.write(skills.get('details', 'N/A'))

                            with col2:
                                experience = detailed.get('experience_match', {})
                                st.metric("Experience", f"{experience.get('score', 0)}/100")
                                with st.expander("Details"):
                                    st.write(experience.get('details', 'N/A'))

                            with col3:
                                education = detailed.get('education_match', {})
                                st.metric("Education", f"{education.get('score', 0)}/100")
                                with st.expander("Details"):
                                    st.write(education.get('details', 'N/A'))

                        with col4:
                            cultural = detailed.get('cultural_fit', {})
                            st.metric("Cultural Fit", f"{cultural.get('score', 0)}/100")
                            with st.expander("Details"):
                                st.write(cultural.get('details', 'N/A'))

                    # Next Steps
                    st.markdown("---")
                    st.markdown("### 🎯 Recommendation")
                    next_steps = result.get('next_steps', 'No recommendation provided')
                    st.info(next_steps)

                    # Debug info (optional)
                    if result.get('error'):
                        st.error(f"**Error:** {result['error']}")

            # Export Results
            st.markdown("---")
            st.subheader("💾 Export Results")

            col1, col2 = st.columns(2)

            with col1:
                # Export as JSON
                json_str = json.dumps(results, indent=2)
                st.download_button(
                    label="📥 Download as JSON",
                    data=json_str,
                    file_name=f"match_results_{selected_jd}.json",
                    mime="application/json",
                    use_container_width=True
                )

            with col2:
                # Export as CSV
                import io
                csv_data = []
                for r in results:
                    csv_data.append({
                        'Resume ID': r.get('resume_id'),
                        'Qualified': r.get('qualified'),
                        'Match Score': r.get('match_score'),
                        'Recommendation': r.get('recommendation'),
                        'Summary': r.get('summary')
                    })

                df = pd.DataFrame(csv_data)
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)

                st.download_button(
                    label="📥 Download as CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"match_results_{selected_jd}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    def show_search_page(self):
        st.header("🔍 Search & Filter Resumes")
        
        # Search options
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_query = st.text_input(
                "Search Query",
                placeholder="e.g., Python machine learning, frontend React, data science..."
            )
        
        with col2:
            top_k = st.number_input("Max Results", min_value=1, max_value=50, value=10)
        
        # Filter options
        st.subheader("🎛️ Filters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            document_type = st.selectbox(
                "Document Type",
                ["All", "resume", "job_description"]
            )
            document_type = None if document_type == "All" else document_type
        
        with col2:
            field_filter = st.selectbox(
                "Field Filter",
                ["All", "skills", "experience", "education", "summary", "certifications"]
            )
            field_filter = None if field_filter == "All" else field_filter
        
        with col3:
            min_similarity = st.slider("Minimum Similarity", -1.0, 1.0, 0.1, 0.05)
        
        # Search button
        if st.button("🔍 Search", type="primary", use_container_width=True):
            if not search_query.strip():
                st.warning("⚠️ Please enter a search query!")
                return
            
            try:
                with st.spinner("Searching..."):
                    results = st.session_state.db.search_similar_chunks(
                        query_text=search_query,
                        document_type=document_type,
                        field=field_filter,
                        top_k=top_k
                    )
                    st.write(f"Total results found: {len(results)}")
                    st.write([r['similarity'] for r in results])
                    # Filter by similarity
                    filtered_results = [r for r in results if r['similarity'] >= min_similarity]
                
                if not filtered_results:
                    st.info("🤷‍♂️ No results found matching your criteria.")
                    return
                
                st.success(f"✅ Found {len(filtered_results)} results")
                
                # Display results
                for i, result in enumerate(filtered_results, 1):
                    with st.expander(f"Result #{i} - {result['chunk_id']} (Similarity: {result['similarity']:.2%})"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write("**Content:**")
                            st.write(result['content'])
                        
                        with col2:
                            st.write("**Metadata:**")
                            metadata = result['metadata']
                            for key, value in metadata.items():
                                st.write(f"**{key}:** {value}")
                            
                            st.write(f"**Field:** {result['metadata'].get('field', 'Unknown')}")
                            st.write(f"**Similarity:** {result['similarity']:.2%}")
                
            except Exception as e:
                st.error(f"❌ Search error: {str(e)}")
    
    def show_details_page(self):
        st.header("📊 Detailed View")

        # Get all documents
        all_resumes = st.session_state.db.list_all_documents("resume")
        all_jds = st.session_state.db.list_all_documents("job_description")

        if not all_resumes and not all_jds:
            st.info("📭 No documents in database yet.")
            return

        # View type selector
        view_type = st.radio(
            "Select view type:",
            ["📄 View Resumes", "💼 View Job Descriptions"],
            horizontal=True
        )

        st.markdown("---")

        if view_type == "📄 View Resumes":
            self.show_resume_table_view(all_resumes)
        else:
            self.show_jd_table_view(all_jds)

    def show_resume_table_view(self, all_resumes: list):
        """Display resumes in a table format with summary and categorized chunks"""
        if not all_resumes:
            st.info("📭 No resumes in database yet.")
            return

        st.subheader(f"📄 All Resumes ({len(all_resumes)} total)")

        # Build table data
        table_data = []

        if len(all_resumes) > 0:
            for idx, resume in enumerate(all_resumes):
                resume_id = resume['id']

                # Get document metadata
                document = st.session_state.db.get_document(resume_id)
                raw_text = document.get('raw_text', 'N/A') if document else 'N/A'
                has_pdf = document.get('metadata', {}).get('has_pdf', 'false') == 'true' if document else False

                # Get summary (resume JSON) from metadata
                summary_json_str = document.get('metadata', {}).get('summary') if document else None

                # Parse the resume JSON
                if summary_json_str:
                    try:
                        resume_data = json.loads(summary_json_str)
                        summary = json.dumps(resume_data, indent=2)
                    except:
                        summary = 'Summary format error'
                else:
                    summary = 'No summary available'

                table_data.append({
                    'resume_id': resume_id,
                    'summary': summary,
                    'raw_text': raw_text,
                    'has_pdf': has_pdf
                })

        # Display table
        st.markdown("---")

        for idx, row in enumerate(table_data):
            with st.container():
                st.markdown(f"### {idx + 1}. {row['resume_id']}")

                # Summary (JSON from LLM)
                st.markdown("**📝 Extracted MESSAGE (LLM):**")
                if row['summary'] not in ['Summary format error', 'No summary available']:
                    st.json(row['summary'])
                else:
                    st.info(row['summary'])

                # Create columns for buttons
                col1, _, col3 = st.columns([1.5, 1, 1])
                with col1:
                    # Raw content button
                    if st.button(f"📄 Raw Content", key=f"raw_{idx}"):
                        st.session_state[f"show_raw_{idx}"] = not st.session_state.get(f"show_raw_{idx}", False)

                # Show content based on button clicks
                if st.session_state.get(f"show_raw_{idx}", False):
                    with st.expander("📄 Raw Resume Content", expanded=True):
                        # Check if PDF is available
                        if row['has_pdf']:
                            st.markdown("### 📄 Original PDF Document")

                            # Get PDF bytes
                            pdf_bytes = st.session_state.db.get_pdf_file(row['resume_id'])

                            if pdf_bytes:
                                # Create download button
                                st.download_button(
                                    label="⬇️ Download PDF",
                                    data=pdf_bytes,
                                    file_name=f"{row['resume_id']}.pdf",
                                    mime="application/pdf",
                                    key=f"download_pdf_{idx}"
                                )

                                st.markdown("---")

                                # Display PDF inline
                                try:
                                    self.display_pdf(pdf_bytes, height=600)
                                except Exception as e:
                                    st.error(f"Could not display PDF: {str(e)}")
                                    st.markdown("**Extracted Text Content:**")
                                    st.text_area("Full Content", row['raw_text'], height=300, disabled=True, key=f"raw_content_text_{idx}")
                            else:
                                st.warning("PDF file not found. Showing extracted text instead.")
                                st.text_area("Full Content", row['raw_text'], height=300, disabled=True, key=f"raw_content_{idx}")
                        else:
                            # No PDF, show text
                            st.markdown("**Extracted Text Content:**")
                            st.text_area("Full Content", row['raw_text'], height=300, disabled=True, key=f"raw_content_{idx}")

                with col3:
                    if st.button(f"🗑️ Delete", key=f"delete_{idx}", type="secondary"):
                        st.session_state[f"confirm_delete_{idx}"] = not st.session_state.get(f"confirm_delete_{idx}", False)

                if st.session_state.get(f"confirm_delete_{idx}", False):
                    st.warning(f"⚠️ Are you sure you want to delete {row['resume_id']}?")
                    col_confirm1, col_confirm2 = st.columns([1, 1])
                    with col_confirm1:
                        if st.button("✅ Yes, Delete", key=f"confirm_yes_{idx}", type="primary"):
                            try:
                                st.session_state.db.delete_document(row['resume_id'])
                                st.success(f"✅ Resume {row['resume_id']} deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                    with col_confirm2:
                        if st.button("❌ Cancel", key=f"confirm_no_{idx}"):
                            st.session_state[f"confirm_delete_{idx}"] = False
                            st.rerun()

                st.markdown("---")

    def show_jd_table_view(self, all_jds: list):
        """Display job descriptions in a table format aligned with resume view"""
        if not all_jds:
            st.info("📭 No job descriptions in database yet.")
            return

        st.subheader(f"💼 All Job Descriptions ({len(all_jds)} total)")
        st.markdown("---")

        for idx, jd in enumerate(all_jds):
            jd_id = jd['id']
            document = st.session_state.db.get_document(jd_id)
            chunks = st.session_state.db.get_chunks_by_document(jd_id)
            raw_text = document.get('raw_text', 'N/A')

            with st.container():
                st.markdown(f"### {idx + 1}. {jd_id}")

                # Get summary (JD JSON) from metadata
                summary_json_str = document.get('metadata', {}).get('summary') if document else None

                # Display extracted JSON if available
                st.markdown("**📝 Extracted JSON (LLM):**")
                if summary_json_str:
                    try:
                        jd_data = json.loads(summary_json_str)
                        st.json(jd_data)
                    except:
                        st.info('Summary format error')
                        # Fallback to preview
                        preview_text = raw_text[:300] + "..." if len(raw_text) > 300 else raw_text
                        st.info(preview_text)
                else:
                    st.info('No structured data available')
                    # Fallback to preview
                    preview_text = raw_text[:300] + "..." if len(raw_text) > 300 else raw_text
                    st.info(preview_text)

                # Create columns for buttons
                col1, col2, col3 = st.columns([1.5, 1, 1])
                with col1:
                    # Raw content button
                    if st.button(f"📄 Full Content", key=f"jd_raw_{idx}"):
                        st.session_state[f"show_jd_raw_{idx}"] = not st.session_state.get(f"show_jd_raw_{idx}", False)

                # Show content based on button clicks
                if st.session_state.get(f"show_jd_raw_{idx}", False):
                    with st.expander("📄 Full Job Description Content", expanded=True):
                        st.text_area("Content", raw_text, height=400, disabled=True, key=f"jd_content_{idx}")

                        # Show chunks
                        if chunks:
                            st.markdown("---")
                            st.markdown("**🧩 Chunks:**")
                            for i, chunk in enumerate(chunks, 1):
                                with st.expander(f"Chunk {i} - {chunk['metadata'].get('field', 'Unknown')}"):
                                    st.write(chunk['content'])

                with col3:
                    if st.button(f"🗑️ Delete", key=f"delete_jd_{idx}", type="secondary"):
                        st.session_state[f"confirm_delete_jd_{idx}"] = not st.session_state.get(f"confirm_delete_jd_{idx}", False)

                if st.session_state.get(f"confirm_delete_jd_{idx}", False):
                    st.warning(f"⚠️ Are you sure you want to delete {jd_id}?")
                    col_confirm1, col_confirm2 = st.columns([1, 1])
                    with col_confirm1:
                        if st.button("✅ Yes, Delete", key=f"confirm_yes_jd_{idx}", type="primary"):
                            try:
                                st.session_state.db.delete_document(jd_id)
                                st.success(f"✅ JD {jd_id} deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                    with col_confirm2:
                        if st.button("❌ Cancel", key=f"confirm_no_jd_{idx}"):
                            st.session_state[f"confirm_delete_jd_{idx}"] = False
                            st.rerun()

                st.markdown("---")

def main():
    app = ResumeManagerApp()
    app.run()

if __name__ == "__main__":
    main()