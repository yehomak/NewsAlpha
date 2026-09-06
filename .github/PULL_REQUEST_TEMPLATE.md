## What

<!--
1-3 bullets describing what changed.
-->

-

## Why

<!--
Which build stage does this implement, or what problem does it solve?
Reference CLAUDE.md stages where applicable.
-->

## Testing

- [ ] `ruff check . && ruff format --check .` pass
- [ ] `mypy app` passes
- [ ] `pytest` passes
- [ ] Docker build passes (if Dockerfile or docker-compose touched)
- [ ] Manual smoke test: <!-- describe what you ran and what you saw -->

## Notes

<!--
Tradeoffs made, known issues, follow-up tickets, anything a reviewer should know.
-->

---

**AI-assisted:** <!-- yes / no -->
**Prompt context:** <!-- what was asked; which stage of CLAUDE.md this implements -->
**Branch type:** <!-- agent/ feat/ fix/ -->
