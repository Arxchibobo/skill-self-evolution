#!/usr/bin/env python3
"""
Template Generator - 模板生成器

从成功模式中提取可复用的代码模板。

核心功能：
1. 模板提取 - 从成功案例中提取通用结构
2. 占位符生成 - 识别可变部分并创建占位符
3. 模板分类 - 按产品类型、样式等分类
4. 模板验证 - 确保生成的模板有效且完整

模板格式：
{
    "id": "template_001",
    "name": "SaaS Landing Hero Section",
    "category": "landing-page",
    "domains": ["product", "style"],
    "tech_stack": "html-tailwind",
    "template": "<section>...</section>",
    "placeholders": {
        "{{title}}": "Main heading text",
        "{{subtitle}}": "Subtitle or description"
    },
    "metadata": {
        "success_rate": 0.85,
        "usage_count": 15,
        "avg_quality_score": 0.88
    }
}

Author: Bobo (Self-Evolution Skill)
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TemplateGenerator:
    """模板生成器主类"""

    def __init__(self):
        self.data_dir = PROJECT_ROOT / 'data'
        self.patterns_dir = self.data_dir / 'patterns'
        self.templates_dir = self.data_dir / 'templates'
        self.templates_dir.mkdir(exist_ok=True)

        # 占位符模式
        self.placeholder_patterns = {
            # 颜色
            'color': r'#[0-9A-Fa-f]{6}',
            # 字体名称
            'font': r'font-family:\s*["\']([^"\']+)["\']',
            # 数字值
            'number': r'\b\d+(?:\.\d+)?\b',
            # 文本内容
            'text': r'(?:>|"|\')([^<>"\']{10,})(?:<|"|\')',
            # 类名
            'className': r'className=["\']([^"\']+)["\']',
            # URL/路径
            'url': r'(?:src|href)=["\']([^"\']+)["\']'
        }

    def load_patterns(self, date: Optional[str] = None) -> Optional[Dict]:
        """加载模式数据

        Args:
            date: 日期字符串 (YYYY-MM-DD)，None 表示加载最新

        Returns:
            模式数据字典
        """
        if date:
            pattern_file = self.patterns_dir / f'{date}.json'
        else:
            pattern_file = self.patterns_dir / 'latest.json'

        if not pattern_file.exists():
            return None

        with open(pattern_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def extract_common_structure(self, code_samples: List[str]) -> str:
        """提取代码样本的通用结构

        Args:
            code_samples: 代码样本列表

        Returns:
            通用结构模板
        """
        if not code_samples:
            return ""

        # 如果只有一个样本，直接使用
        if len(code_samples) == 1:
            return code_samples[0]

        # 找到所有样本的公共部分
        # 这是一个简化实现，实际应该使用更复杂的 diff 算法
        common = code_samples[0]

        for sample in code_samples[1:]:
            common = self._find_common_parts(common, sample)

        return common

    def _find_common_parts(self, str1: str, str2: str) -> str:
        """找到两个字符串的公共部分（简化实现）"""
        # 按行分割
        lines1 = str1.split('\n')
        lines2 = str2.split('\n')

        common_lines = []
        for l1, l2 in zip(lines1, lines2):
            if l1 == l2:
                common_lines.append(l1)
            else:
                # 如果行不同，尝试找到公共的前缀/后缀
                common_lines.append(self._extract_common_line(l1, l2))

        return '\n'.join(common_lines)

    def _extract_common_line(self, line1: str, line2: str) -> str:
        """从两行中提取公共部分"""
        # 找到公共前缀
        i = 0
        while i < min(len(line1), len(line2)) and line1[i] == line2[i]:
            i += 1

        prefix = line1[:i]

        # 找到公共后缀
        j = 0
        while j < min(len(line1) - i, len(line2) - i) and \
              line1[-(j+1)] == line2[-(j+1)]:
            j += 1

        suffix = line1[-j:] if j > 0 else ''

        # 中间部分用占位符
        if i < len(line1) - j:
            middle = '{{variable}}'
        else:
            middle = ''

        return prefix + middle + suffix

    def generate_placeholders(self, template: str) -> Dict[str, str]:
        """为模板生成占位符

        Args:
            template: 原始模板字符串

        Returns:
            占位符字典 {placeholder: description}
        """
        placeholders = {}
        counter = defaultdict(int)

        # 颜色占位符
        colors = re.findall(self.placeholder_patterns['color'], template)
        for i, color in enumerate(set(colors), 1):
            placeholder = f'{{{{color_{i}}}}}'
            placeholders[placeholder] = f'Color value (original: {color})'
            template = template.replace(color, placeholder, 1)

        # 字体占位符
        fonts = re.findall(self.placeholder_patterns['font'], template)
        for i, font in enumerate(set(fonts), 1):
            placeholder = f'{{{{font_{i}}}}}'
            placeholders[placeholder] = f'Font family (original: {font})'
            pattern = f'font-family:\\s*["\']({re.escape(font)})["\']'
            template = re.sub(pattern, f'font-family: "{placeholder}"', template, count=1)

        # URL 占位符
        urls = re.findall(self.placeholder_patterns['url'], template)
        for i, url in enumerate(set(urls), 1):
            if url.startswith('http') or url.startswith('/'):
                placeholder = f'{{{{url_{i}}}}}'
                placeholders[placeholder] = f'URL or path (original: {url})'
                template = template.replace(url, placeholder, 1)

        return placeholders

    def categorize_template(self, pattern: Dict) -> Dict[str, Any]:
        """对模板进行分类

        Args:
            pattern: 模式数据

        Returns:
            分类信息
        """
        categories = {
            'primary': None,
            'secondary': [],
            'tech_stack': 'html-tailwind',
            'complexity': 'medium'
        }

        # 从模式的元素使用情况推断主要类别
        elements = pattern.get('elements_used', {})

        # 检查是否是特定产品类型
        if 'product_type' in pattern:
            categories['primary'] = pattern['product_type']
        elif 'saas' in str(elements).lower():
            categories['primary'] = 'saas'
        elif 'ecommerce' in str(elements).lower() or 'shop' in str(elements).lower():
            categories['primary'] = 'ecommerce'
        elif 'portfolio' in str(elements).lower():
            categories['primary'] = 'portfolio'
        else:
            categories['primary'] = 'general'

        # 检查样式类型
        styles = elements.get('styles', [])
        if styles:
            categories['secondary'].extend(styles)

        # 检查技术栈
        if 'react' in str(pattern).lower():
            categories['tech_stack'] = 'react'
        elif 'vue' in str(pattern).lower():
            categories['tech_stack'] = 'vue'
        elif 'nextjs' in str(pattern).lower() or 'next.js' in str(pattern).lower():
            categories['tech_stack'] = 'nextjs'

        # 评估复杂度
        code_lines = pattern.get('code_lines', 0)
        components_count = pattern.get('components_count', 0)

        if code_lines > 200 or components_count > 5:
            categories['complexity'] = 'high'
        elif code_lines < 50 or components_count <= 2:
            categories['complexity'] = 'low'

        return categories

    def create_template(self, pattern: Dict, pattern_id: str) -> Dict[str, Any]:
        """从模式创建模板

        Args:
            pattern: 成功模式
            pattern_id: 模式标识符

        Returns:
            模板对象
        """
        # 提取代码
        code = pattern.get('code', '')
        if not code:
            # 尝试从其他字段获取代码
            code = pattern.get('output', '')

        # 生成基础模板
        template_str = code

        # 生成占位符
        placeholders = self.generate_placeholders(template_str)

        # 分类
        categories = self.categorize_template(pattern)

        # 生成元数据
        metadata = {
            'success_rate': pattern.get('success_rate', 0.0),
            'usage_count': pattern.get('usage_count', 0),
            'avg_quality_score': pattern.get('avg_quality', 0.0),
            'created_at': datetime.now().isoformat(),
            'source_pattern_id': pattern_id
        }

        # 构建模板对象
        template = {
            'id': f'template_{pattern_id}',
            'name': self._generate_template_name(categories, pattern),
            'category': categories['primary'],
            'subcategories': categories['secondary'],
            'tech_stack': categories['tech_stack'],
            'complexity': categories['complexity'],
            'template': template_str,
            'placeholders': placeholders,
            'metadata': metadata,
            'usage_hints': self._generate_usage_hints(pattern, categories)
        }

        return template

    def _generate_template_name(self, categories: Dict, pattern: Dict) -> str:
        """生成模板名称"""
        primary = categories.get('primary', 'General').title()
        complexity = categories.get('complexity', 'Medium').title()

        # 尝试从模式中提取更具体的名称
        if 'hero' in str(pattern).lower():
            section = 'Hero Section'
        elif 'pricing' in str(pattern).lower():
            section = 'Pricing Section'
        elif 'testimonial' in str(pattern).lower():
            section = 'Testimonial Section'
        elif 'cta' in str(pattern).lower():
            section = 'CTA Section'
        else:
            section = 'Component'

        return f'{primary} {section} ({complexity})'

    def _generate_usage_hints(self, pattern: Dict, categories: Dict) -> List[str]:
        """生成使用提示"""
        hints = []

        # 基于复杂度的提示
        complexity = categories.get('complexity', 'medium')
        if complexity == 'high':
            hints.append('This is a complex template - consider breaking it into smaller components')
        elif complexity == 'low':
            hints.append('This is a simple, single-purpose template - easy to customize')

        # 基于样式的提示
        subcategories = categories.get('secondary', [])
        if 'glassmorphism' in subcategories:
            hints.append('Uses glassmorphism effect - requires backdrop-blur support')
        if 'dark mode' in str(subcategories).lower():
            hints.append('Includes dark mode support - uses dark: prefix')

        # 基于技术栈的提示
        tech_stack = categories.get('tech_stack', 'html-tailwind')
        if tech_stack == 'react':
            hints.append('React component - uses hooks and state management')
        elif tech_stack == 'vue':
            hints.append('Vue component - uses Composition API')

        return hints

    def generate(self, verbose: bool = True, min_quality: float = 0.75) -> Dict[str, Any]:
        """生成所有模板

        Args:
            verbose: 详细输出
            min_quality: 最小质量分数

        Returns:
            生成结果
        """
        if verbose:
            print("🎨 Starting template generation...")

        # 加载模式
        patterns_data = self.load_patterns()
        if not patterns_data:
            print("❌ No patterns data found")
            return {'status': 'no_data'}

        # 提取成功模式
        success_patterns = patterns_data.get('success_patterns', [])
        if not success_patterns:
            print("❌ No success patterns found")
            return {'status': 'no_patterns'}

        if verbose:
            print(f"📊 Found {len(success_patterns)} success patterns")

        # 生成模板
        templates = []
        for i, pattern in enumerate(success_patterns):
            # 检查质量
            quality = pattern.get('avg_quality', 0.0)
            if quality < min_quality:
                continue

            try:
                template = self.create_template(pattern, f'{i+1:03d}')
                templates.append(template)

                if verbose:
                    print(f"✅ Generated: {template['name']}")
            except Exception as e:
                if verbose:
                    print(f"⚠️  Failed to generate template {i+1}: {e}")

        # 保存模板
        if templates:
            output = {
                'generated_at': datetime.now().isoformat(),
                'total_templates': len(templates),
                'min_quality_threshold': min_quality,
                'templates': templates
            }

            output_file = self.templates_dir / 'latest.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            # 也保存一份带日期的副本
            date_str = datetime.now().strftime('%Y-%m-%d')
            dated_file = self.templates_dir / f'{date_str}.json'
            with open(dated_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            if verbose:
                print(f"\n✅ Generated {len(templates)} templates")
                print(f"💾 Saved to: {output_file}")

            return {
                'status': 'success',
                'templates_count': len(templates),
                'file': str(output_file)
            }
        else:
            if verbose:
                print("⚠️  No templates generated (quality threshold too high?)")
            return {
                'status': 'no_templates',
                'reason': 'No patterns met quality threshold'
            }


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='Template Generator - 模板生成器')
    parser.add_argument('--min-quality', type=float, default=0.75,
                       help='最小质量分数 (默认: 0.75)')
    parser.add_argument('--quiet', action='store_true', help='静默模式')

    args = parser.parse_args()

    try:
        generator = TemplateGenerator()
        result = generator.generate(
            verbose=not args.quiet,
            min_quality=args.min_quality
        )

        sys.exit(0 if result['status'] == 'success' else 1)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
