"""Shared pytest fixtures and Hypothesis configuration.

This module provides pytest fixtures and configures Hypothesis profiles
for the test suite.
"""

from __future__ import annotations

from hypothesis import Verbosity, settings

# Configure Hypothesis settings for the test suite
settings.register_profile("ci", max_examples=200, deadline=None)
settings.register_profile("dev", max_examples=50, deadline=None)
settings.register_profile("debug", max_examples=10, deadline=None, verbosity=Verbosity.verbose)
