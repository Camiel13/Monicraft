from rich.console import Console

def format_tag(tag):
    return tag.split(":")[1].replace("_", " ").title()
    
console = Console()