#!/usr/bin/env python3
"""
Quality Evaluator - 质量评估器

对 Skill 输出进行多维度质量评估，生成 0-1 范围的质量分数。

评估维度：
1. Completeness (完整性) - 是否包含所有必需元素
2. Consistency (一致性) - 代码风格、命名、结构是否统一
3. Professionalism (专业性) - 是否遵循最佳实践和行业标准
4. Performance (性能) - 代码效率、资源使用是否优化
5. Maintainability (可维护性) - 代码可读性、注释、模块化程度

算法：
Overall_Score = w1×Completeness + w2×Consistency + w3×Professionalism
              + w4×Performance + w5×Maintainability
其中 w1+w2+w3+w4+w5 = 1

Author: Bobo (Self-Evolution Skill)
"""

import json
import re
from typing import Dict, Any, List, Tuple
from pathlib import Path
import sys

# 添加父目录到路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


class QualityEvaluator:
    """质量评估器主类"""

    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        """初始化评估器

        Args:
            thresholds: 各维度的阈值配置
        """
        # 默认阈值
        self.thresholds = {
            'completeness': 0.8,
            'consistency': 0.7,
            'professionalism': 0.75,
            'performance': 0.7,
            'maintainability': 0.75
        }

        if thresholds:
            self.thresholds.update(thresholds)

        # 默认权重（可配置）
        self.weights = {
            'completeness': 0.25,
            'consistency': 0.20,
            'professionalism': 0.25,
            'performance': 0.15,
            'maintainability': 0.15
        }

    def evaluate_completeness(self, output: Dict[str, Any], context: Dict[str, Any]) -> Tuple[float, List[str]]:
        """评估完整性

        检查输出是否包含所有必需元素

        Args:
            output: Skill 生成的输出
            context: 执行上下文（包含要求的元素）

        Returns:
            (score, issues) 元组
        """
        issues = []
        required_elements = context.get('required_elements', [])

        if not required_elements:
            # 通用检查：基本元素
            required_elements = ['code', 'structure', 'styling']

        present_count = 0
        total_count = len(required_elements)

        for element in required_elements:
            # 检查是否存在
            element_present = False

            # 在输出文件中搜索相关内容
            if 'files' in output:
                for file_content in output['files'].values():
                    if element.lower() in str(file_content).lower():
                        element_present = True
                        break

            if element_present:
                present_count += 1
            else:
                issues.append(f"Missing required element: {element}")

        score = present_count / total_count if total_count > 0 else 1.0

        # 额外检查：代码是否太短（可能不完整）
        total_lines = 0
        if 'files' in output:
            for content in output['files'].values():
                total_lines += len(str(content).split('\n'))

        if total_lines < 20:
            score *= 0.8
            issues.append(f"Output seems too short ({total_lines} lines)")

        return score, issues

    def evaluate_consistency(self, output: Dict[str, Any]) -> Tuple[float, List[str]]:
        """评估一致性

        检查代码风格、命名、结构的统一性

        Args:
            output: Skill 生成的输出

        Returns:
            (score, issues) 元组
        """
        issues = []
        score = 1.0

        if 'files' not in output or not output['files']:
            return 0.5, ["No files to evaluate"]

        # 收集所有代码内容
        all_code = '\n'.join(str(content) for content in output['files'].values())

        # 1. 命名风格一致性（camelCase vs snake_case）
        camel_case_count = len(re.findall(r'\b[a-z]+[A-Z][a-zA-Z]*\b', all_code))
        snake_case_count = len(re.findall(r'\b[a-z]+_[a-z_]+\b', all_code))

        if camel_case_count > 0 and snake_case_count > 0:
            # 混合使用，检查是否合理（例如 JS 用 camelCase，Python 用 snake_case）
            ratio = min(camel_case_count, snake_case_count) / max(camel_case_count, snake_case_count)
            if ratio > 0.3:  # 过于混杂
                score *= 0.9
                issues.append(f"Mixed naming conventions: {camel_case_count} camelCase, {snake_case_count} snake_case")

        # 2. 缩进一致性（2 spaces vs 4 spaces vs tabs）
        lines = all_code.split('\n')
        indent_patterns = {'2spaces': 0, '4spaces': 0, 'tabs': 0}

        for line in lines:
            if line.startswith('  ') and not line.startswith('    '):
                indent_patterns['2spaces'] += 1
            elif line.startswith('    '):
                indent_patterns['4spaces'] += 1
            elif line.startswith('\t'):
                indent_patterns['tabs'] += 1

        if sum(indent_patterns.values()) > 0:
            max_indent = max(indent_patterns.values())
            other_indents = sum(indent_patterns.values()) - max_indent
            if other_indents / sum(indent_patterns.values()) > 0.2:
                score *= 0.85
                issues.append(f"Inconsistent indentation: {indent_patterns}")

        # 3. 引号风格（single vs double quotes）
        single_quotes = len(re.findall(r"'[^']*'", all_code))
        double_quotes = len(re.findall(r'"[^"]*"', all_code))

        if single_quotes > 0 and double_quotes > 0:
            ratio = min(single_quotes, double_quotes) / max(single_quotes, double_quotes)
            if ratio > 0.3:
                score *= 0.95
                issues.append(f"Mixed quote styles: {single_quotes} single, {double_quotes} double")

        return score, issues

    def evaluate_professionalism(self, output: Dict[str, Any]) -> Tuple[float, List[str]]:
        """评估专业性

        检查是否遵循最佳实践和行业标准

        Args:
            output: Skill 生成的输出

        Returns:
            (score, issues) 元组
        """
        issues = []
        score = 1.0

        if 'files' not in output or not output['files']:
            return 0.5, ["No files to evaluate"]

        all_code = '\n'.join(str(content) for content in output['files'].values())

        # 1. 检查是否有注释（专业代码应该有解释）
        comment_lines = len(re.findall(r'^\s*(/\*|//|#|<!--)', all_code, re.MULTILINE))
        total_lines = len(all_code.split('\n'))
        comment_ratio = comment_lines / total_lines if total_lines > 0 else 0

        if comment_ratio < 0.05:  # 少于 5% 的注释
            score *= 0.9
            issues.append(f"Low comment ratio: {comment_ratio:.1%}")

        # 2. 检查错误处理（try-catch, error checking）
        error_handling = len(re.findall(r'\b(try|catch|throw|error|Error|Exception)\b', all_code))
        if total_lines > 50 and error_handling == 0:
            score *= 0.85
            issues.append("No error handling detected in code >50 lines")

        # 3. 检查硬编码值（magic numbers）
        # 排除常见的 0, 1, 2, 100 等
        magic_numbers = re.findall(r'\b(?!0\b|1\b|2\b|100\b)\d{3,}\b', all_code)
        if len(magic_numbers) > 5:
            score *= 0.9
            issues.append(f"Too many magic numbers: {len(magic_numbers)} found")

        # 4. 检查是否使用了现代特性（ES6+, async/await 等）
        modern_features = len(re.findall(
            r'\b(const|let|async|await|arrow|=>|class|import|export|Promise)\b',
            all_code
        ))

        if total_lines > 30 and modern_features == 0:
            score *= 0.95
            issues.append("No modern language features detected")

        # 5. 检查是否有 TODO/FIXME（未完成的代码）
        todos = len(re.findall(r'\b(TODO|FIXME|HACK|XXX)\b', all_code, re.IGNORECASE))
        if todos > 3:
            score *= 0.9
            issues.append(f"Too many TODO/FIXME: {todos} found")

        return score, issues

    def evaluate_performance(self, output: Dict[str, Any]) -> Tuple[float, List[str]]:
        """评估性能

        检查代码效率和资源使用

        Args:
            output: Skill 生成的输出

        Returns:
            (score, issues) 元组
        """
        issues = []
        score = 1.0

        if 'files' not in output or not output['files']:
            return 0.5, ["No files to evaluate"]

        all_code = '\n'.join(str(content) for content in output['files'].values())

        # 1. 检查嵌套循环（O(n²) 或更差）
        nested_loops = len(re.findall(
            r'(for|while).*(for|while)',
            all_code,
            re.DOTALL
        ))
        if nested_loops > 2:
            score *= 0.85
            issues.append(f"Multiple nested loops detected: {nested_loops}")

        # 2. 检查低效的字符串拼接（在循环中）
        inefficient_concat = len(re.findall(
            r'(for|while).*\+\s*["\']',
            all_code,
            re.DOTALL
        ))
        if inefficient_concat > 0:
            score *= 0.9
            issues.append(f"Inefficient string concatenation in loops: {inefficient_concat}")

        # 3. 检查是否有缓存/记忆化
        has_caching = bool(re.search(r'\b(cache|memo|memoize|Map|WeakMap)\b', all_code))
        lines_count = len(all_code.split('\n'))

        if lines_count > 100 and not has_caching:
            # 大型代码但没有缓存，可能性能不佳
            score *= 0.95
            issues.append("Large code without caching mechanism")

        # 4. 检查是否有不必要的计算
        repeated_calls = len(re.findall(
            r'(\w+\([^)]*\)).*\1',  # 同一函数调用出现多次
            all_code
        ))
        if repeated_calls > 5:
            score *= 0.92
            issues.append(f"Potentially repeated function calls: {repeated_calls}")

        return score, issues

    def evaluate_maintainability(self, output: Dict[str, Any]) -> Tuple[float, List[str]]:
        """评估可维护性

        检查代码可读性、模块化程度

        Args:
            output: Skill 生成的输出

        Returns:
            (score, issues) 元组
        """
        issues = []
        score = 1.0

        if 'files' not in output or not output['files']:
            return 0.5, ["No files to evaluate"]

        all_code = '\n'.join(str(content) for content in output['files'].values())

        # 1. 检查函数/方法的平均长度
        functions = re.findall(
            r'(function\s+\w+|const\s+\w+\s*=.*=>|def\s+\w+)',
            all_code
        )
        total_lines = len(all_code.split('\n'))

        if functions:
            avg_function_length = total_lines / len(functions)
            if avg_function_length > 50:
                score *= 0.85
                issues.append(f"Functions too long: avg {avg_function_length:.0f} lines")

        # 2. 检查模块化程度（是否有多个文件）
        file_count = len(output.get('files', {}))
        if total_lines > 200 and file_count == 1:
            score *= 0.9
            issues.append(f"Large codebase ({total_lines} lines) in single file")

        # 3. 检查变量命名质量（单字母变量）
        single_letter_vars = len(re.findall(r'\b[a-z]\b(?!\s*[=:])', all_code))
        if single_letter_vars > 10:
            score *= 0.9
            issues.append(f"Too many single-letter variables: {single_letter_vars}")

        # 4. 检查复杂的嵌套结构
        max_nesting = 0
        current_nesting = 0
        for char in all_code:
            if char == '{':
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif char == '}':
                current_nesting -= 1

        if max_nesting > 5:
            score *= 0.85
            issues.append(f"Deeply nested code: {max_nesting} levels")

        # 5. 检查是否有文档字符串
        docstrings = len(re.findall(r'("""|\'\'\').*?\1', all_code, re.DOTALL))
        if functions and docstrings / len(functions) < 0.3:
            score *= 0.92
            issues.append(f"Low documentation: {docstrings}/{len(functions)} functions documented")

        return score, issues

    def evaluate(self, output: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """综合评估

        Args:
            output: Skill 生成的输出
            context: 执行上下文（可选）

        Returns:
            评估结果字典
        """
        if context is None:
            context = {}

        # 执行各维度评估
        completeness_score, completeness_issues = self.evaluate_completeness(output, context)
        consistency_score, consistency_issues = self.evaluate_consistency(output)
        professionalism_score, professionalism_issues = self.evaluate_professionalism(output)
        performance_score, performance_issues = self.evaluate_performance(output)
        maintainability_score, maintainability_issues = self.evaluate_maintainability(output)

        # 计算加权总分
        overall_score = (
            self.weights['completeness'] * completeness_score +
            self.weights['consistency'] * consistency_score +
            self.weights['professionalism'] * professionalism_score +
            self.weights['performance'] * performance_score +
            self.weights['maintainability'] * maintainability_score
        )

        # 构建结果
        result = {
            'overall': round(overall_score, 3),
            'dimensions': {
                'completeness': round(completeness_score, 3),
                'consistency': round(consistency_score, 3),
                'professionalism': round(professionalism_score, 3),
                'performance': round(performance_score, 3),
                'maintainability': round(maintainability_score, 3)
            },
            'issues': {
                'completeness': completeness_issues,
                'consistency': consistency_issues,
                'professionalism': professionalism_issues,
                'performance': performance_issues,
                'maintainability': maintainability_issues
            },
            'passed': overall_score >= self.thresholds.get('completeness', 0.8),
            'thresholds': self.thresholds
        }

        return result


def main():
    """命令行测试入口"""
    import argparse

    parser = argparse.ArgumentParser(description='Quality Evaluator - 评估代码质量')
    parser.add_argument('file', help='要评估的 JSON 文件（包含 output 字段）')
    args = parser.parse_args()

    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        evaluator = QualityEvaluator()
        result = evaluator.evaluate(data.get('output', {}), data.get('context', {}))

        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
