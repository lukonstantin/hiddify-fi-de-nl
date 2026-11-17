#!/usr/bin/env python3
from subscription_builder import build, COUNTRIES

if __name__ == "__main__":
    build("europe.txt", "🇪🇺 EUROPE AUTO", set(COUNTRIES))
