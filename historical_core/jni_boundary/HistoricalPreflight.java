/*
 * JVM-only seam contract; not installed in the APK.
 * An upstream-integrated caller must provide trusted, decoded operation identity.
 */
package historical_core.jni_boundary;

import java.util.Objects;
import java.util.function.Supplier;

public final class HistoricalPreflight {
    public enum Kind { EVENT, BANNER, STORE, OTHER, UNKNOWN }
    public static final class Request {
        public final Kind kind;
        public final String contentKey;
        public final String selectedDay;
        public final boolean identityVerified;
        public Request(Kind kind, String contentKey, String selectedDay, boolean identityVerified) {
            this.kind = Objects.requireNonNull(kind);
            this.contentKey = contentKey;
            this.selectedDay = selectedDay;
            this.identityVerified = identityVerified;
        }
    }
    public interface Policy {
        boolean eligible(String contentKey, String selectedDay);
    }
    public static final class Denied extends RuntimeException {
        public Denied(String reason) { super(reason); }
    }

    private final Policy policy;
    public HistoricalPreflight(Policy policy) { this.policy = Objects.requireNonNull(policy); }

    /** Pure authorization gate: deny before native dispatch; never alter payloads or saves. */
    public <T> T dispatch(Request req, Supplier<T> nativeCall) {
        Objects.requireNonNull(req);
        Objects.requireNonNull(nativeCall);
        if (req.kind == Kind.STORE || req.kind == Kind.OTHER) {
            return nativeCall.get(); // Entirely owned by the original offline engine.
        }
        if (req.kind == Kind.UNKNOWN) {
            throw new Denied("operation_not_classified");
        }
        if (!req.identityVerified || req.contentKey == null || req.contentKey.isEmpty()
                || req.selectedDay == null || req.selectedDay.isEmpty()) {
            throw new Denied("identity_or_period_unverified");
        }
        if (!policy.eligible(req.contentKey, req.selectedDay)) {
            throw new Denied("historically_unavailable");
        }
        return nativeCall.get();
    }
}
