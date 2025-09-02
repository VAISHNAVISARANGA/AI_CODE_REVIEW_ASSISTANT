import streamlit as st
import time
import os
import pandas as pd
from analyzer_py import analyze_code_py,pyAnalysisResult
from analyzer_js import analyze_javascript_code, JSAnalysisResult
from ai_reviewer import review_code_with_ai, get_ai_reviewer, AIReviewResult
from analyzer_cpp import analyze_cpp_code ,CppAnalysisResult
from analyzer_java import analyze_java_code ,JavaAnalysisResult
# Page configuration
st.set_page_config(
    page_title="Code Review Tool",
    page_icon="📝",
    layout="wide"
)

# Language detection mapping
LANGUAGE_EXTENSIONS = {
    '.py': 'Python',
    '.java': 'Java',
    '.cpp': 'C++',
    '.cc': 'C++',
    '.cxx': 'C++',
    '.c': 'C',
    '.js': 'JavaScript',
    '.jsx': 'JavaScript (React)',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript (React)',
    '.php': 'PHP',
    '.rb': 'Ruby',
    '.go': 'Go',
    '.rs': 'Rust',
    '.swift': 'Swift',
    '.kt': 'Kotlin'
}

def detect_language_from_extension(filename):
    """Detect programming language based on file extension"""
    if not filename:
        return "Unknown"
    
    _, ext = os.path.splitext(filename.lower())
    return LANGUAGE_EXTENSIONS.get(ext, "Unknown")

def detect_language_from_code(code):
    """Simple heuristic to detect language from code content"""
    if not code.strip():
        return "Unknown"
    
    # Simple detection patterns
    code_lower = code.lower()
    
    if 'def ' in code or 'import ' in code or 'print(' in code:
        return "Python"
    elif 'public class' in code or 'System.out.println' in code:
        return "Java"
    elif '#include' in code and ('int main' in code or 'cout' in code):
        return "C++"
    elif 'function' in code or 'console.log' in code or 'var ' in code or 'let ' in code:
        return "JavaScript"
    else:
        return "Unknown"

def analyze_code(code: str, language: str):
    """Analyze code based on selected language"""
    if language.lower() == 'python':
        return analyze_code_py(code, language)
    elif language.lower() in ['javascript', 'js', 'javascript (react)', 'typescript', 'ts', 'typescript (react)']:
        return analyze_javascript_code(code, language)
    elif language.lower() == 'java':
        return analyze_java_code(code, language)
    elif language.lower() in ['c++', 'cpp']:
        return analyze_cpp_code(code, language)
    
    
    
def perform_real_code_analysis(code: str, language: str):
    """Perform real code analysis using appropriate analyzer"""
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Real analysis steps
    if language.lower() == 'python':
        steps = [
            "Initializing Pylint analyzer...",
            "Running Pylint analysis...",
            "Calculating complexity metrics with Radon...",
            "Processing results...",
            "Generating report..."
        ]
   
    elif language.lower() in ['javascript', 'js', 'javascript (react)', 'typescript', 'ts', 'typescript (react)']:
        steps = [
            "Initializing ESLint analyzer...",
            "Running ESLint analysis...",
            "Processing JavaScript/TypeScript rules...",
            "Calculating complexity metrics...",
            "Generating report..."
        ]

    elif language.lower() == 'java':
        steps = [
            "Initializing checkstyle analyzer...",
            "Running Java analysis...",
            "Processing Java rules...",
            "Calculating complexity metrics...",
            "Generating report..."
        ]
    elif language.lower() in ['c++', 'cpp']:
        steps = [
            "Initializing clang-tidy analyzer...",
            "Running C++ analysis...",
            "Processing C++ rules...",
            "Calculating complexity metrics...",
            "Generating report..."
        ]
    else:
        steps = [
            "Initializing analyzer...",
            "Running linting analysis...",
            "Calculating complexity metrics...",
            "Processing results...",
            "Generating report..."
        ]
    
    for i, step in enumerate(steps):
        status_text.text(step)
        progress_bar.progress((i + 1) / len(steps))
        
        if i == 1:  # During analysis step
            time.sleep(0.5)  # Give time for actual analysis
        else:
            time.sleep(0.2)
    
    # Perform actual analysis based on language
    try:
        
        result = analyze_code(code, language)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        return result
        
    except Exception as e:
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Return error result
        st.error(f"Analysis failed: {str(e)}")
        return None

def perform_ai_code_review(code: str, language: str) -> AIReviewResult:
    """Perform AI code review"""
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # AI analysis steps
    steps = [
        "🤖 Initializing AI reviewer...",
        "🧠 Analyzing code structure...",
        "🔍 Identifying potential issues...",
        "💡 Generating recommendations...",
        "📊 Finalizing review..."
    ]
    
    for i, step in enumerate(steps):
        status_text.text(step)
        progress_bar.progress((i + 1) / len(steps))
        time.sleep(0.3)  # Simulate processing time
    
    # Perform actual AI review
    try:
        result = review_code_with_ai(code, language)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        return result
        
    except Exception as e:
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Return error result
        st.error(f"AI review failed: {str(e)}")
        return AIReviewResult(
            bugs=[],
            improvements=[],
            best_practices=[],
            overall_assessment=f"AI review failed: {str(e)}",
            code_quality_score=5,
            error=str(e)
        )

def display_ai_review_results(ai_result: AIReviewResult):
    """Display AI review results in a clean format"""
    
    if ai_result is None or ai_result.error:
        if ai_result and "GEMINI_API_KEY" in str(ai_result.error):
            st.warning("🤖 AI Review unavailable - Please configure GEMINI_API_KEY in your .env file")
        else:
            st.error(f"⚠️ AI Review failed: {ai_result.error if ai_result else 'Unknown error'}")
        return
    
    # Success message
    st.success("🤖 AI code review completed!")
    
    # AI Score Display
    col1, col2 = st.columns(2)
    
    with col1:
        score_color = "normal"
        if ai_result.code_quality_score >= 8:
            score_color = "normal"
        elif ai_result.code_quality_score >= 6:
            score_color = "normal"
        else:
            score_color = "inverse"
            
        st.metric("AI Quality Score", f"{ai_result.code_quality_score}/10", help="AI assessment of code quality", delta_color=score_color)
    
    with col2:
        total_issues = len(ai_result.bugs) + len(ai_result.improvements) + len(ai_result.best_practices)
        st.metric("Total Suggestions", total_issues)
    
    # Overall Assessment
    st.subheader("🎯 AI Assessment")
    st.info(ai_result.overall_assessment)
    
    # Create tabs for different types of feedback
    if ai_result.bugs or ai_result.improvements or ai_result.best_practices:
        tab1, tab2, tab3 = st.tabs([
            f"🐛 Bugs & Issues ({len(ai_result.bugs)})",
            f"⚡ Improvements ({len(ai_result.improvements)})", 
            f"✅ Best Practices ({len(ai_result.best_practices)})"
        ])
        
        with tab1:
            st.subheader("🐛 Potential Bugs & Critical Issues")
            if ai_result.bugs:
                for i, bug in enumerate(ai_result.bugs, 1):
                    with st.container():
                        st.error(f"**Issue #{i}:** {bug}")
            else:
                st.success("🎉 No critical bugs or issues identified!")
        
        with tab2:
            st.subheader("⚡ Suggested Improvements")
            if ai_result.improvements:
                for i, improvement in enumerate(ai_result.improvements, 1):
                    with st.container():
                        st.warning(f"**Improvement #{i}:** {improvement}")
            else:
                st.success("✨ Code looks well-optimized!")
        
        with tab3:
            st.subheader("✅ Best Practices & Standards")
            if ai_result.best_practices:
                for i, practice in enumerate(ai_result.best_practices, 1):
                    with st.container():
                        st.info(f"**Best Practice #{i}:** {practice}")
            else:
                st.success("👍 Code follows good practices!")
    
    # AI Quality Gauge
    st.subheader("📊 AI Quality Assessment")
    
    # Create a visual quality gauge
    quality_score = ai_result.code_quality_score / 10.0
    st.progress(quality_score)
    
    if ai_result.code_quality_score >= 9:
        st.success("🏆 **Excellent Code!** Production-ready with minimal issues")
    elif ai_result.code_quality_score >= 8:
        st.success("🥇 **Great Code!** High quality with minor improvements possible")
    elif ai_result.code_quality_score >= 7:
        st.warning("🥈 **Good Code!** Solid foundation with some room for improvement")
    elif ai_result.code_quality_score >= 6:
        st.warning("🥉 **Fair Code!** Functional but needs attention")
    elif ai_result.code_quality_score >= 5:
        st.error("⚠️ **Needs Work!** Several issues need addressing")
    else:
        st.error("🚨 **Major Issues!** Significant refactoring required")

def display_analysis_results(result):
    """Display analysis results in a clean format - supports both AnalysisResult and JSAnalysisResult"""
    
    if result is None:
        st.error("⚠️ Code analysis failed")
        return
    
    # Success message with analyzer type
    if isinstance(result, pyAnalysisResult):
        st.success("✅ Python code analyzed with Pylint & Radon!")
    elif isinstance(result, JSAnalysisResult):
        st.success("✅ JavaScript/TypeScript code analyzed with ESLint!")
    elif isinstance(result, JavaAnalysisResult):
        st.success("✅ Java code analyzed with Checkstyle!")
    elif isinstance(result, CppAnalysisResult):
        st.success("✅ C++ code analyzed with Clang-Tidy!")
    else:
        st.success("✅ Code analyzed successfully!")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Language", result.language)
    
    with col2:
        st.metric("Total Issues", result.total_issues)
    
    with col3:
        complexity_color = "normal"
        if result.complexity > 10:
            complexity_color = "inverse"
        st.metric("Complexity", f"{result.complexity:.1f}", help="Lower is better", delta_color=complexity_color)
    
    with col4:
        maintainability_color = "normal" if result.maintainability_index > 50 else "inverse"
        st.metric("Maintainability", f"{result.maintainability_index:.1f}/100", help="Higher is better", delta_color=maintainability_color)
    
    
    # Progress bars for visual representation
    st.subheader("📊 Code Quality Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🧩Complexity Score**")
        # Invert complexity for progress bar (lower is better)
        complexity_normalized = max(0, min(1, (20 - result.complexity) / 20))
        st.progress(complexity_normalized)
        
        if result.complexity <= 5:
            st.success("🟢 Low complexity - code is clean, simple, easy to follow")
        elif result.complexity <= 10:
            st.warning("🟡 Moderate complexity - Consider refactoring")
        else:
            st.error("🔴 High complexity - Needs refactoring")
    
    with col2:
        st.write("**🛠️Maintainability Index**")
        st.progress(result.maintainability_index / 100)
        
        if result.maintainability_index >= 70:
            st.success("🟢 Highly maintainable - Code is stable, easy to enhance, and low-cost to maintain.")
        elif result.maintainability_index >= 50:
            st.warning("🟡 Moderately maintainable- Code works but may require extra effort to update or debug.")
        else:
            st.error("🔴 Difficultly maintainable – Code is fragile, costly to update, and risky for long-term use.")
    
    # Issues Tables
    if result.errors or result.warnings:
        st.subheader("🛠️ Issues Found")
        
        # Create tabs for errors and warnings
        tab1, tab2 = st.tabs([f"⚠️ Errors ({len(result.errors)})", f"⚠️ Warnings ({len(result.warnings)})"])
        
        with tab1:
            if result.errors:
                # Convert errors to DataFrame with proper column handling
                error_df = pd.DataFrame(result.errors)
                display_columns = []
                
                # Dynamically create column mapping based on what's available
                column_mapping = {
                    'line': 'Line',
                    'column': 'Col',
                    'message': 'Message',
                    'rule_id': 'Code',
                    'severity': 'Severity'
                }
                
                # Rename existing columns
                for old_col, new_col in column_mapping.items():
                    if old_col in error_df.columns:
                        error_df = error_df.rename(columns={old_col: new_col})
                        display_columns.append(new_col)
                
                # Display available columns
                st.dataframe(
                    error_df[display_columns],
                    use_container_width=True,
                    hide_index=True
                )
                # Show ESLint-specific information
                if isinstance(result, JSAnalysisResult):
                    st.info("💡 **ESLint Rules:** Errors are critical issues that may break functionality")
                    
            else:
                st.success("No errors found! 🎉")
        
        with tab2:
            if result.warnings:
                # Convert warnings to DataFrame with proper column handling
                warning_df = pd.DataFrame(result.warnings)
                display_columns = []
                
                # Dynamically create column mapping based on what's available
                column_mapping = {
                    'line': 'Line',
                    'column': 'Col',
                    'message': 'Message',
                    'rule_id': 'Code',
                    'severity': 'Severity',
                    'symbol': 'Rule'
                }
                
                # Rename existing columns
                for old_col, new_col in column_mapping.items():
                    if old_col in warning_df.columns:
                        warning_df = warning_df.rename(columns={old_col: new_col})
                        display_columns.append(new_col)
                
                # Display available columns
                st.dataframe(
                    warning_df[display_columns],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success("No warnings found! 🎉")
    else:
        st.success("🎉 No issues found! Your code looks great!")
    
    # Summary and Recommendations
    with st.expander("📋 Analysis Summary & Recommendations"):
        st.markdown("### Summary")
        
        if result.total_issues == 0:
            st.markdown("✅ **Excellent!** No issues detected in your code.")
        elif result.total_issues <= 5:
            st.markdown("✅ **Good!** Minor issues detected. Easy fixes.")
        elif result.total_issues <= 15:
            st.markdown("⚠️ **Fair.** Several issues need attention.")
        else:
            st.markdown("❌ **Needs Work.** Many issues require fixing.")
        
        st.markdown("### Recommendations")
        
        recommendations = []
        
        if result.complexity > 10:
            recommendations.append("🔥 **Refactor complex functions** - Break down large functions into smaller, focused ones")
        
        if result.maintainability_index < 50:
            recommendations.append("📚 **Improve documentation** - Add comments and docstrings")
        
        if len(result.errors) > 0:
            recommendations.append("🚨 **Fix critical errors first** - Address all error-level issues before warnings")
        
        if len(result.warnings) > 10:
            recommendations.append("🧹 **Clean up warnings** - Address style and convention issues")
        
        if result.language == 'Python' and result.total_issues == 0:
            recommendations.append("🚀 **Consider advanced practices** - Look into type hints, async/await, or design patterns")
        
        if not recommendations:
            recommendations.append("🎯 **Keep it up!** - Your code follows good practices")
        
        for rec in recommendations:
            st.markdown(f"• {rec}")
        
        # Code quality grade
        st.markdown("### Overall Grade")
        
        # Calculate grade based on multiple factors
        grade_score = 100
        grade_score -= min(50, result.total_issues * 3)  # Deduct for issues
        grade_score -= min(30, max(0, (result.complexity - 5) * 3))  # Deduct for high complexity
        grade_score += min(20, (result.maintainability_index - 50) / 2.5)  # Bonus for maintainability
        
        grade_score = max(0, min(100, grade_score))
        
        if grade_score >= 90:
            st.success(f"🏆 **A+ ({grade_score:.0f}/100)** - Exceptional code quality!")
        elif grade_score >= 80:
            st.success(f"🥇 **A ({grade_score:.0f}/100)** - Great code quality!")
        elif grade_score >= 70:
            st.warning(f"🥈 **B ({grade_score:.0f}/100)** - Good code quality with room for improvement")
        elif grade_score >= 60:
            st.warning(f"🥉 **C ({grade_score:.0f}/100)** - Average code quality, needs attention")
        else:
            st.error(f"📚 **D ({grade_score:.0f}/100)** - Code needs significant improvement")

# Main app
def main():
    st.title("📝 Code Review Tool")
    st.markdown("Upload a file or paste your code for automated review and AI analysis")
    
    # Create two columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Code input section
        st.subheader("📝 Code Input")
        
        # Tab selection for input method
        tab1, tab2 = st.tabs(["📋 Paste Code", "📁 Upload File"])
        
        code_content = ""
        detected_language = "Unknown"
        
        with tab1:
            # Text area for pasting code
            code_content = st.text_area(
                "Paste your code here:",
                height=300,
                placeholder="Paste your Python, Java, C++, or JavaScript code here..."
            )
            
            if code_content:
                detected_language = detect_language_from_code(code_content)
        
        with tab2:
            # File uploader
            uploaded_file = st.file_uploader(
                "Choose a code file",
                type=['py', 'java', 'cpp', 'cc', 'cxx', 'c', 'js', 'jsx', 'ts', 'tsx'],
                help="Supported formats: .py, .java, .cpp, .js, and more"
            )
            
            if uploaded_file is not None:
                # Read file content
                try:
                    code_content = str(uploaded_file.read(), "utf-8")
                    detected_language = detect_language_from_extension(uploaded_file.name)
                    
                    st.success(f"✅ File '{uploaded_file.name}' loaded successfully!")
                    st.info(f"🔍 Detected language: **{detected_language}**")
                    
                    # Show file preview
                    with st.expander("📖 File Preview"):
                        st.code(code_content[:500] + "..." if len(code_content) > 500 else code_content)
                        
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
    
    with col2:
        # Sidebar information
        st.subheader("ℹ️ Information")
        
        if detected_language != "Unknown":
            st.info(f"**Language:** {detected_language}")
        
        if code_content:
            lines = len([line for line in code_content.split('\n') if line.strip()])
            chars = len(code_content)
            st.metric("Lines of Code", lines)
            st.metric("Characters", chars)
        
        # AI Status Check
        ai_reviewer = get_ai_reviewer()
        if ai_reviewer.is_available():
            st.success("🤖 AI Review: Available")
        else:
            st.warning("🤖 AI Review: Configure GEMINI_API_KEY")
        
        st.markdown("---")
        st.markdown("**Supported Languages:**")
        st.markdown("• Python (.py)")
        st.markdown("• Java (.java)")
        st.markdown("• C++ (.cpp, .cc, .cxx)")
        st.markdown("• C (.c)")
        st.markdown("• JavaScript (.js, .jsx)")
        st.markdown("• TypeScript (.ts, .tsx)")
    
    # Review buttons and results
    st.markdown("---")
    
    # Create review button columns
    col1, col2 = st.columns(2)
    
    with col1:
        review_clicked = st.button("🔍 Static Analysis", type="primary", disabled=not bool(code_content), use_container_width=True)
    
    with col2:
        ai_review_clicked = st.button("🤖 AI Review", type="secondary", disabled=not bool(code_content), use_container_width=True)
    
    # Perform analysis based on button clicks
    if review_clicked or ai_review_clicked:
        if not code_content:
            st.warning("⚠️ Please provide code content to review")
            return
        
        # Create tabs for results
        if review_clicked and ai_review_clicked:
            tab1, tab2 = st.tabs(["🔍 Static Analysis Results", "🤖 AI Review Results"])
        elif review_clicked:
            tab1 = st.container()
            tab2 = None
        else:  # ai_review_clicked
            tab1 = None  
            tab2 = st.container()
        
        # Static Analysis
        if review_clicked and tab1:
            with tab1:
                st.subheader("📊 Static Analysis Results")
                result = perform_real_code_analysis(code_content, detected_language)
                if result:
                    display_analysis_results(result)
        
        # AI Review
        if ai_review_clicked and tab2:
            with tab2:
                st.subheader("🤖 AI Review Results")
                ai_result = perform_ai_code_review(code_content, detected_language)
                display_ai_review_results(ai_result)
        
        # Combined analysis if both buttons clicked
        if review_clicked and ai_review_clicked:
            st.markdown("---")
            st.subheader("🎯 Combined Summary")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info("📊 **Static Analysis:** Focuses on syntax, complexity, and style issues")
            with col2:
                st.info("🤖 **AI Review:** Provides contextual insights and architectural suggestions")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Code Review Tool - Powered by Pylint, Radon & Google Gemini 🚀<br>"
        "<small>Install: pip install pylint radon google-generativeai python-dotenv</small>"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()