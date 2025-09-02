import json
import subprocess
import tempfile
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class JSAnalysisResult:
    """Result of JavaScript code analysis"""
    language: str
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    total_issues: int
    complexity: float
    maintainability_index: float
    file_path: Optional[str] = None


class JavaScriptAnalyzer:
    """JavaScript code analyzer using ESLint"""
    
    def __init__(self):
        self.eslint_available = self._check_eslint_availability()
        
    def _check_eslint_availability(self) -> bool:
        """Check if ESLint is available in the system"""
        try:
            result = subprocess.run(['eslint', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def _create_eslint_config(self) -> str:
        """Create a basic ESLint configuration for analysis"""
        config = {
            "env": {
                "browser": True,
                "node": True,
                "es2021": True
            },
            "extends": [
                "eslint:recommended"
            ],
            "parserOptions": {
                "ecmaVersion": 12,
                "sourceType": "module"
            },
            "rules": {
                # Error level rules
                "no-unused-vars": "error",
                "no-undef": "error",
                "no-unreachable": "error",
                "no-dupe-args": "error",
                "no-dupe-keys": "error",
                "no-duplicate-case": "error",
                "no-empty": "error",
                "no-extra-semi": "error",
                "no-func-assign": "error",
                "no-inner-declarations": "error",
                "no-invalid-regexp": "error",
                "no-obj-calls": "error",
                "no-sparse-arrays": "error",
                "use-isnan": "error",
                "valid-typeof": "error",
                
                # Warning level rules
                "no-console": "warn",
                "no-debugger": "warn",
                "no-alert": "warn",
                "no-eval": "warn",
                "no-implied-eval": "warn",
                "no-with": "warn",
                "curly": "warn",
                "eqeqeq": "warn",
                "no-eq-null": "warn",
                "no-floating-decimal": "warn",
                "no-multi-spaces": "warn",
                "no-multi-str": "warn",
                "no-global-assign": "warn",
                "no-implicit-globals": "warn",
                "no-lone-blocks": "warn",
                "no-loop-func": "warn",
                "no-new": "warn",
                "no-new-func": "warn",
                "no-new-wrappers": "warn",
                "no-octal": "warn",
                "no-redeclare": "warn",
                "no-self-assign": "warn",
                "no-self-compare": "warn",
                "no-sequences": "warn",
                "no-throw-literal": "warn",
                "no-unused-expressions": "warn",
                "no-useless-call": "warn",
                "no-useless-concat": "warn",
                "vars-on-top": "warn",
                "wrap-iife": "warn",
                "yoda": "warn",
                
                # Style rules
                "indent": ["warn", 2],
                "quotes": ["warn", "single"],
                "semi": ["warn", "always"],
                "no-trailing-spaces": "warn",
                "no-multiple-empty-lines": ["warn", {"max": 2}],
                "comma-dangle": ["warn", "never"],
                "comma-spacing": "warn",
                "key-spacing": "warn",
                "space-before-blocks": "warn",
                "space-in-parens": "warn",
                "space-infix-ops": "warn",
                "space-unary-ops": "warn"
            }
        }
        return json.dumps(config, indent=2)
    
    def _run_eslint(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Run ESLint on the JavaScript file and return results"""
        if not self.eslint_available:
            return None
            
        try:
            # Create temporary config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as config_file:
                config_file.write(self._create_eslint_config())
                config_path = config_file.name
            
            try:
                # Run ESLint with JSON output
                cmd = [
                    'eslint', 
                    '--config', config_path,
                    '--format', 'json',
                    '--no-eslintrc',  # Don't use any existing config
                    file_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                # ESLint returns non-zero exit code when issues are found
                # This is expected, so we process the output regardless
                if result.stdout:
                    try:
                        return json.loads(result.stdout)
                    except json.JSONDecodeError:
                        return None
                        
                return []  # Empty result means no issues
                
            finally:
                # Clean up config file
                try:
                    os.unlink(config_path)
                except OSError:
                    pass
                    
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, Exception):
            return None
    
    def _calculate_complexity_score(self, issues: List[Dict[str, Any]]) -> float:
        """Calculate a complexity score based on ESLint issues"""
        if not issues:
            return 1.0
        
        complexity_indicators = {
            'no-unused-vars': 0.5,
            'complexity': 2.0,
            'max-depth': 1.5,
            'max-nested-callbacks': 1.5,
            'max-params': 1.0,
            'max-statements': 1.0,
            'cyclomatic-complexity': 2.0,
            'no-loop-func': 1.0,
            'no-inner-declarations': 0.5,
            'no-eval': 1.5,
            'no-implied-eval': 1.5,
            'no-with': 1.0
        }
        
        total_complexity = 1.0
        
        for issue in issues:
            rule_id = issue.get('ruleId', '')
            severity = issue.get('severity', 1)
            
            # Add complexity based on rule type
            weight = complexity_indicators.get(rule_id, 0.1)
            total_complexity += weight * severity
        
        return min(total_complexity, 20.0)  # Cap at 20
    
    def _calculate_maintainability_index(self, errors: List[Dict], warnings: List[Dict]) -> float:
        """Calculate maintainability index based on issues found"""
        base_score = 100.0
        
        # Deduct points for errors and warnings
        error_deduction = len(errors) * 5.0
        warning_deduction = len(warnings) * 2.0
        
        # Additional deductions for specific rule types
        critical_rules = [
            'no-eval', 'no-implied-eval', 'no-with', 'no-global-assign',
            'no-unreachable', 'no-unused-vars', 'no-undef'
        ]
        
        for error in errors:
            if error.get('ruleId') in critical_rules:
                error_deduction += 3.0
        
        final_score = base_score - error_deduction - warning_deduction
        return max(0.0, min(100.0, final_score))
    
    def _parse_eslint_output(self, eslint_result: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse ESLint JSON output into structured format"""
        all_errors = []
        all_warnings = []
        
        for file_result in eslint_result:
            messages = file_result.get('messages', [])
            
            for message in messages:
                issue = {
                    'line': message.get('line', 0),
                    'column': message.get('column', 0),
                    'message': message.get('message', 'Unknown issue'),
                    'severity': 'error' if message.get('severity', 1) == 2 else 'warning',
                    'symbol': message.get('ruleId', 'unknown-rule'),
                    'rule_id': message.get('ruleId', 'unknown-rule')
                }
                
                if message.get('severity', 1) == 2:  # Error
                    all_errors.append(issue)
                else:  # Warning
                    all_warnings.append(issue)
        
        return {
            'errors': all_errors,
            'warnings': all_warnings,
            'total_issues': len(all_errors) + len(all_warnings)
        }
    
    def analyze_code(self, code: str, language: str = "JavaScript") -> JSAnalysisResult:
        """Analyze JavaScript code using ESLint"""
        
        # Create temporary file with the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as temp_file:
            temp_file.write(code)
            temp_path = temp_file.name
        
        try:
            # Run ESLint analysis
            eslint_result = self._run_eslint(temp_path)
            
            if eslint_result is None:
                # ESLint not available or failed, return basic analysis
                return JSAnalysisResult(
                    language=language,
                    errors=[],
                    warnings=[{
                        'line': 1,
                        'column': 1,
                        'message': 'ESLint not available. Please install: npm install -g eslint',
                        'severity': 'warning',
                        'symbol': 'eslint-unavailable'
                    }],
                    total_issues=1,
                    complexity=5.0,
                    maintainability_index=50.0,
                    file_path=temp_path
                )
            
            # Parse ESLint results
            parsed_results = self._parse_eslint_output(eslint_result)
            
            # Calculate metrics
            complexity = self._calculate_complexity_score(
                parsed_results['errors'] + parsed_results['warnings']
            )
            
            maintainability = self._calculate_maintainability_index(
                parsed_results['errors'], 
                parsed_results['warnings']
            )
            
            return JSAnalysisResult(
                language=language,
                errors=parsed_results['errors'],
                warnings=parsed_results['warnings'],
                total_issues=parsed_results['total_issues'],
                complexity=complexity,
                maintainability_index=maintainability,
                file_path=temp_path
            )
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except OSError:
                pass


def analyze_javascript_code(code: str, language: str = "JavaScript") -> JSAnalysisResult:
    """Main function to analyze JavaScript code"""
    analyzer = JavaScriptAnalyzer()
    return analyzer.analyze_code(code, language)


# For backward compatibility with the main analyzers.py interface
def analyze_code(code: str, language: str) -> JSAnalysisResult:
    """Analyze code - JavaScript specific implementation"""
    if language.lower() in ['javascript', 'js', 'javascript (react)', 'typescript', 'ts']:
        return analyze_javascript_code(code, language)
    else:
        # Return a basic result for unsupported languages
        return JSAnalysisResult(
            language=language,
            errors=[],
            warnings=[{
                'line': 1,
                'column': 1,
                'message': f'Language {language} not supported by JavaScript analyzer',
                'severity': 'warning',
                'symbol': 'unsupported-language'
            }],
            total_issues=1,
            complexity=5.0,
            maintainability_index=50.0
        )


