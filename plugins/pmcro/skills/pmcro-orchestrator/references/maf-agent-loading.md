# MAF agent loading

MAF discovers `SKILL.md` packages, not arbitrary agent files. `assets/agents-index.json` is a registry consumed by an adapter.

The adapter must:

1. Read and validate the registry.
2. Resolve each path against the base the registry declares in `path_base`: `skill-root` (the default, and what the shipped entries use) or `registry`. Do not guess between them - the wrong choice fails as a missing-file error that reads like a packaging bug.
3. Reject absolute paths and traversal outside the plugin.
4. Load the phase skill.
5. Read the host-specific agent definition when the host supports it.
6. Create the MAF agent in code with tools and approval middleware.
7. Validate input and output envelopes.

The `agents/` folder is a projection/configuration layer. The phase `skills/` folders are the portable MAF capability layer.
