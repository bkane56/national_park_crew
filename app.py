from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from national_park_crew.app import launch


if __name__ == "__main__":
    launch()
