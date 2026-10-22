---
description: Install, set up, refresh the numbers or update your Fábrica (pixel-art factory of your funnel)
argument-hint: "[install | client \"Client name\" | numbers | update]"
---
Use the `fabrica` skill to handle this request: $ARGUMENTS

If the argument starts with `client`, install a factory for that client (agency plan).

If no argument was given: if a `fabrica/` folder with `.fabrica-licenca` exists in the current directory, ask whether to refresh the numbers or update the app; otherwise start the install.
