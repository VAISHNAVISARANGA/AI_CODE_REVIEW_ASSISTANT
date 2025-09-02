import subprocess
import tempfile
import os
import xml.etree.ElementTree as ET
import json
from typing import List, Dict, Any
from dataclasses import dataclass
import re

@dataclass
class JavaAnalysisResult:
    """Data class to hold analysis results"""
    language: str
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    total_issues: int
    complexity: float
    maintainability_index: float

class JavaAnalyzer:
    """Java code analyzer using Checkstyle"""
    
    def __init__(self):
        self.checkstyle_jar = None
        self.config_file = None
        self._setup_checkstyle()
    
    def _setup_checkstyle(self):
        """Setup Checkstyle configuration"""
        # Create a basic Checkstyle configuration
        checkstyle_config = """<?xml version="1.0"?>
<!DOCTYPE module PUBLIC
    "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN"
    "https://checkstyle.org/dtds/configuration_1_3.dtd">

<module name="Checker">
    <property name="charset" value="UTF-8"/>
    <property name="severity" value="warning"/>
    <property name="fileExtensions" value="java"/>
    
    <!-- Filters -->
    <module name="BeforeExecutionExclusionFileFilter">
        <property name="fileNamePattern" value="module\-info\.java$"/>
    </module>
    
    <!-- File-level checks -->
    <module name="FileTabCharacter">
        <property name="eachLine" value="true"/>
    </module>
    <module name="FileLength">
        <property name="max" value="2000"/>
    </module>
    <module name="LineLength">
        <property name="max" value="120"/>
        <property name="ignorePattern" value="^package.*|^import.*|a href|href|http://|https://|ftp://"/>
    </module>
    
    <module name="TreeWalker">
        <!-- Naming conventions -->
        <module name="ConstantName"/>
        <module name="LocalFinalVariableName"/>
        <module name="LocalVariableName"/>
        <module name="MemberName"/>
        <module name="MethodName"/>
        <module name="PackageName"/>
        <module name="ParameterName"/>
        <module name="StaticVariableName"/>
        <module name="TypeName"/>
        
        <!-- Imports -->
        <module name="AvoidStarImport"/>
        <module name="IllegalImport"/>
        <module name="RedundantImport"/>
        <module name="UnusedImports"/>
        
        <!-- Size Violations -->
        <module name="MethodLength">
            <property name="max" value="150"/>
        </module>
        <module name="ParameterNumber">
            <property name="max" value="7"/>
        </module>
        
        <!-- Whitespace -->
        <module name="EmptyForIteratorPad"/>
        <module name="GenericWhitespace"/>
        <module name="MethodParamPad"/>
        <module name="NoWhitespaceAfter"/>
        <module name="NoWhitespaceBefore"/>
        <module name="OperatorWrap"/>
        <module name="ParenPad"/>
        <module name="TypecastParenPad"/>
        <module name="WhitespaceAfter"/>
        <module name="WhitespaceAround"/>
        
        <!-- Modifier Checks -->
        <module name="ModifierOrder"/>
        <module name="RedundantModifier"/>
        
        <!-- Blocks -->
        <module name="AvoidNestedBlocks"/>
        <module name="EmptyBlock"/>
        <module name="LeftCurly"/>
        <module name="NeedBraces"/>
        <module name="RightCurly"/>
        
        <!-- Common coding problems -->
        <module name="EmptyStatement"/>
        <module name="EqualsHashCode"/>
        <module name="HiddenField"/>
        <module name="IllegalInstantiation"/>
        <module name="InnerAssignment"/>
        <module name="MissingSwitchDefault"/>
        <module name="SimplifyBooleanExpression"/>
        <module name="SimplifyBooleanReturn"/>
        
        <!-- Class design -->
        <module name="DesignForExtension"/>
        <module name="FinalClass"/>
        <module name="HideUtilityClassConstructor"/>
        <module name="InterfaceIsType"/>
        <module name="VisibilityModifier"/>
        
        <!-- Complexity -->
        <module name="CyclomaticComplexity">
            <property name="max" value="10"/>
        </module>
        <module name="JavaNCSS">
            <property name="methodMaximum" value="50"/>
            <property name="classMaximum" value="1500"/>
        </module>
        <module name="NPathComplexity">
            <property name="max" value="200"/>
        </module>
    </module>
</module>"""
        
        # Save config to temporary file
        self.config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False)
        self.config_file.write(checkstyle_config)
        self.config_file.close()
    
    def _check_checkstyle_availability(self) -> bool:
        """Check if Checkstyle is available in the system"""
        try:
            # Try to run checkstyle command
            result = subprocess.run(['checkstyle', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _run_checkstyle_analysis(self, java_file_path: str) -> str:
        """Run Checkstyle analysis on the Java file"""
        try:
            # Run Checkstyle with XML output
            cmd = [
                'checkstyle',
                '-c', self.config_file.name,
                '-f', 'xml',
                java_file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode in [0, 1]:  # 0 = no issues, 1 = issues found
                return result.stdout
            else:
                raise Exception(f"Checkstyle failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise Exception("Checkstyle analysis timed out")
        except FileNotFoundError:
            raise Exception("Checkstyle not found. Please install Checkstyle: https://checkstyle.sourceforge.io/")
    
    def _parse_checkstyle_xml(self, xml_output: str) -> tuple:
        """Parse Checkstyle XML output into errors and warnings"""
        errors = []
        warnings = []
        
        try:
            if not xml_output.strip():
                return errors, warnings
            
            root = ET.fromstring(xml_output)
            
            for file_elem in root.findall('file'):
                filename = file_elem.get('name', '')
                
                for error_elem in file_elem.findall('error'):
                    issue = {
                        'line': int(error_elem.get('line', 0)),
                        'column': int(error_elem.get('column', 0)),
                        'severity': error_elem.get('severity', 'warning'),
                        'message': error_elem.get('message', ''),
                        'source': error_elem.get('source', ''),
                        'symbol': self._extract_rule_name(error_elem.get('source', ''))
                    }
                    
                    if issue['severity'].lower() == 'error':
                        errors.append(issue)
                    else:
                        warnings.append(issue)
                        
        except ET.ParseError as e:
            # If XML parsing fails, try to extract issues from plain text
            return self._parse_checkstyle_text(xml_output)
        
        return errors, warnings
    
    def _extract_rule_name(self, source: str) -> str:
        """Extract rule name from Checkstyle source"""
        if not source:
            return "unknown"
        
        # Extract the last part after the last dot
        parts = source.split('.')
        if parts:
            return parts[-1]
        return source
    
    def _parse_checkstyle_text(self, text_output: str) -> tuple:
        """Fallback parser for plain text Checkstyle output"""
        errors = []
        warnings = []
        
        lines = text_output.split('\n')
        for line in lines:
            line = line.strip()
            if not line or 'Starting audit' in line or 'Audit done' in line:
                continue
            
            # Parse line format: [WARN] file.java:line:column: message [RuleName]
            match = re.match(r'\[(\w+)\]\s+.*?:(\d+):(\d+):\s+(.*?)\s+\[([^\]]+)\]', line)
            if match:
                severity, line_num, col_num, message, rule = match.groups()
                
                issue = {
                    'line': int(line_num),
                    'column': int(col_num),
                    'severity': severity.lower(),
                    'message': message.strip(),
                    'source': rule,
                    'symbol': rule
                }
                
                if severity.lower() == 'error':
                    errors.append(issue)
                else:
                    warnings.append(issue)
        
        return errors, warnings
    
    def _calculate_complexity_metrics(self, code: str) -> tuple:
        """Calculate complexity and maintainability metrics for Java code"""
        
        # Basic complexity calculation based on code patterns
        complexity_score = 1  # Base complexity
        
        # Count complexity-adding constructs
        if_statements = len(re.findall(r'\bif\s*\(', code))
        while_loops = len(re.findall(r'\bwhile\s*\(', code))
        for_loops = len(re.findall(r'\bfor\s*\(', code))
        switch_statements = len(re.findall(r'\bswitch\s*\(', code))
        catch_blocks = len(re.findall(r'\bcatch\s*\(', code))
        ternary_ops = len(re.findall(r'\?.*:', code))
        
        # Add to complexity
        complexity_score += if_statements
        complexity_score += while_loops
        complexity_score += for_loops
        complexity_score += switch_statements * 2  # Switch adds more complexity
        complexity_score += catch_blocks
        complexity_score += ternary_ops
        
        # Calculate lines of code
        lines = [line for line in code.split('\n') if line.strip() and not line.strip().startswith('//')]
        loc = len(lines)
        
        # Count methods and classes
        methods = len(re.findall(r'\b(public|private|protected|static).*?\b\w+\s*\([^)]*\)\s*{', code))
        classes = len(re.findall(r'\bclass\s+\w+', code))
        
        # Calculate maintainability index (simplified version)
        # Based on Halstead metrics and cyclomatic complexity
        if loc > 0:
            avg_complexity_per_method = complexity_score / max(1, methods)
            comment_ratio = len(re.findall(r'//.*|/\*.*?\*/', code, re.DOTALL)) / loc
            
            # Simplified maintainability formula
            maintainability = 100 - (avg_complexity_per_method * 5) - (loc / 20)
            maintainability += comment_ratio * 10  # Bonus for comments
            
            # Normalize to 0-100 range
            maintainability = max(0, min(100, maintainability))
        else:
            maintainability = 100
        
        return float(complexity_score), float(maintainability)
    
    def analyze(self, code: str) -> JavaAnalysisResult:
        """Analyze Java code and return results"""
        
        # Check if Checkstyle is available
        if not self._check_checkstyle_availability():
            # Fallback to basic analysis if Checkstyle is not available
            return self._basic_java_analysis(code)
        
        # Create temporary Java file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name
        
        try:
            # Run Checkstyle analysis
            xml_output = self._run_checkstyle_analysis(temp_file_path)
            
            # Parse results
            errors, warnings = self._parse_checkstyle_xml(xml_output)
            
            # Calculate complexity metrics
            complexity, maintainability = self._calculate_complexity_metrics(code)
            
            return JavaAnalysisResult(
                language="Java",
                errors=errors,
                warnings=warnings,
                total_issues=len(errors) + len(warnings),
                complexity=complexity,
                maintainability_index=maintainability
            )
            
        except Exception as e:
            # Fallback to basic analysis if Checkstyle fails
            print(f"Checkstyle analysis failed: {e}")
            return self._basic_java_analysis(code)
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    def _basic_java_analysis(self, code: str) -> JavaAnalysisResult:
        """Basic Java analysis without external tools"""
        errors = []
        warnings = []
        
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Basic syntax checks
            if line and not line.startswith('//') and not line.startswith('/*'):
                # Check for common issues
                if line.endswith(';') and (line.startswith('if') or line.startswith('while') or line.startswith('for')):
                    errors.append({
                        'line': i,
                        'column': 1,
                        'severity': 'error',
                        'message': 'Control statement should not end with semicolon',
                        'source': 'BasicSyntaxCheck',
                        'symbol': 'ControlStatementSemicolon'
                    })
                
                # Check for missing semicolons (basic heuristic)
                if (line and not line.endswith((';', '{', '}', ')', '//', '*/')) 
                    and not line.startswith(('@', 'package', 'import', 'public class', 'private class', 'class'))
                    and not any(keyword in line for keyword in ['if', 'else', 'while', 'for', 'try', 'catch', 'finally'])):
                    
                    # Skip comments and empty lines
                    if not re.match(r'^\s*(//|/\*|\*|\*/)', line):
                        warnings.append({
                            'line': i,
                            'column': len(line),
                            'severity': 'warning',
                            'message': 'Statement might be missing semicolon',
                            'source': 'BasicSyntaxCheck',
                            'symbol': 'MissingSemicolon'
                        })
                
                # Check for very long lines
                if len(line) > 120:
                    warnings.append({
                        'line': i,
                        'column': 120,
                        'severity': 'warning',
                        'message': f'Line too long ({len(line)} characters)',
                        'source': 'LineLengthCheck',
                        'symbol': 'LineLength'
                    })
                
                # Check for tabs
                if '\t' in line:
                    warnings.append({
                        'line': i,
                        'column': line.find('\t') + 1,
                        'severity': 'warning',
                        'message': 'Use spaces instead of tabs',
                        'source': 'WhitespaceCheck',
                        'symbol': 'TabCharacter'
                    })
        
        # Calculate metrics
        complexity, maintainability = self._calculate_complexity_metrics(code)
        
        return JavaAnalysisResult(
            language="Java",
            errors=errors,
            warnings=warnings,
            total_issues=len(errors) + len(warnings),
            complexity=complexity,
            maintainability_index=maintainability
        )
    
    def __del__(self):
        """Cleanup temporary files"""
        try:
            if self.config_file and os.path.exists(self.config_file.name):
                os.unlink(self.config_file.name)
        except:
            pass

# Global analyzer instance
_java_analyzer = None

def analyze_java_code(code: str, language: str='java') -> JavaAnalysisResult:
    """Analyze Java code using Checkstyle"""
    global _java_analyzer
    
    if _java_analyzer is None:
        _java_analyzer = JavaAnalyzer()
    
    return _java_analyzer.analyze(code)

def analyze_code(code: str, language: str) -> JavaAnalysisResult:
    """Main entry point for code analysis"""
    if language.lower() in ['java']:
        return analyze_java_code(code, language)
    else:
        # Fallback for unsupported languages
        return JavaAnalysisResult(
            language=language,
            errors=[],
            warnings=[{
                'line': 1,
                'column': 1,
                'severity': 'warning',
                'message': f'Analysis not yet implemented for {language}',
                'source': 'UnsupportedLanguage',
                'symbol': 'NotImplemented'
            }],
            total_issues=1,
            complexity=1.0,
            maintainability_index=75.0
        )