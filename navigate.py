"""
navigate.py
─────────────────────────────────────────────────────────────
CLI entry point for the BuildingPath navigation system.

Usage:
    python navigate.py "büyük amfiye nasıl giderim"
    python navigate.py "Prof. Whitfield's office" --verbose
    python navigate.py   # interactive mode
"""

import sys
import os
from llm.navigator import Navigator


def main():
    args    = sys.argv[1:]
    verbose = "--verbose" in args or "-v" in args
    args    = [a for a in args if a not in ("--verbose", "-v")]

    if not os.environ.get("GROQ_API_KEY"):
        print("⚠️  GROQ_API_KEY environment variable not set.")
        print("   export GROQ_API_KEY='your-key-here'")
        sys.exit(1)

    print("🗺️  BuildingPath Navigation System")
    print("   Initialising...", end=" ", flush=True)
    nav = Navigator()
    print("ready.\n")

    if args:
        # Single query from command line
        query = " ".join(args)
        print(f"Query: {query}\n")
        response = nav.navigate(query, verbose=verbose)
        print(response)
    else:
        # Interactive mode
        print("Type your destination (or 'quit' to exit):\n")
        while True:
            try:
                query = input("  > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGüle güle!")
                break
            if not query:
                continue
            if query.lower() in ("quit", "exit", "q", "çık"):
                print("Güle güle!")
                break
            print()
            response = nav.navigate(query, verbose=verbose)
            print(response)
            print()


if __name__ == "__main__":
    main()
