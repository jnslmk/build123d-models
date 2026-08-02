"""Shared helpers that are not specific to any one model.

Anything in here earned its place by being needed twice. Model-specific
geometry, constants and assertions stay in the model's own package -- this is a
toolbox, not a dumping ground.

* ``edges``  -- edge treatments (chamfer helpers, boolean chamfer tools)
* ``checks`` -- point-sampling a solid and collecting pass/fail lines
* ``fits``   -- named FDM fit classes, so a clearance records its intent
"""
