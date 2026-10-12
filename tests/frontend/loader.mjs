// Load unchanged UniApp ES modules with their @/ aliases and an in-memory uni API.
import vm from 'node:vm';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../../frontend/', import.meta.url));
export async function createFrontend() {
  const values = new Map();
  const requests = [];
  let responder;
  const uni = {
    setStorageSync: (key, value) => values.set(key, structuredClone(value)),
    getStorageSync: key => values.has(key) ? structuredClone(values.get(key)) : '',
    removeStorageSync: key => values.delete(key),
    showToast() {}, showLoading() {}, hideLoading() {}, reLaunch() {},
    request(options) {
      requests.push(options);
      if (!responder) throw new Error('Unexpected network call in isolated frontend test');
      responder(options);
    }
  };
  const context = vm.createContext({ uni, console: { log() {}, error() {} },
    setTimeout: callback => queueMicrotask(callback), clearTimeout() {} });
  const modules = new Map();
  async function load(name, parent = root) {
    let filename = name.startsWith('@/') ? path.join(root, name.slice(2)) : path.resolve(parent, name);
    if (!path.extname(filename)) {
      try { await fs.access(filename + '.js'); filename += '.js'; }
      catch { filename = path.join(filename, 'index.js'); }
    }
    if (!modules.has(filename)) {
      const module = new vm.SourceTextModule(await fs.readFile(filename, 'utf8'),
                                             { context, identifier: filename });
      modules.set(filename, module);
      await module.link(specifier => load(specifier, path.dirname(filename)));
    }
    return modules.get(filename);
  }
  return {
    requests, uni, respond: fn => { responder = fn; },
    async import(name) {
      const module = await load('@/' + name);
      if (module.status === 'linked') await module.evaluate();
      return module.namespace;
    }
  };
}
