"""
AI Code Reviewer Module
Uses Google Gemini API to provide intelligent code reviews
"""

import os
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class AIReviewResult:
    """Structure for AI review results"""
    bugs: List[str]
    improvements: List[str]
    best_practices: List[str]
    overall_assessment: str
    code_quality_score: int
    error: Optional[str] = None

class AICodeReviewer:
    """AI-powered code reviewer using Google Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
    
    def is_available(self) -> bool:
        """Check if AI reviewer is available (API key configured)"""
        return self.api_key is not None and self.model is not None
    
    def create_review_prompt(self, code: str, language: str) -> str:
        """Create a structured prompt for code review"""
        
        prompt = f"""You are a senior software engineer with 10+ years of experience. Please review the following {language} code thoroughly and professionally.

**CODE TO REVIEW:**
```{language.lower()}
{code}
```

**INSTRUCTIONS:**
Provide a comprehensive code review with specific, actionable feedback. Focus on real issues and practical improvements.

**OUTPUT FORMAT (use exactly this structure):**

## BUGS
[List specific bugs, logic errors, or potential runtime issues. If none found, write "No critical bugs detected."]

## IMPROVEMENTS
[List specific improvements for performance, readability, maintainability. Be specific about what to change and why.]

## BEST PRACTICES
[List violations of {language} best practices, coding standards, or conventions. Suggest specific alternatives.]

## OVERALL ASSESSMENT
[Provide a 2-3 sentence summary of the code quality and main areas for improvement.]

## CODE QUALITY SCORE
[Provide a score from 1-10, where 10 is production-ready enterprise code.]

**GUIDELINES:**
- Be specific and actionable in your feedback
- Focus on the most important issues first
- Provide code examples when helpful
- Consider security, performance, and maintainability
- If code is excellent, acknowledge it but still provide constructive suggestions
"""
        
        return prompt
    
    def parse_ai_response(self, response_text: str) -> AIReviewResult:
        """Parse the AI response into structured format"""
        
        try:
            # Initialize with empty lists
            bugs = []
            improvements = []
            best_practices = []
            overall_assessment = ""
            code_quality_score = 5
            
            # Split response into sections
            sections = re.split(r'##\s+(BUGS|IMPROVEMENTS|BEST PRACTICES|OVERALL ASSESSMENT|CODE QUALITY SCORE)', 
                              response_text, flags=re.IGNORECASE)
            
            current_section = None
            
            for i, section in enumerate(sections):
                section = section.strip()
                
                if section.upper() in ['BUGS', 'IMPROVEMENTS', 'BEST PRACTICES', 'OVERALL ASSESSMENT', 'CODE QUALITY SCORE']:
                    current_section = section.upper()
                elif current_section and section:
                    if current_section == 'BUGS':
                        bugs = self._parse_list_items(section)
                    elif current_section == 'IMPROVEMENTS':
                        improvements = self._parse_list_items(section)
                    elif current_section == 'BEST PRACTICES':
                        best_practices = self._parse_list_items(section)
                    elif current_section == 'OVERALL ASSESSMENT':
                        overall_assessment = section.strip()
                    elif current_section == 'CODE QUALITY SCORE':
                        # Extract numeric score
                        score_match = re.search(r'(\d+)', section)
                        if score_match:
                            code_quality_score = int(score_match.group(1))
            
            # Fallback parsing if structured format wasn't followed
            if not bugs and not improvements and not best_practices:
                return self._fallback_parse(response_text)
            
            return AIReviewResult(
                bugs=bugs,
                improvements=improvements,
                best_practices=best_practices,
                overall_assessment=overall_assessment or "Code review completed.",
                code_quality_score=max(1, min(10, code_quality_score))
            )
            
        except Exception as e:
            return AIReviewResult(
                bugs=[],
                improvements=[],
                best_practices=[],
                overall_assessment="Failed to parse AI response.",
                code_quality_score=5,
                error=f"Parsing error: {str(e)}"
            )
    
    def _parse_list_items(self, text: str) -> List[str]:
        """Parse text into list items"""
        if not text.strip():
            return []
        
        # Handle "No issues" type responses
        if any(phrase in text.lower() for phrase in ['no critical bugs', 'no bugs', 'no issues', 'none found']):
            return []
        
        # Split by bullet points, dashes, or line breaks
        items = []
        
        # First try to split by markdown list items
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('- ', '* ', '+ ', '1. ', '2. ', '3. ', '4. ', '5. ')):
                # Remove markdown formatting
                clean_line = re.sub(r'^[-*+\d.]\s*', '', line).strip()
                if clean_line:
                    items.append(clean_line)
            elif line and not items:  # If no markdown, treat each non-empty line as item
                items.append(line)
        
        # If no structured items found, split by sentences
        if not items and text.strip():
            sentences = re.split(r'[.!?]+', text)
            items = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        return items[:10]  # Limit to 10 items max
    
    def _fallback_parse(self, text: str) -> AIReviewResult:
        """Fallback parsing when structured format isn't followed"""
        
        # Try to extract any meaningful content
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        bugs = []
        improvements = []
        best_practices = []
        
        for para in paragraphs:
            para_lower = para.lower()
            if any(word in para_lower for word in ['bug', 'error', 'issue', 'problem', 'crash']):
                bugs.extend(para.split('. '))
            elif any(word in para_lower for word in ['improve', 'better', 'optimize', 'enhance']):
                improvements.extend(para.split('. '))
            elif any(word in para_lower for word in ['practice', 'convention', 'standard', 'should']):
                best_practices.extend(para.split('. '))
        
        return AIReviewResult(
            bugs=[b.strip() for b in bugs if b.strip()][:5],
            improvements=[i.strip() for i in improvements if i.strip()][:5],
            best_practices=[bp.strip() for bp in best_practices if bp.strip()][:5],
            overall_assessment=paragraphs[0] if paragraphs else "AI review completed.",
            code_quality_score=7
        )
    
    def review_code(self, code: str, language: str) -> AIReviewResult:
        """Main method to review code using AI"""
        
        if not self.is_available():
            return AIReviewResult(
                bugs=[],
                improvements=[],
                best_practices=[],
                overall_assessment="AI reviewer not available. Please set GEMINI_API_KEY in .env file.",
                code_quality_score=5,
                error="GEMINI_API_KEY not configured"
            )
        
        try:
            # Create prompt
            prompt = self.create_review_prompt(code, language)
            
            # Call Gemini API
            response = self.model.generate_content(prompt)
            
            if response.text:
                # Parse response
                return self.parse_ai_response(response.text)
            else:
                return AIReviewResult(
                    bugs=[],
                    improvements=[],
                    best_practices=[],
                    overall_assessment="AI reviewer did not return a response.",
                    code_quality_score=5,
                    error="Empty response from AI"
                )
                
        except Exception as e:
            return AIReviewResult(
                bugs=[],
                improvements=[],
                best_practices=[],
                overall_assessment=f"AI review failed: {str(e)}",
                code_quality_score=5,
                error=str(e)
            )

# Global reviewer instance
_ai_reviewer = None

def get_ai_reviewer() -> AICodeReviewer:
    """Get singleton AI reviewer instance"""
    global _ai_reviewer
    if _ai_reviewer is None:
        _ai_reviewer = AICodeReviewer()
    return _ai_reviewer

def review_code_with_ai(code: str, language: str = 'Python') -> AIReviewResult:
    """Convenience function to review code with AI"""
    reviewer = get_ai_reviewer()
    return reviewer.review_code(code, language)

# Example usage
if __name__ == "__main__":
    # Test the AI reviewer
    test_code = """
def calculate_sum(numbers):
    sum = 0
    for i in range(len(numbers)):
        sum += numbers[i]
    return sum

def divide(a, b):
    return a / b

x = [1, 2, 3, 4, 5]
result = calculate_sum(x)
print("Sum is:", result)

# Division without error checking
answer = divide(10, 0)
print(answer)
"""
    
    result = review_code_with_ai(test_code, "Python")
    
    print("AI Code Review Results:")
    print(f"Bugs: {len(result.bugs)}")
    print(f"Improvements: {len(result.improvements)}")
    print(f"Best Practices: {len(result.best_practices)}")
    print(f"Score: {result.code_quality_score}/10")
    print(f"Assessment: {result.overall_assessment}")
    
    if result.error:
        print(f"Error: {result.error}")