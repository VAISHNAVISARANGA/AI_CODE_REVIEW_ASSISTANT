"""
Code Analysis Module
Handles linting and complexity analysis for various programming languages
"""

import json
import subprocess
import tempfile
import os
import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import sys

@dataclass
class pyAnalysisResult:
    """Structure for analysis results"""
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    complexity: float
    maintainability_index: float
    total_issues: int
    language: str

class CodeAnalyzer:
    """Main code analyzer class"""
    
    def __init__(self):
        self.temp_files = []
    
    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except OSError as e:
                print(f"Warning: Failed to delete temporary file {temp_file}: {e}", file=sys.stderr)
        self.temp_files = []
    
    def create_temp_file(self, code: str, extension: str = ".py") -> str:
        """Create temporary file with code content"""
        with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        self.temp_files.append(temp_path)
        return temp_path
    
    def _create_error_result(self, error_message: str, error_type: str = "error") -> Dict[str, Any]:
        """Create standardized error result dictionary"""
        return {
            'issues': [],
            'score': 5.0,
            'error': error_message,
            'error_type': error_type
        }
    
    def run_pylint(self, file_path: str) -> Dict[str, Any]:
        """Run pylint analysis and return structured results"""
        try:
            # Run pylint with JSON output
            result = subprocess.run([
                sys.executable, '-m', 'pylint',
                '--output-format=json',
                '--score=yes',
                '--disable=missing-module-docstring,missing-function-docstring,missing-class-docstring',
                file_path
            ], capture_output=True, text=True, timeout=30)
            
            # Parse JSON output
            if result.stdout.strip():
                try:
                    pylint_output = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Fallback parsing if JSON is malformed
                    pylint_output = self._parse_pylint_text(result.stdout)
            else:
                pylint_output = []
            
            # Extract score from stderr (pylint prints score there)
            score = self._extract_pylint_score(result.stderr)
            
            return {
                'issues': pylint_output if isinstance(pylint_output, list) else [],
                'score': score,
                'raw_output': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return self._create_error_result('Analysis timeout', 'timeout')
        except FileNotFoundError:
            return self._create_error_result('Pylint not installed', 'environment')
        except Exception as e:
            return self._create_error_result(str(e), 'runtime')
    def _parse_pylint_text(self, output: str) -> List[Dict]:
        """Fallback parser for pylint text output"""
        issues = []
        lines = output.split('\n')
        
        for line in lines:
            if ':' in line and any(severity in line for severity in ['error', 'warning', 'convention', 'refactor']):
                try:
                    # Parse format: filename:line:column: severity: message
                    parts = line.split(':', 4)
                    if len(parts) >= 4:
                        issues.append({
                            'line': int(parts[1]) if parts[1].isdigit() else 1,
                            'column': int(parts[2]) if parts[2].isdigit() else 0,
                            'type': parts[3].strip(),
                            'message': parts[4].strip() if len(parts) > 4 else 'Unknown issue',
                            'symbol': 'unknown'
                        })
                except (ValueError, IndexError):
                    continue
        
        return issues
    
    def _extract_pylint_score(self, stderr: str) -> float:
        """Extract pylint score from stderr output"""
        try:
            # Look for score pattern in stderr
            score_match = re.search(r'Your code has been rated at ([\d.]+)/10', stderr)
            if score_match:
                return float(score_match.group(1))
        except(AttributeError, ValueError,IndexError) as e:
            print(f"Warning: Failed to extract pylint score: {e}", file=sys.stderr)
            pass
        return 5.0  # Default score
    
    def run_radon_complexity(self, file_path: str) -> Dict[str, Any]:
        """Run radon complexity analysis"""
        try:
            # Run radon for cyclomatic complexity
            cc_result = subprocess.run([
                sys.executable, '-m', 'radon', 'cc', file_path, '--json'
            ], capture_output=True, text=True, timeout=15)
            
            # Run radon for maintainability index
            mi_result = subprocess.run([
                sys.executable, '-m', 'radon', 'mi', file_path, '--json'
            ], capture_output=True, text=True, timeout=15)
            
            # Parse complexity results
            cc_data = {}
            mi_data = {}
            
            if cc_result.stdout.strip():
                try:
                    cc_data = json.loads(cc_result.stdout)
                except json.JSONDecodeError:
                    pass
            
            if mi_result.stdout.strip():
                try:
                    mi_data = json.loads(mi_result.stdout)
                except json.JSONDecodeError:
                    pass
            
            # Calculate average complexity
            avg_complexity = self._calculate_average_complexity(cc_data)
            maintainability = self._extract_maintainability_index(mi_data, file_path)
            
            return {
                'complexity': avg_complexity,
                'maintainability_index': maintainability,
                'complexity_details': cc_data,
                'maintainability_details': mi_data
            }
            
        except subprocess.TimeoutExpired:
            return self._create_error_result('Complexity analysis timeout', 'timeout')
        except FileNotFoundError:
            return self._create_error_result('Radon not installed', 'environment')
        except Exception as e:
            return self._create_error_result(str(e), 'runtime')
    def _calculate_average_complexity(self, cc_data: Dict) -> float:
        """Calculate average cyclomatic complexity"""
        if not cc_data:
            return 1.0
        
        total_complexity = 0
        function_count = 0
        
        for file_data in cc_data.values():
            if isinstance(file_data, list):
                for item in file_data:
                    if isinstance(item, dict) and 'complexity' in item:
                        total_complexity += item['complexity']
                        function_count += 1
            if function_count==0:
                return 1.0
        
        return total_complexity / function_count 
    def _extract_maintainability_index(self, mi_data: Dict, file_path: str) -> float:
        """Extract maintainability index from radon output"""
        if not mi_data:
            return 50.0
        
        # Get the maintainability index for our file
        filename = os.path.basename(file_path)
        
        for key, value in mi_data.items():
            if isinstance(value, dict) and 'mi' in value:
                return float(value['mi'])
            elif isinstance(value, (int, float)):
                return float(value)
        
        return 50.0
    
    def parse_analysis_results(self, pylint_result: Dict, radon_result: Dict, language: str) -> pyAnalysisResult:
        """Parse and structure analysis results"""
        errors = []
        warnings = []
        
        # Handle analysis errors
        if pylint_result.get('error'):
            errors.append({
                'type': 'tool_error',
                'message': f"Pylint error: {pylint_result['error']}",
                'severity': 'high'
            })
            
        if radon_result.get('error'):
            errors.append({
                'type': 'tool_error',
                'message': f"Complexity analysis error: {radon_result['error']}",
                'severity': 'medium'
            })
        # Process pylint issues
        for issue in pylint_result.get('issues', []):
            issue_type = issue.get('type', '').lower()
            
            issue_data = {
                'line': issue.get('line', 1),
                'column': issue.get('column', 0),
                'message': issue.get('message', 'Unknown issue'),
                'symbol': issue.get('symbol', 'unknown'),
                'severity': issue_type
            }
            
            if issue_type in ['error', 'fatal']:
                errors.append(issue_data)
            else:
                warnings.append(issue_data)
        
        # Calculate metrics
        complexity = radon_result.get('complexity', 1.0)
        maintainability = radon_result.get('maintainability_index', 50.0)
        total_issues = len(errors) + len(warnings)
        
        return pyAnalysisResult(
            errors=errors,
            warnings=warnings,
            complexity=complexity,
            maintainability_index=maintainability,
            total_issues=total_issues,
            language=language
        )
    
    def analyze_python_code(self, code: str) -> pyAnalysisResult:
        """Complete analysis for Python code"""
        # Create temporary file
        temp_file = self.create_temp_file(code, '.py')
        
        try:
            # Run analyses
            pylint_result = self.run_pylint(temp_file)
            radon_result = self.run_radon_complexity(temp_file)
            
            # Parse results
            return self.parse_analysis_results(pylint_result, radon_result, 'Python')
            
        finally:
            self.cleanup()
    
    def analyze_code(self, code: str, language: str) -> pyAnalysisResult:
        """Main entry point for code analysis"""
        if language.lower() == 'python':
            return self.analyze_python_code(code)
        '''else:
            # For non-Python languages, return basic analysis
            return self._basic_analysis(code, language)
    
    def _basic_analysis(self, code: str, language: str) -> pyAnalysisResult:
        """Basic analysis for non-Python languages"""
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Simple heuristic analysis
        errors = []
        warnings = []
        
        # Basic syntax checks
        if language.lower() in ['java', 'c++', 'javascript']:
            # Check for missing semicolons (simple heuristic)
            for i, line in enumerate(non_empty_lines, 1):
                line = line.strip()
                if line and not line.endswith((';', '{', '}', '//', '/*', '*/')):
                    if any(keyword in line for keyword in ['if', 'for', 'while', 'else']):
                        continue  # Skip control structures
                    if line.startswith(('#', '//')):
                        continue  # Skip comments
                    warnings.append({
                        'line': i,
                        'column': 0,
                        'message': 'Possible missing semicolon',
                        'symbol': 'missing-semicolon',
                        'severity': 'convention'
                    })
        
        # Calculate basic complexity (lines of code / 10)
        complexity = max(1.0, len(non_empty_lines) / 10)
        maintainability = max(0, min(100, 100 - len(non_empty_lines) / 5))
        
        return pyAnalysisResult(
            errors=errors,
            warnings=warnings,
            complexity=complexity,
            maintainability_index=maintainability,
            total_issues=len(errors) + len(warnings),
            language=language
        )'''

# Convenience function for easy usage
def analyze_code_py(code: str, language: str = 'python') -> pyAnalysisResult:
    """Analyze code and return structured results"""
    analyzer = CodeAnalyzer()
    try:
        return analyzer.analyze_code(code, language)
    finally:
        analyzer.cleanup()

# Example usage and testing
'''if __name__ == "__main__":
    # Test code
    test_python_code = """
def calculate_sum(a, b):
    result = a + b
    return result

def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
            else:
                return x + y
        else:
            return x
    else:
        return 0

unused_variable = 42
print(calculate_sum(5, 3))
"""
    
    result = analyze_code_py(test_python_code, 'Python')
    print(f"Analysis Results:")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")
    print(f"Complexity: {result.complexity:.2f}")
    print(f"Maintainability Index: {result.maintainability_index:.2f}")'''