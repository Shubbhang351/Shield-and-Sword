# Shield & Sword Go Engine

This is the Go deterministic decision core. The Python LLM analysis pipeline consumes results asynchronously and is not called from the synchronous evaluation path.

## Evaluation flow

1. An email, transaction, or security-event adapter normalizes the event into an `EvaluationRequest` with an `EntityType`, entity ID, and raw `Input`.
2. The engine selects active rules for the event type, merchant, and requested rulesets from an in-memory compiled-rule snapshot.
3. CEL identifiers are checked against the typed parameter catalog when rules are created or loaded. Rule authors choose from the catalog; the engine derives the referenced names from the checked CEL AST so parameter lists cannot drift from expressions.
4. Evaluation creates one session context. Raw input is available immediately. Other parameters are resolved only when CEL evaluates the corresponding identifier, then memoized for the rest of that evaluation.
5. Resolvers use bounded sources: event input, registered pure derived functions, in-memory lists/cache, or a Redis adapter for rolling velocity and aggregate values. JSON files are configuration persistence, not a per-event parameter source.
6. CEL evaluates precompiled programs. Boolean short-circuiting can avoid downstream parameter resolution; the rule engine must not prefetch every referenced parameter before evaluating the expression.
7. Weight rules run before action rules. Matching actions are resolved by precedence: WHITELIST, BLOCK, REVIEW, ALLOW. A missing or failed parameter follows the rule's explicit `on_parameter_error` action; it is never silently treated as false.
8. The engine returns the decision and triggered-rule details. An event publisher may send the normalized event and decision to the asynchronous Python LLM pipeline.

## Parameter catalog

The starter `data/parameters.json` catalog shows separate transaction, email, and security-event inputs, derived values, in-memory list values, and Redis velocity values. Rule authors may reference only catalogued parameters supported for the selected event type. Derived resolver names map to Go functions registered by the application; JSON cannot contain executable code.

Examples:

- Transaction: `amount > 100000 && attempts_ip_5m >= 4`
- Email: `spf_pass == false || dkim_pass == false || "example.test" in blocked_url_domains`
- Security event: `failed_logins_ip_5m >= 20 && requests_ip_1m >= 100`

## Persistence and cache boundaries

Rule-management services depend on `pkg/store.RuleStore` and `ParameterStore`. The initial `internal/store/jsonfile` adapter supports CRUD against versioned JSON catalogs with atomic file replacement. The engine does not import the adapter. A later database adapter can implement the same interfaces and be selected only in application wiring.

At startup, catalogs are loaded and active CEL expressions are checked and compiled into an immutable in-memory snapshot. Rule edits validate and compile the proposed snapshot before activation. The hot path reads that snapshot and does not scan JSON files. A Redis parameter adapter is separate from the rule-definition store and is needed only for cross-event counters and rolling aggregates. If V1 runs without Redis, those parameters must be unavailable or served by a single-process in-memory implementation; they cannot represent durable multi-instance history.

The JSON adapter is intended for a single writer/process. It is not a shared multi-replica database. Atomic replace prevents partial files; cross-process coordination and hot reload are later operational concerns.

## Current implementation slice

The directory structure, shared models, storage interfaces, JSON-file CRUD adapter, and starter parameter catalog are implemented. CEL session activation, lazy fetch/memoization, rule compilation/cache, and the HTTP/event entrypoints are later Phase 1 steps.
