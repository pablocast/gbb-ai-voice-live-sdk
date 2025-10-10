from pathlib import Path
import asyncio

def load_instructions(instructions_file: str) -> str:
    """Load instructions from a file."""
    shared_path = Path(__file__).parent.resolve() / "shared"
    file_path = shared_path / instructions_file
    with file_path.open("r", encoding="utf-8", errors="ignore") as file:
        return file.read()
    

