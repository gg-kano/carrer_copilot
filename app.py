import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import json
from typing import List, Dict

# Import your existing modules
from database.chroma_db import ChromaDBStorage
from process.resume_process import ResumePreprocessor
from process.jd_process import JDPreprocessor

class ResumeManagerApp:
    def __init__(self):
        if 'db' not in st.session_state:
            st.session_state.db = ChromaDBStorage(persist_directory="./chroma_db")
        if 'processor' not in st.session_state:
            st.session_state.processor = ResumePreprocessor()
        if 'jd_processor' not in st.session_state:
            st.session_state.jd_processor = JDPreprocessor()
    
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
        page = st.sidebar.selectbox(
            "Choose a page",
            ["Dashboard", "Upload Resume", "Upload Job Description", "Search & Filter", "View Details"]
        )
        
        if page == "Dashboard":
            self.show_dashboard()
        elif page == "Upload Resume":
            self.show_upload_page()
        elif page == "Upload Job Description":
            self.show_upload_jd_page()
        elif page == "Search & Filter":
            self.show_search_page()
        elif page == "View Details":
            self.show_details_page()
    
    def show_dashboard(self):
        st.header("📊 Dashboard")
        
        # Get statistics
        all_resumes = st.session_state.db.list_all_documents("resume")
        all_jds = st.session_state.db.list_all_documents("job_description")
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📄 Total Resumes", len(all_resumes))
        
        with col2:
            st.metric("💼 Job Descriptions", len(all_jds))
        
        with col3:
            # Calculate total chunks for resumes and JDs
            total_chunks = 0
            for resume in all_resumes:
                chunks = st.session_state.db.get_chunks_by_document(resume['id'])
                total_chunks += len(chunks)
            for jd in all_jds:
                chunks = st.session_state.db.get_chunks_by_document(jd['id'])
                total_chunks += len(chunks)
            st.metric("🧩 Total Chunks", total_chunks)
        
        with col4:
            # Show last upload time
            if all_resumes:
                latest = max(all_resumes, key=lambda x: x['metadata'].get('created_at', ''))
                latest_date = latest['metadata'].get('created_at', 'Unknown')
                if latest_date != 'Unknown':
                    latest_date = latest_date.split()[0]  # Get just the date part
                st.metric("⏰ Last Upload", latest_date)
            else:
                st.metric("⏰ Last Upload", "None")
        
        st.markdown("---")
        
        # Recent uploads table
        st.subheader("📋 Recent Resumes")
        
        if all_resumes:
            # Convert to DataFrame for better display
            resume_data = []
            for resume in all_resumes[-10:]:  # Show last 10
                metadata = resume['metadata']
                resume_data.append({
                    'ID': resume['id'],
                    'Type': metadata.get('document_type', 'Unknown'),
                    'User ID': metadata.get('user_id', 'N/A'),
                    'Created At': metadata.get('created_at', 'Unknown'),
                    'Chunks': len(st.session_state.db.get_chunks_by_document(resume['id']))
                })
            
            df = pd.DataFrame(resume_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No resumes in database yet. Upload some resumes to get started!")

        # Recent job descriptions table
        st.markdown("---")
        st.subheader("💼 Recent Job Descriptions")

        if all_jds:
            # Convert to DataFrame for better display
            jd_data = []
            for jd in all_jds[-10:]:  # Show last 10
                metadata = jd['metadata']
                jd_data.append({
                    'ID': jd['id'],
                    'Type': metadata.get('document_type', 'Unknown'),
                    'User ID': metadata.get('user_id', 'N/A'),
                    'Created At': metadata.get('created_at', 'Unknown'),
                    'Chunks': len(st.session_state.db.get_chunks_by_document(jd['id']))
                })

            df = pd.DataFrame(jd_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No job descriptions in database yet. Upload some job descriptions to get started!")


    def show_upload_page(self):
        st.header("📤 Upload Resume")
        
        # Upload options
        upload_method = st.radio(
            "Choose upload method:",
            ["Text Input", "File Upload"]
        )
        
        resume_text = ""
        resume_id = ""
        
        if upload_method == "Text Input":
            st.subheader("✍️ Paste Resume Text")
            resume_text = st.text_area(
                "Resume Content",
                height=300,
                placeholder="Paste the resume text here..."
            )
            
            resume_id = st.text_input(
                "Resume ID (optional)",
                placeholder="Leave empty for auto-generation"
            )
            
        else:  # File Upload
            st.subheader("📁 Upload Resume File")
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['txt', 'md'],
                help="Currently supports .txt and .md files"
            )
            
            if uploaded_file:
                resume_text = str(uploaded_file.read(), "utf-8")
                resume_id = uploaded_file.name.split('.')[0]  # Use filename as ID
                
                st.success(f"File loaded: {uploaded_file.name}")
                
                # Show preview
                with st.expander("📖 Preview Content"):
                    st.text_area("Content Preview", resume_text[:500] + "...", height=100, disabled=True)
        
        # Additional metadata
        st.markdown("---")
        st.subheader("📝 Additional Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            user_id = st.text_input("User ID (optional)", placeholder="e.g., john_doe")
        
        with col2:
            if not resume_id:
                resume_id = st.text_input("Resume ID", value=f"resume_{uuid.uuid4().hex[:8]}", disabled=True)
            else:
                resume_id = st.text_input("Resume ID", value=resume_id, disabled=True)

        # Process and save
        if st.button("💾 Save Resume to Database", type="primary", use_container_width=True):
            if not resume_text.strip():
                st.error("❌ Please provide resume text!")
                return
            
            if not resume_id.strip():
                st.error("❌ Please provide a resume ID!")
                return
            
            try:
                with st.spinner("Processing and saving resume..."):
                    # Check if ID already exists
                    existing = st.session_state.db.get_document(resume_id)
                    if existing:
                        st.error(f"❌ Resume with ID '{resume_id}' already exists!")
                        return
                    
                    # Process the resume
                    chunks = st.session_state.processor.preprocess_resume(resume_text, resume_id)
                    
                    if not chunks:
                        st.error("❌ Failed to process resume. Please check the content.")
                        return
                    
                    # Store in database
                    st.session_state.db.store_document(
                        document_id=resume_id,
                        document_type="resume",
                        raw_text=resume_text,
                        user_id=user_id
                    )
                    
                    st.session_state.db.store_chunks(chunks)
                    
                    st.success(f"✅ Resume saved successfully!")
                    st.success(f"📊 Generated {len(chunks)} chunks")
                    
                    # Show success details
                    with st.expander("📋 Processing Details"):
                        st.write(f"**Resume ID:** {resume_id}")
                        st.write(f"**User ID:** {user_id or 'Not specified'}")
                        st.write(f"**Chunks Created:** {len(chunks)}")
                        st.write(f"**Content Length:** {len(resume_text)} characters")
                        
                        # Show chunk fields
                        fields = list(set([chunk['field'] for chunk in chunks]))
                        st.write(f"**Extracted Fields:** {', '.join(fields)}")
                    
            except Exception as e:
                st.error(f"❌ Error saving resume: {str(e)}")

    def show_upload_jd_page(self):
        st.header("💼 Upload Job Description")

        # Upload options
        upload_method = st.radio(
            "Choose upload method:",
            ["Text Input", "File Upload"]
        )

        jd_text = ""
        jd_id = ""

        if upload_method == "Text Input":
            st.subheader("✍️ Paste Job Description Text")
            jd_text = st.text_area(
                "Job Description Content",
                height=300,
                placeholder="Paste the job description text here..."
            )

            jd_id = st.text_input(
                "Job Description ID (optional)",
                placeholder="Leave empty for auto-generation"
            )

        else:  # File Upload
            st.subheader("📁 Upload Job Description File")
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['txt', 'md'],
                help="Currently supports .txt and .md files"
            )

            if uploaded_file:
                jd_text = str(uploaded_file.read(), "utf-8")
                jd_id = uploaded_file.name.split('.')[0]  # Use filename as ID

                st.success(f"File loaded: {uploaded_file.name}")

                # Show preview
                with st.expander("📖 Preview Content"):
                    st.text_area("Content Preview", jd_text[:500] + "...", height=100, disabled=True)

        # Additional metadata
        st.markdown("---")
        st.subheader("📝 Additional Information")

        col1, col2 = st.columns(2)

        with col1:
            user_id = st.text_input("User ID (optional)", placeholder="e.g., hr_team")

        with col2:
            if not jd_id:
                jd_id = st.text_input("Job Description ID", value=f"jd_{uuid.uuid4().hex[:8]}", disabled=True)
            else:
                jd_id = st.text_input("Job Description ID", value=jd_id, disabled=True)

        # Process and save
        if st.button("💾 Save Job Description to Database", type="primary", use_container_width=True):
            if not jd_text.strip():
                st.error("❌ Please provide job description text!")
                return

            if not jd_id.strip():
                st.error("❌ Please provide a job description ID!")
                return

            try:
                with st.spinner("Processing and saving job description..."):
                    # Check if ID already exists
                    existing = st.session_state.db.get_document(jd_id)
                    if existing:
                        st.error(f"❌ Job description with ID '{jd_id}' already exists!")
                        return

                    # Process the job description
                    chunks = st.session_state.jd_processor.preprocess_jd(jd_text, jd_id)

                    if not chunks:
                        st.error("❌ Failed to process job description. Please check the content.")
                        return

                    # Store in database
                    st.session_state.db.store_document(
                        document_id=jd_id,
                        document_type="job_description",
                        raw_text=jd_text,
                        user_id=user_id
                    )

                    st.session_state.db.store_chunks(chunks)

                    st.success(f"✅ Job description saved successfully!")
                    st.success(f"📊 Generated {len(chunks)} chunks")

                    # Show success details
                    with st.expander("📋 Processing Details"):
                        st.write(f"**Job Description ID:** {jd_id}")
                        st.write(f"**User ID:** {user_id or 'Not specified'}")
                        st.write(f"**Chunks Created:** {len(chunks)}")
                        st.write(f"**Content Length:** {len(jd_text)} characters")

                        # Show chunk fields
                        fields = list(set([chunk['field'] for chunk in chunks]))
                        st.write(f"**Extracted Fields:** {', '.join(fields)}")

            except Exception as e:
                st.error(f"❌ Error saving job description: {str(e)}")

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
        
        # Document selector
        all_docs = []
        for doc in all_resumes:
            all_docs.append(f"resume: {doc['id']}")
        for doc in all_jds:
            all_docs.append(f"job_description: {doc['id']}")
        
        selected_doc = st.selectbox("Select Document", all_docs)
        
        if selected_doc:
            doc_type, doc_id = selected_doc.split(": ", 1)
            
            # Get document details
            document = st.session_state.db.get_document(doc_id)
            chunks = st.session_state.db.get_chunks_by_document(doc_id)
            
            if document:
                # Document overview
                st.subheader(f"📄 Document: {doc_id}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Type", document['metadata'].get('document_type', 'Unknown'))
                
                with col2:
                    st.metric("Chunks", len(chunks))
                
                with col3:
                    st.metric("Content Length", f"{len(document['raw_text'])} chars")
                
                # Metadata
                with st.expander("📋 Metadata"):
                    st.json(document['metadata'])
                
                # Raw content
                with st.expander("📖 Raw Content"):
                    st.text_area("Full Content", document['raw_text'], height=200, disabled=True)
                
                # Chunks analysis
                st.subheader("🧩 Chunks Analysis")
                
                if chunks:
                    # Field distribution
                    field_counts = {}
                    for chunk in chunks:
                        field = chunk['metadata'].get('field', 'Unknown')
                        field_counts[field] = field_counts.get(field, 0) + 1
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Field Distribution:**")
                        for field, count in field_counts.items():
                            st.write(f"• {field}: {count} chunks")
                    
                    with col2:
                        st.write("**Content Lengths:**")
                        lengths = [len(chunk['content']) for chunk in chunks]
                        st.write(f"• Average: {sum(lengths)//len(lengths)} chars")
                        st.write(f"• Min: {min(lengths)} chars")
                        st.write(f"• Max: {max(lengths)} chars")
                    
                    # Individual chunks
                    st.subheader("📝 Individual Chunks")
                    
                    for i, chunk in enumerate(chunks, 1):
                        with st.expander(f"Chunk #{i} - {chunk['metadata'].get('field', 'Unknown')}"):
                            st.write(f"**ID:** {chunk['chunk_id']}")
                            st.write(f"**Field:** {chunk['metadata'].get('field', 'Unknown')}")
                            st.write(f"**Content:**")
                            st.write(chunk['content'])
                            st.write(f"**Metadata:**")
                            st.json(chunk['metadata'])
                
                # Delete option
                st.markdown("---")
                st.subheader("🗑️ Danger Zone")

                confirm_delete = st.checkbox(f"I confirm I want to delete {doc_id}")

                if st.button(f"❌ Delete {doc_id}", type="secondary", disabled=not confirm_delete):
                    try:
                        st.session_state.db.delete_document(doc_id)
                        st.success(f"✅ Document {doc_id} deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error deleting document: {str(e)}")

def main():
    app = ResumeManagerApp()
    app.run()

if __name__ == "__main__":
    main()