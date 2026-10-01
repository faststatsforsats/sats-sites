"""One module per data source. Each returns plain Python (lists of (date, value) pairs) and never writes files.

Every function takes care of its own retries and raises SourceError with a readable message when the
source is down, so the runner can skip that source, keep yesterday's file, and report it.
"""
