package historical_core.jni_boundary;

import java.util.concurrent.atomic.AtomicInteger;
import historical_core.jni_boundary.HistoricalPreflight.Kind;
import historical_core.jni_boundary.HistoricalPreflight.Request;
import historical_core.jni_boundary.HistoricalPreflight.Denied;

public final class HistoricalPreflightTest {
    private static final AtomicInteger calls = new AtomicInteger();
    private static String nativeCall() { calls.incrementAndGet(); return "native-response"; }
    private static void denied(HistoricalPreflight gate, Request request) {
        int before = calls.get();
        try { gate.dispatch(request, HistoricalPreflightTest::nativeCall); }
        catch (Denied expected) {
            if (calls.get() != before) throw new AssertionError("native mutated before denial");
            return;
        }
        throw new AssertionError("expected denial");
    }
    private static void forwarded(HistoricalPreflight gate, Request request) {
        int before = calls.get();
        String result = gate.dispatch(request, HistoricalPreflightTest::nativeCall);
        if (!"native-response".equals(result) || calls.get() != before + 1)
            throw new AssertionError("native not forwarded exactly once");
    }
    public static void main(String[] args) {
        HistoricalPreflight gate = new HistoricalPreflight((key, day) ->
            "banner:verified".equals(key) && day.compareTo("2016-07-08") >= 0);
        denied(gate, new Request(Kind.BANNER, "banner:verified", "2016-07-07", true));
        denied(gate, new Request(Kind.EVENT, "event:unknown", "2016-10-14", true));
        denied(gate, new Request(Kind.BANNER, "banner:verified", "2016-07-08", false));
        denied(gate, new Request(Kind.UNKNOWN, null, null, false));
        forwarded(gate, new Request(Kind.BANNER, "banner:verified", "2016-07-08", true));
        forwarded(gate, new Request(Kind.STORE, null, null, false));
        forwarded(gate, new Request(Kind.OTHER, null, null, false));
        System.out.println("7 JVM boundary scenarios passed; native callback calls=" + calls.get());
    }
}
