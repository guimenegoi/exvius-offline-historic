# Java/JNI boundary feasibility spike (NOT a patched APK)

Verified by decompiling only `classes7.dex` from the independently SHA-256
verified official v0.1.30 APK. `DirectRules.respond()` calls
`NativeRules.localRequest(method, path, body, headers)` after local-file
resolution. `NativeRules.localRequest()` delegates to a native `request()`
method and decodes its response. `DirectFiles.materializeFile()` also calls
`NativeRules.localRequest()` directly: hooking only `DirectRules.respond()`
would be incomplete.

`HistoricalPreflight` demonstrates the **desired** pre-dispatch contract
with an injected native callback. It neither decompiles nor replaces the
native engine, and does not read or mutate the game's save or shop.

Tests (JDK 8 or newer; verified with OpenJDK 21 in an isolated compiler environment):

    javac -d /tmp/ffbe-jni-classes historical_core/jni_boundary/*.java
    java -cp /tmp/ffbe-jni-classes historical_core.jni_boundary.HistoricalPreflightTest

## Blocking integration conditions

1. A trustworthy parser must identify the decoded native operation and the
   actual event/banner ID. The legacy `source/server/endpoints.json` maps
   URLs to request classes, but is not verified against the v0.1.30 native
   implementation. URL-only classification is **insufficient**: different
   requests share endpoints (including bundle purchases and bundle status).
2. The selected historical date must be trusted and persist with the save,
   independently of user-provided request fields.
3. A verified approved-ID catalogue must exist. Research-only candidates
   cannot be promoted automatically.
4. The guard must cover listing **and** authoritative execution/reward entry
   points, including native-to-native paths that could bypass Java dispatch.
5. Denial response must use the game's expected protocol; throwing `Denied`
   is a test-only abstraction and must never be shipped directly.
6. Store operations must be forwarded untouched; missing classifications must
   not be guessed as safe store operations.
7. Build, sign, launch and end-to-end test on Android before claiming support.

Do not inject this prototype into the APK: it intentionally has no decoder,
real request mapping, release catalogue, serialization or safe integration ABI.
