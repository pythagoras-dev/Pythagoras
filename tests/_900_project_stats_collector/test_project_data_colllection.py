from pathlib import Path

from pythagoras._900_project_stats_collector.project_analyzer import analyze_project


def test_project_data_collection():
    dir_to_analyze = Path(__file__).parent.parent.parent.parent
    dir_to_analyze = str(dir_to_analyze)
    result = analyze_project(dir_to_analyze)
    print("\n")
    print(result)