"""Render pair for one lamp: the closed tube as a dark body, the diffuser as
the surface the light comes from.

Two models, one module each, so each is addressable by name -- ``uv run show
led_profiles.previz.body`` and likewise ``.diffuser`` -- and the two GLBs the
visualizer loads stay aligned by construction: both build off ``config.py``'s
own constants through ``assembly.previz_parts`` and ``profile``.

``body`` is the whole finished lamp minus the diffuser and the COB strip: the
aluminium extrusion, both endcaps, both glands and both cable stubs, each in
its installed place. The strip stays out because it is enclosed once the
diffuser closes the channel; the renderer never sees it. ``diffuser`` is the
snap-in COB diffuser on its own, in its clipped-in position.

A scene, not a print job -- neither file is printable, so both set
``IS_ASSEMBLY`` and the site offers no STL/STEP download for them.
"""
