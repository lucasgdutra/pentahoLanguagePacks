#!/usr/bin/env python3
"""
Analyze Brazilian Portuguese translation completeness
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Configuration
DATA_DIR = Path("data/pt_BR")
TRANSLATE_MARKER = "TRANSLATE ME"

def analyze_file(filepath):
    """Analyze a single properties file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')

        total_entries = 0
        untranslated = 0

        for line in lines:
            # Skip comments and empty lines
            if line.strip() and not line.strip().startswith('#'):
                total_entries += 1
                if TRANSLATE_MARKER in line:
                    untranslated += 1

        return {
            'total': total_entries,
            'untranslated': untranslated,
            'translated': total_entries - untranslated
        }
    except Exception as e:
        return {'total': 0, 'untranslated': 0, 'translated': 0}

def main():
    print("=" * 80)
    print("Brazilian Portuguese (pt_BR) Translation Analysis")
    print("=" * 80)
    print()

    # Find all properties files
    properties_files = list(DATA_DIR.rglob("*.properties"))

    # Analyze each file
    stats_by_plugin = defaultdict(lambda: {'files': 0, 'total': 0, 'untranslated': 0, 'translated': 0})
    files_needing_work = []
    worst_files = []

    for filepath in properties_files:
        stats = analyze_file(filepath)

        if stats['total'] > 0:
            # Get plugin name (first directory under system or tomcat)
            rel_path = filepath.relative_to(DATA_DIR)
            if rel_path.parts[0] == 'system' and len(rel_path.parts) > 1:
                plugin = rel_path.parts[1]
            elif rel_path.parts[0] == 'tomcat':
                plugin = 'tomcat'
            else:
                plugin = 'other'

            # Update stats
            stats_by_plugin[plugin]['files'] += 1
            stats_by_plugin[plugin]['total'] += stats['total']
            stats_by_plugin[plugin]['untranslated'] += stats['untranslated']
            stats_by_plugin[plugin]['translated'] += stats['translated']

            # Track files needing work
            if stats['untranslated'] > 0:
                pct_untrans = (stats['untranslated'] / stats['total']) * 100
                files_needing_work.append({
                    'path': str(filepath.relative_to(DATA_DIR)),
                    'untranslated': stats['untranslated'],
                    'total': stats['total'],
                    'percent': pct_untrans
                })

                # Track worst offenders
                if stats['untranslated'] >= 100:
                    worst_files.append({
                        'path': str(filepath.relative_to(DATA_DIR)),
                        'untranslated': stats['untranslated'],
                        'total': stats['total'],
                        'percent': pct_untrans
                    })

    # Overall statistics
    total_files = len(properties_files)
    files_with_issues = len(files_needing_work)
    total_entries = sum(p['total'] for p in stats_by_plugin.values())
    total_untranslated = sum(p['untranslated'] for p in stats_by_plugin.values())
    total_translated = sum(p['translated'] for p in stats_by_plugin.values())

    print("OVERALL STATISTICS")
    print("-" * 80)
    print(f"Total .properties files:        {total_files}")
    print(f"Files with untranslated content: {files_with_issues} ({files_with_issues*100//total_files}%)")
    print(f"Files fully translated:          {total_files - files_with_issues}")
    print()
    print(f"Total property entries:          {total_entries}")
    print(f"Translated entries:              {total_translated} ({total_translated*100//total_entries}%)")
    print(f"Untranslated entries:            {total_untranslated} ({total_untranslated*100//total_entries}%)")
    print()

    # Sort by completion percentage
    sorted_plugins = sorted(stats_by_plugin.items(),
                           key=lambda x: x[1]['translated'] / max(x[1]['total'], 1),
                           reverse=True)

    print("TRANSLATION STATUS BY PLUGIN")
    print("-" * 80)
    print(f"{'Plugin':<30} {'Files':<8} {'Translated':<12} {'Untranslated':<12} {'%':<6}")
    print("-" * 80)

    for plugin, stats in sorted_plugins[:25]:  # Top 25
        if stats['total'] > 0:
            pct = (stats['translated'] / stats['total']) * 100
            print(f"{plugin[:30]:<30} {stats['files']:<8} {stats['translated']:<12} "
                  f"{stats['untranslated']:<12} {pct:>5.1f}%")

    print()

    # Worst files
    print("TOP 20 FILES NEEDING MOST TRANSLATION WORK")
    print("-" * 80)
    worst_sorted = sorted(worst_files, key=lambda x: x['untranslated'], reverse=True)[:20]

    for item in worst_sorted:
        filename = item['path'].split('/')[-1]
        plugin_path = '/'.join(item['path'].split('/')[:3])
        print(f"{item['untranslated']:>4} untranslated | {item['percent']:>5.1f}% | {plugin_path}/{filename}")

    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if total_untranslated > 0:
        print(f"⚠️  The Brazilian Portuguese language pack has {total_untranslated:,} ")
        print(f"   untranslated entries across {files_with_issues} files.")
        print()
        print(f"   Overall translation completion: {total_translated*100//total_entries}%")
        print()
        print("   Priority areas for translation:")

        # Find plugins with most untranslated content
        priority_plugins = sorted(stats_by_plugin.items(),
                                 key=lambda x: x[1]['untranslated'],
                                 reverse=True)[:5]

        for plugin, stats in priority_plugins:
            if stats['untranslated'] > 0:
                print(f"   - {plugin}: {stats['untranslated']} untranslated entries")
    else:
        print("✅ All content is fully translated!")

    print()
    print("=" * 80)

if __name__ == '__main__':
    main()
