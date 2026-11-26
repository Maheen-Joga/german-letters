# german-letters

Formal German letters to DIN 5008 (cancellations, objections, GDPR requests) with the deadline
worked out and an English explanation of every paragraph. Pure Python, no dependencies.
Help with writing, not legal advice.

**Status: early development.** Built in small steps; checked items exist and are tested.

- [x] Letter model, DIN 5008 conventions check, plain-text output
- [x] Deadlines (§§ 187-193 BGB) and public holidays for all 16 states
- [x] Six letter templates with English explanations
- [x] Printable DIN 5008 Form B page
- [x] Command line: list, show, deadline, write
- [ ] Claude skill (SKILL.md) and full documentation

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
