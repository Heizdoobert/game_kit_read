// Headless Ghidra script: label IL2CPP methods from Il2CppDumper script.json, decompile chosen targets.
// args: <script.json> <targets.txt> <outdir>
// targets.txt: one per line, Java regex matched (find) against "Namespace.Class$$Method". '#' comments ok.
import com.google.gson.stream.JsonReader;
import ghidra.app.decompiler.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

public class Il2CppDecomp extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] a = getScriptArgs();
        if (a.length < 3) { printerr("args: script.json targets.txt outdir"); return; }
        Path outDir = Paths.get(a[2]); Files.createDirectories(outDir);
        List<Pattern> pats = new ArrayList<>();
        for (String l : Files.readAllLines(Paths.get(a[1]))) {
            l = l.trim(); if (l.isEmpty() || l.startsWith("#")) continue;
            pats.add(Pattern.compile(l));
        }
        Address base = currentProgram.getImageBase();
        SymbolTable st = currentProgram.getSymbolTable();
        Map<Long, String> names = new HashMap<>();
        List<long[]> hits = new ArrayList<>(); List<String> hitNames = new ArrayList<>();
        List<String[]> strs = new ArrayList<>();
        try (JsonReader r = new JsonReader(new InputStreamReader(new FileInputStream(a[0]), "UTF-8"))) {
            r.beginObject();
            while (r.hasNext()) {
                String k = r.nextName();
                if (k.equals("ScriptMethod")) {
                    r.beginArray();
                    while (r.hasNext()) {
                        long addr = 0; String name = "", sig = "";
                        r.beginObject();
                        while (r.hasNext()) {
                            String f = r.nextName();
                            if (f.equals("Address")) addr = r.nextLong();
                            else if (f.equals("Name")) name = r.nextString();
                            else if (f.equals("Signature")) sig = r.nextString();
                            else r.skipValue();
                        }
                        r.endObject();
                        names.put(addr, name);
                        for (Pattern p : pats) if (p.matcher(name).find()) { hits.add(new long[]{addr}); hitNames.add(name + "\n" + sig); break; }
                    }
                    r.endArray();
                } else if (k.equals("ScriptString")) {
                    r.beginArray();
                    int i = 0;
                    while (r.hasNext()) {
                        long addr = 0; String v = "";
                        r.beginObject();
                        while (r.hasNext()) {
                            String f = r.nextName();
                            if (f.equals("Address")) addr = r.nextLong();
                            else if (f.equals("Value")) v = r.nextString();
                            else r.skipValue();
                        }
                        r.endObject();
                        String s = v.replaceAll("[^A-Za-z0-9]", "_");
                        if (s.length() > 40) s = s.substring(0, 40);
                        try { createLabel(base.add(addr), "STR_" + (++i) + "_" + s, true); } catch (Exception e) {}
                    }
                    r.endArray();
                } else r.skipValue();
            }
            r.endObject();
        }
        long[] sorted = names.keySet().stream().mapToLong(Long::longValue).sorted().toArray();
        println("methods=" + names.size() + " targets=" + hits.size());
        Listing li = currentProgram.getListing();
        // label every method (cheap) so callee names resolve
        for (Map.Entry<Long, String> e : names.entrySet()) {
            try { createLabel(base.add(e.getKey()), e.getValue().replace(' ', '-'), true); } catch (Exception x) {}
        }
        // functions: targets + their direct callees
        for (long[] h : hits) {
            Address ad = base.add(h[0]);
            mk(base, sorted, h[0]);
        }
        for (long[] h : hits) {
            Function f = getFunctionAt(base.add(h[0]));
            if (f == null) continue;
            for (Address ia : li.getInstructions(f.getBody(), true).hasNext() ? collect(li, f) : new ArrayList<Address>()) {
                for (Reference rf : getReferencesFrom(ia)) {
                    if (rf.getReferenceType().isCall()) {
                        Address t = rf.getToAddress();
                        if (names.containsKey(t.subtract(base))) mk(base, sorted, t.subtract(base));
                    }
                }
            }
        }
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        int ok = 0;
        for (int i = 0; i < hits.size(); i++) {
            Address ad = base.add(hits.get(i)[0]);
            Function f = getFunctionAt(ad);
            if (f == null) continue;
            DecompileResults res = di.decompileFunction(f, 120, monitor);
            if (!res.decompileCompleted()) { println("FAIL " + hitNames.get(i)); continue; }
            String[] nm = hitNames.get(i).split("\n");
            String fn = nm[0].replaceAll("[^A-Za-z0-9_.$<>,-]", "_");
            if (fn.length() > 150) fn = fn.substring(0, 150);
            String body = "// " + nm[0] + " @ " + ad + "\n// " + (nm.length > 1 ? nm[1] : "") + "\n" + res.getDecompiledFunction().getC().replaceAll("(?m)^/\\* WARNING:.*\\*/\\R", "");
            Files.write(outDir.resolve(fn + ".c"), body.getBytes("UTF-8"));
            ok++;
        }
        println("decompiled=" + ok);
    }
    // create function bounded by the next known method start (IL2CPP code ends in tail-branches; unbounded bodies bleed into neighbours)
    private void mk(Address base, long[] sorted, long off) throws Exception {
        Address a = base.add(off);
        if (getFunctionAt(a) != null) return;
        int i = Arrays.binarySearch(sorted, off);
        long end = (i + 1 < sorted.length) ? sorted[i + 1] : off + 0x400;
        if (end - off > 0x20000) end = off + 0x20000;
        AddressSet body = new AddressSet(a, base.add(end - 1));
        disassemble(a);
        Function c = getFunctionContaining(a);
        if (c != null) removeFunction(c); // earlier run's bleed-over body
        try { currentProgram.getFunctionManager().createFunction(null, a, body, SourceType.USER_DEFINED); }
        catch (ghidra.program.database.function.OverlappingFunctionException e) { println("overlap skip " + a); }
    }
    private List<Address> collect(Listing li, Function f) {
        List<Address> l = new ArrayList<>();
        InstructionIterator it = li.getInstructions(f.getBody(), true);
        while (it.hasNext()) l.add(it.next().getAddress());
        return l;
    }
}
