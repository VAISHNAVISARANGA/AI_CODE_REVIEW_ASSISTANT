import subprocess
import json
import yaml
import tempfile
import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class CppAnalysisResult:
    """Result of C++ code analysis"""
    language: str
    total_issues: int
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    complexity: float
    maintainability_index: float
    clang_tidy_available: bool = False
    analysis_details: Dict[str, Any] = None

class CppAnalyzer:
    """C++ code analyzer using clang-tidy"""
    
    def __init__(self):
        self.clang_tidy_available = self._check_clang_tidy_availability()
        self.temp_dir = tempfile.gettempdir()
    
    def _check_clang_tidy_availability(self) -> bool:
        """Check if clang-tidy is available on the system"""
        try:
            result = subprocess.run(
                ['clang-tidy', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def _estimate_complexity_from_code(self, code: str) -> float:
        """Estimate cyclomatic complexity from C++ code using pattern matching"""
        complexity = 1  # Base complexity
        
        # Count decision points that increase complexity
        patterns = [
            r'\bif\s*\(',           # if statements
            r'\belse\s+if\s*\(',    # else if statements
            r'\bwhile\s*\(',        # while loops
            r'\bfor\s*\(',          # for loops
            r'\bdo\s*\{',           # do-while loops
            r'\bswitch\s*\(',       # switch statements
            r'\bcase\s+',           # case statements
            r'\bcatch\s*\(',        # catch blocks
            r'\b\?\s*',             # ternary operators
            r'\|\|',                # logical OR
            r'&&',                  # logical AND
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, code, re.IGNORECASE)
            complexity += len(matches)
        
        return float(complexity)
    
    def _estimate_maintainability_index(self, code: str, complexity: float) -> float:
        """Estimate maintainability index for C++ code"""
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        total_lines = len(lines)
        
        if total_lines == 0:
            return 100.0
        
        # Count comments
        comment_lines = len([line for line in lines if line.startswith('//') or line.startswith('/*')])
        comment_ratio = comment_lines / total_lines if total_lines > 0 else 0
        
        # Count long lines (over 120 characters)
        long_lines = len([line for line in lines if len(line) > 120])
        long_line_ratio = long_lines / total_lines if total_lines > 0 else 0
        
        # Simple maintainability calculation
        # Start with 100 and deduct based on various factors
        maintainability = 100.0
        maintainability -= complexity * 2  # Deduct for complexity
        maintainability -= long_line_ratio * 20  # Deduct for long lines
        maintainability += comment_ratio * 10  # Bonus for comments
        
        # Ensure reasonable bounds
        return max(0.0, min(100.0, maintainability))
    
    def _create_temp_cpp_file(self, code: str) -> str:
        """Create a temporary C++ file for analysis"""
        temp_file = os.path.join(self.temp_dir, 'temp_code.cpp')
        
        # Add basic includes if not present to avoid compilation errors
        includes_needed = [
            '#include <iostream>',
            '#include <vector>',
            '#include <string>'
        ]
        
        has_includes = any('#include' in line for line in code.split('\n')[:10])
        
        if not has_includes:
            code = '\n'.join(includes_needed) + '\n\n' + code
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        return temp_file
    
    def _parse_clang_tidy_output(self, output: str, format_type: str = 'text') -> tuple:
        """Parse clang-tidy output and extract errors/warnings"""
        errors = []
        warnings = []
        
        if format_type == 'yaml':
            try:
                data = yaml.safe_load(output)
                if isinstance(data, dict) and 'Diagnostics' in data:
                    for diagnostic in data['Diagnostics']:
                        issue = {
                            'line': diagnostic.get('DiagnosticMessage', {}).get('FileOffset', 0),
                            'column': 0,
                            'message': diagnostic.get('DiagnosticMessage', {}).get('Message', 'Unknown issue'),
                            'severity': 'error' if 'error' in diagnostic.get('Level', '').lower() else 'warning',
                            'symbol': diagnostic.get('DiagnosticName', 'clang-tidy')
                        }
                        
                        if issue['severity'] == 'error':
                            errors.append(issue)
                        else:
                            warnings.append(issue)
                            
            except yaml.YAMLError:
                # Fallback to text parsing
                pass
        
        # Text format parsing (default and fallback)
        if not errors and not warnings:
            lines = output.split('\n')
            for line in lines:
                # Match clang-tidy output format: file:line:column: severity: message [check-name]
                match = re.match(r'^(.+?):(\d+):(\d+):\s*(warning|error|note):\s*(.+?)\s*\[([^\]]+)\]', line)
                if match:
                    file_path, line_num, col_num, severity, message, check_name = match.groups()
                    
                    issue = {
                        'line': int(line_num),
                        'column': int(col_num),
                        'message': message.strip(),
                        'severity': severity.lower(),
                        'symbol': check_name
                    }
                    
                    if severity.lower() in ['error']:
                        errors.append(issue)
                    elif severity.lower() in ['warning']:
                        warnings.append(issue)
        
        return errors, warnings
    
    def _run_clang_tidy_analysis(self, temp_file: str) -> tuple:
        """Run clang-tidy analysis on the temporary file"""
        errors = []
        warnings = []
        
        if not self.clang_tidy_available:
            # Return fallback analysis
            return errors, warnings
        
        try:
            # Common clang-tidy checks for general code quality
            checks = [
                'bugprone-*',
                'readability-*',
                'performance-*',
                'modernize-*',
                'cppcoreguidelines-*',
                'misc-*',
                '-readability-identifier-length',  # Can be too strict
                '-modernize-use-trailing-return-type',  # Style preference
            ]
            
            checks_str = ','.join(checks)
            
            # Run clang-tidy with text output first
            cmd = [
                'clang-tidy',
                temp_file,
                f'--checks={checks_str}',
                '--',
                '-std=c++17'  # Use C++17 standard
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse the output
            if result.stdout or result.stderr:
                output = result.stdout + result.stderr
                errors, warnings = self._parse_clang_tidy_output(output, 'text')
            
            # Try YAML format if available and no results from text
            if not errors and not warnings:
                try:
                    cmd_yaml = cmd + ['--format-style=yaml']
                    result_yaml = subprocess.run(
                        cmd_yaml,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result_yaml.stdout:
                        errors, warnings = self._parse_clang_tidy_output(result_yaml.stdout, 'yaml')
                        
                except subprocess.SubprocessError:
                    pass  # Fall back to text results
            
        except subprocess.TimeoutExpired:
            # Analysis took too long
            warnings.append({
                'line': 1,
                'column': 1,
                'message': 'Analysis timeout - code may be too complex',
                'severity': 'warning',
                'symbol': 'timeout'
            })
        except subprocess.SubprocessError as e:
            # clang-tidy execution failed
            errors.append({
                'line': 1,
                'column': 1,
                'message': f'Analysis failed: {str(e)}',
                'severity': 'error',
                'symbol': 'analysis-error'
            })
        
        return errors, warnings
    
    def _cleanup_temp_file(self, temp_file: str):
        """Clean up temporary file"""
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except OSError:
            pass  # Ignore cleanup errors
    
    def analyze(self, code: str, language: str = 'C++') -> CppAnalysisResult:
        """Analyze C++ code using clang-tidy"""
        
        if not code.strip():
            return CppAnalysisResult(
                language=language,
                total_issues=0,
                errors=[],
                warnings=[],
                complexity=1.0,
                maintainability_index=100.0,
                clang_tidy_available=self.clang_tidy_available
            )
        
        # Create temporary file
        temp_file = self._create_temp_cpp_file(code)
        
        try:
            # Run clang-tidy analysis
            errors, warnings = self._run_clang_tidy_analysis(temp_file)
            
            # Calculate metrics
            complexity = self._estimate_complexity_from_code(code)
            maintainability = self._estimate_maintainability_index(code, complexity)
            total_issues = len(errors) + len(warnings)
            
            # Create analysis details
            analysis_details = {
                'clang_tidy_used': self.clang_tidy_available,
                'temp_file_created': True,
                'lines_analyzed': len([line for line in code.split('\n') if line.strip()])
            }
            
            return CppAnalysisResult(
                language=language,
                total_issues=total_issues,
                errors=errors,
                warnings=warnings,
                complexity=complexity,
                maintainability_index=maintainability,
                clang_tidy_available=self.clang_tidy_available,
                analysis_details=analysis_details
            )
            
        finally:
            # Always cleanup temporary file
            self._cleanup_temp_file(temp_file)

def analyze_cpp_code(code: str, language: str = 'C++') -> CppAnalysisResult:
    """Main function to analyze C++ code"""
    analyzer = CppAnalyzer()
    return analyzer.analyze(code, language)

# Additional helper functions for integration

def get_cpp_analyzer_status() -> Dict[str, Any]:
    """Get status information about the C++ analyzer"""
    analyzer = CppAnalyzer()
    return {
        'clang_tidy_available': analyzer.clang_tidy_available,
        'supported_languages': ['C++', 'C'],
        'supported_extensions': ['.cpp', '.cc', '.cxx', '.c', '.h', '.hpp'],
        'analyzer_type': 'clang-tidy'
    }

def is_cpp_language(language: str) -> bool:
    """Check if the language is C/C++ related"""
    cpp_languages = ['c++', 'cpp', 'c', 'cc', 'cxx']
    return language.lower() in cpp_languages

