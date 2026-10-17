"""Pwnforge catalogue: authoring source and importer.

The authoring source of truth lives in :mod:`backend.app.catalog.content`.
``build_catalog`` materialises it into versioned YAML/JSON under ``catalog/``;
``importer`` loads those files into the database. This keeps a deterministic,
reviewable pipeline from authored content to runtime records.
"""
