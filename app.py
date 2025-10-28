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
            ["Dashboard", "Upload Resume", "Upload Job Description", "Match Resumes", "Search & Filter", "View Details"]
        )
        
        if page == "Dashboard":
            self.show_dashboard()
        elif page == "Upload Resume":
            self.show_upload_page()
        elif page == "Upload Job Description":
            self.show_upload_jd_page()
        elif page == "Match Resumes":
            self.show_matching_page()
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

        # Matching Mode Selection
        st.subheader("1️⃣ Select Matching Mode")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### ⚡ Rough Mode")
            st.markdown("**Fast screening**")
            st.markdown("✓ Seconds to complete")
            st.markdown("✓ Vector similarity")
            st.markdown("✓ All resumes ranked")
            st.markdown("✓ Good for overview")

        with col2:
            st.markdown("### 🚀 Hybrid Mode")
            st.markdown("**Smart filtering**")
            st.markdown("✓ Best of both worlds")
            st.markdown("✓ Fast rough filter first")
            st.markdown("✓ Deep analysis on top N")
            st.markdown("✓ **Recommended**")

        with col3:
            st.markdown("### 🎯 Precise Mode")
            st.markdown("**Deep analysis**")
            st.markdown("✓ Detailed evaluation")
            st.markdown("✓ AI insights")
            st.markdown("✓ Strengths/weaknesses")
            st.markdown("✓ Slower, thorough")

        matching_mode = st.radio(
            "Choose matching mode:",
            ["⚡ Rough Mode (Fast)", "🚀 Hybrid Mode (Recommended)", "🎯 Precise Mode (Detailed)"],
            index=1,  # Default to Hybrid
            horizontal=True
        )

        is_rough_mode = matching_mode.startswith("⚡")
        is_hybrid_mode = matching_mode.startswith("🚀")
        is_precise_mode = matching_mode.startswith("🎯")

        # Job Description Selection
        st.markdown("---")
        st.subheader("2️⃣ Select Job Description")
        jd_options = [jd['id'] for jd in all_jds]
        selected_jd = st.selectbox("Choose a job description:", jd_options)

        # Configuration based on mode
        st.markdown("---")
        if is_rough_mode:
            st.subheader("3️⃣ Configure Search")
            top_k = st.slider(
                "Number of top chunks to retrieve:",
                min_value=10,
                max_value=200,
                value=50,
                step=10,
                help="More chunks = more comprehensive but may include less relevant matches"
            )
            selected_resumes = None
            precise_top_n = None
            st.info(f"ℹ️ Rough mode will automatically search across all {len(all_resumes)} resumes")

        elif is_hybrid_mode:
            st.subheader("3️⃣ Configure Hybrid Matching")

            col1, col2 = st.columns(2)

            with col1:
                rough_top_k = st.slider(
                    "Rough filter: Top chunks to search",
                    min_value=20,
                    max_value=200,
                    value=50,
                    step=10,
                    help="More chunks = more resumes in initial filter"
                )

            with col2:
                precise_top_n = st.slider(
                    "Precise analysis: Top N resumes",
                    min_value=3,
                    max_value=20,
                    value=10,
                    step=1,
                    help="Number of top rough matches to analyze in detail"
                )

            top_k = rough_top_k
            selected_resumes = None
            st.info(f"ℹ️ Will filter all {len(all_resumes)} resumes with rough matching, then analyze top {precise_top_n} with AI")

        else:  # Precise mode
            st.subheader("3️⃣ Select Resumes to Match")

            # Option to select all or specific resumes
            select_all = st.checkbox("Select all resumes", value=True)

            if select_all:
                selected_resumes = [resume['id'] for resume in all_resumes]
                st.info(f"✅ Selected {len(selected_resumes)} resumes")
            else:
                resume_options = [resume['id'] for resume in all_resumes]
                selected_resumes = st.multiselect(
                    "Choose resumes to match:",
                    resume_options,
                    default=[]
                )
            top_k = None
            precise_top_n = None

        # Match Button
        st.markdown("---")
        st.subheader("4️⃣ Run Matching")

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            match_button = st.button("🚀 Run Matching Analysis", type="primary", use_container_width=True)

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
            st.markdown("---")

            results = st.session_state.match_results
            display_mode = st.session_state.get('matching_mode', 'precise')

            # Display mode indicator
            if display_mode == 'rough':
                st.header("⚡ Rough Matching Results")
                st.info("💡 Results based on semantic similarity search. For detailed analysis, use Hybrid or Precise Mode.")
            elif display_mode == 'hybrid':
                st.header("🚀 Hybrid Matching Results")
                st.success("💡 Top candidates filtered by rough matching, then analyzed in detail by AI.")
                # Show breakdown
                precise_count = sum(1 for r in results if r.get('matching_mode') == 'hybrid')
                rough_only_count = sum(1 for r in results if r.get('matching_mode') == 'hybrid_rough_only')
                st.write(f"📊 **{precise_count}** resumes with AI analysis | **{rough_only_count}** filtered by rough matching only")
            else:
                st.header("🎯 Precise Matching Results")
                st.info("💡 Results based on AI-powered detailed analysis.")

            # Summary Statistics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                qualified_count = sum(1 for r in results if r.get('qualified', False))
                st.metric("✅ Qualified", qualified_count)

            with col2:
                avg_score = sum(r.get('match_score', 0) for r in results) / len(results)
                st.metric("📈 Avg Score", f"{avg_score:.1f}")

            with col3:
                strong_matches = sum(1 for r in results if r.get('recommendation') == 'STRONG_MATCH')
                st.metric("⭐ Strong Matches", strong_matches)

            with col4:
                st.metric("📄 Total Analyzed", len(results))

            st.markdown("---")

            # Individual Results
            for idx, result in enumerate(results, 1):
                resume_id = result.get('resume_id', 'Unknown')
                qualified = result.get('qualified', False)
                match_score = result.get('match_score', 0)
                recommendation = result.get('recommendation', 'N/A')
                summary = result.get('summary', 'No summary available')

                # Color coding based on qualification
                if qualified:
                    status_emoji = "✅"
                    status_color = "green"
                else:
                    status_emoji = "❌"
                    status_color = "red"

                # Recommendation badge
                rec_colors = {
                    'STRONG_MATCH': '🟢',
                    'GOOD_MATCH': '🟡',
                    'PARTIAL_MATCH': '🟠',
                    'NOT_MATCH': '🔴'
                }
                rec_emoji = rec_colors.get(recommendation, '⚪')

                with st.expander(
                    f"{status_emoji} #{idx} - {resume_id} | Score: {match_score}/100 {rec_emoji} {recommendation}",
                    expanded=(idx <= 3)  # Expand top 3 results by default
                ):
                    # Summary
                    st.markdown(f"**Summary:** {summary}")
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