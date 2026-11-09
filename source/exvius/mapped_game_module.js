import { GL9_OFFSETS } from './gl9_export_offsets.js';

// Keep the normal Frida Module resolver as the primary path. Houdini's
// arm64 NativeBridge can map libgame.so without registering it in Frida's
// module list even though Frida's ARM64 Interceptor can hook the code.
// This read-only fallback is valid only for the PINNED GL9.0.0 ELF.
export function findMappedGameModule(note = () => {}) {
  if (Process.arch !== 'arm64' ||
      typeof File === 'undefined' ||
      typeof File.readAllText !== 'function') return null;
  let lines;
  try {
    lines = File.readAllText('/proc/self/maps').split('\n')
      .filter(line => /\/libgame\.so$/.test(line));
  } catch (_) {
    return null;
  }
  const first = lines.find(line => /\s00000000\s/.test(line));
  const match = first && /^([0-9a-f]+)-([0-9a-f]+)/.exec(first);
  if (!match) return null;
  const base = ptr('0x' + match[1]);
  try {
    if (base.readU32() !== 0x464c457f ||
        base.add(0x1e5b51c).readU32() !== 0xfc170fec ||
        base.add(0x1e49e34).readU32() !== 0xd10283ff) {
      note('STARTUP_MAPPED_GAME_SIGNATURE_MISMATCH base=' + base);
      return null;
    }
  } catch (_) {
    return null;
  }
  const end = Math.max(...lines.map(row => parseInt(
    /^([0-9a-f]+)-([0-9a-f]+)/.exec(row)[2], 16)));
  const size = end - parseInt(match[1], 16);
  const path = first.trim().split(/\s+/).pop();

  function findExportByName(name) {
    const offset = GL9_OFFSETS[name];
    if (offset !== undefined) return base.add(offset);
    // Imported C++ runtime functions are supplied by libc++, not libgame.
    if (name === '__dynamic_cast' || name === '_Znwm') {
      try {
        return Module.getGlobalExportByName(name);
      } catch (_) {
        return null;
      }
    }
    return null;
  }
  note('STARTUP_MAPPED_GAME_READY base=' + base +
    ' size=' + size + ' symbols=' + Object.keys(GL9_OFFSETS).length);
  return {
    name: 'libgame.so',
    path,
    base,
    size,
    findExportByName,
    getExportByName(name) {
      const address = findExportByName(name);
      if (!address) throw new Error('GL9 mapped export missing: ' + name);
      return address;
    },
  };
}
