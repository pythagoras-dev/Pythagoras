"""Update README.md and index.rst with project statistics.

This "test" runs against the actual project files (README.md and docs/source/index.rst)
to ensure that statistics are always up-to-date. It's a CI/CD action masquerading as
a regular test - it validates that the documentation can be updated with current stats
by actually updating the documentation files.

"""
import pytest
from pathlib import Path

from mixinforge.command_line_tools.project_analyzer import analyze_project
from mixinforge.command_line_tools._cli_entry_points import (
    _update_readme_if_possible
)


@pytest.mark.live_actions
def test_live_stats_update(pytestconfig):
    project_root = Path(pytestconfig.rootdir)

    readme_path = project_root / "README.md"

    # Validate README.md has required markers
    readme_content = readme_path.read_text()
    assert '<!-- MIXINFORGE_STATS_START -->' in readme_content, \
        "README.md missing <!-- MIXINFORGE_STATS_START --> marker"
    assert '<!-- MIXINFORGE_STATS_END -->' in readme_content, \
        "README.md missing <!-- MIXINFORGE_STATS_END --> marker"

    # # Validate docs/source/index.rst exists
    # index_rst_path = project_root / "docs" / "source" / "index.rst"
    # assert index_rst_path.exists(), f"index.rst not found at {index_rst_path}"
    #
    # # Validate index.rst has required markers
    # index_rst_content = index_rst_path.read_text()
    # assert '.. MIXINFORGE_STATS_START' in index_rst_content, \
    #     "index.rst missing .. MIXINFORGE_STATS_START marker"
    # assert '.. MIXINFORGE_STATS_END' in index_rst_content, \
    #     "index.rst missing .. MIXINFORGE_STATS_END marker"

    # Generate fresh statistics
    analysis = analyze_project(project_root, verbose=False)
    markdown_content = analysis.to_markdown()
    analysis.to_rst()

    # original_index_rst = index_rst_content

    # Attempt to update README.md
    updated_readme_path = _update_readme_if_possible(project_root, markdown_content)

    # Function returns None if content didn't change (already up-to-date)
    # This is valid and expected - verify the content is there regardless
    if updated_readme_path is not None:
        assert updated_readme_path == readme_path, \
            f"Updated path mismatch: expected {readme_path}, got {updated_readme_path}"
        status_readme = "updated"
    else:
        status_readme = "already up-to-date"


    # Attempt to update index.rst
    # updated_rst_path = _update_rst_docs_if_possible(project_root, rst_content)

    # Function returns None if content didn't change (already up-to-date)
    # if updated_rst_path is not None:
    #     assert updated_rst_path == index_rst_path, \
    #         f"Updated path mismatch: expected {index_rst_path}, got {updated_rst_path}"
    #     status_rst = "updated"
    # else:
    #     status_rst = "already up-to-date"


    # Display results with visual distinction
    print("\n")
    print("=" * 70)
    print("📊 STATS UPDATE (Live Action on Project)")
    print("=" * 70)
    print("✓ Validation successful:")
    print(f"  • README.md: {status_readme}")
    # print(f"  • index.rst: {status_rst}")
    print("=" * 70)
    print()
