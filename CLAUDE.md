# Nanoptic Research — rules for Claude Code

Nanoptic is a one-person AI research lab directed by Seth. Focus: small, energy-efficient world models. The lab's base model is **Pico**, built from scratch. Full rules: `Nanoptic_Lab_Foundations_v1.1.pdf`.

## Your role
You write code from a study's `WORKORDER.md`. Seth is the director, not a programmer: he must be able to explain what every block of code does in plain English.

## Always
- Work only inside the study folder named in the workorder. Do only what the workorder lists; ask Seth before adding anything.
- Comment every block with what it does and why, in plain English. Prefer clear code over clever code.
- Fix and record random seeds; use `numpy.random.default_rng(seed)`; no global random state.
- Every figure and table comes from a script. Never hand-edit results.
- Fix code to pass tests; never weaken a test. If a test looks wrong, stop and say why.
- Report with evidence: commands run and their output.

## Never
- Run a study's measurement before its `card.md` is frozen (Seth gives you the commit hash).
- Use seeds reserved for future Pico testing (listed in each workorder).
- Interpret results or write claims. Report numbers with source labels (MEASURED, DERIVED, ASSUMED…); interpretation is Seth's job.
- Create a GitHub remote, push, or publish without Seth's explicit yes.
- Put large data or model files in the repo.
