# bp-taki

This repository contains an implementation of the TAKI card game in
Scenario-Based Programming (SBP), also known as Behavioral Programming (BP).
For an introduction to the paradigm, see Harel, Marron, and Weiss,
["Behavioral Programming"](https://doi.org/10.1145/2209249.2209270),
*Communications of the ACM*, 55(7), 90–100 (2012).

This repository accompanies the paper *“From Domain Knowledge to Composable
Reactive Code: LLM-Assisted Development with Scenario-Based Programming”*,
currently under review for ICECCS 2026. The paper and its supplementary
material are available in [`paper/`](./paper).

The implementation in this repository continues to evolve beyond the version
used in the paper. The current code includes additional hand-authored strategy
refinements and implementation extensions that are not part of the reported
evaluation.

For exact reproduction of the experiments reported in the paper, including the
evaluated code versions, prompts, generated strategies, configurations, and
simulation setup, see
[`taki-llm-experiments`](https://github.com/adielashrov/taki-llm-experiments).
