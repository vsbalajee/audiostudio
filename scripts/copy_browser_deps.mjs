import { copyFileSync, mkdirSync, existsSync } from "node:fs";
import { join } from "node:path";
const input = join(process.cwd(), "node_modules", "lamejs", "lame.min.js");
const outputDir = join(process.cwd(), "web", "vendor");
if (!existsSync(input)) throw new Error("Run npm install before building the browser's MP3 encoder");
mkdirSync(outputDir, { recursive: true });
copyFileSync(input, join(outputDir, "lame.min.js"));
console.log("Browser MP3 encoder bundled into web/vendor/lame.min.js");
