"""V3 PDF-to-graph architecture: read, map, extract, check, merge, ask.

The plan and the reasons for each boundary are in docs/PIANO_V3.md. This
package currently holds the shared contracts and the interchangeable reviewers
used by every gate; the stations are implemented against these contracts.
It is not yet wired into the application.
"""
