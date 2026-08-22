import argparse
from monicraft import Monicraft

parser = argparse.ArgumentParser(description="Monicraft Dashboard")
parser.add_argument("--dummy", action="store_true", help="Run a dummy variant of the program to test out its capabilities.")
args = parser.parse_args()

app = Monicraft(is_dummy=args.dummy)
app.start_dashboard()
