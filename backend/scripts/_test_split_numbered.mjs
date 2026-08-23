/**
 * Unit check: OgeRusUI.splitNumberedOptions on the exact flat user string.
 * Run: node backend/scripts/_test_split_numbered.mjs
 */
import fs from "fs";
import path from "path";
import vm from "vm";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const UI_PATH = path.resolve(__dirname, "../../frontend/js/oge_rus_ui.js");

const FLAT =
  "Укажите варианты ответов, в которых верно определена грамматическая основа " +
  "в одном из предложений или в одной из частей сложного предложения текста. " +
  "Запишите номера ответов. " +
  "1) соль поддерживает (предложение 1) " +
  "2) может привести (предложение 2) " +
  "3) соль содержится (предложение 3) " +
  "4) организм получает (предложение 4) " +
  "5) он поглощает (предложение 5)";

const MULTILINE =
  "Укажите варианты ответов, в которых верно определена грамматическая основа " +
  "в одном из предложений или в одной из частей сложного предложения текста. " +
  "Запишите номера ответов.\n" +
  "1) соль поддерживает (предложение 1)\n" +
  "2) может привести (предложение 2)\n" +
  "3) соль содержится (предложение 3)\n" +
  "4) организм получает (предложение 4)\n" +
  "5) он поглощает (предложение 5)";

const code = fs.readFileSync(UI_PATH, "utf8");
const sandbox = { window: {}, console };
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const UI = sandbox.OgeRusUI || sandbox.window.OgeRusUI;
if (!UI?.splitNumberedOptions || !UI?.formatProseTaskHtml) {
  console.error("NO_SPLITTER in", UI_PATH);
  process.exit(2);
}

function check(label, text) {
  const before = text;
  const r = UI.splitNumberedOptions(text);
  const html = UI.formatProseTaskHtml(text);
  console.log("=== BEFORE (" + label + ") ===");
  console.log(before);
  console.log("=== AFTER stem/options ===");
  console.log("stem:", r.stem);
  console.log("n_options:", r.options.length);
  for (const o of r.options) console.log(`  ${o.id}) ${o.text}`);
  console.log("=== HTML ===");
  console.log(html);
  if (r.options.length !== 5) {
    console.error("FAIL: expected 5 options, got", r.options.length);
    process.exit(1);
  }
  if (r.options[0].id !== "1" || r.options[4].id !== "5") {
    console.error("FAIL: bad ids", r.options.map((o) => o.id));
    process.exit(1);
  }
  for (const o of r.options) {
    if (!/\(предложение \d+\)/.test(o.text)) {
      console.error("FAIL: (предложение N) must stay inside option text:", o);
      process.exit(1);
    }
  }
  const rows = (html.match(/oge-prose-opt/g) || []).length;
  if (rows < 5) {
    console.error("FAIL: html option rows", rows);
    process.exit(1);
  }
}

check("FLAT", FLAT);
check("MULTILINE", MULTILINE);
console.log("OK splitNumberedOptions");
