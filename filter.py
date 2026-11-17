#!/usr/bin/env python3
from subscription_builder import build

if __name__ == "__main__":
    build("filtered.txt", "🇫🇮🇩🇪🇳🇱 FI-DE-NL AUTO", {"finland", "germany", "netherlands"})
