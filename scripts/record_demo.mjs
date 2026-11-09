import fs from "node:fs/promises";
import path from "node:path";
import { execFileSync } from "node:child_process";

const root = process.cwd();
const baseUrl = process.env.ROOK_WEB_URL || "http://localhost:3000";
const mediaDir = path.join(root, "docs", "media");

let chromium;
try {
  ({ chromium } = await import("playwright"));
} catch {
  console.error("Playwright is not installed. Install it with: npm install -D playwright && npx playwright install chromium");
  process.exit(2);
}

await fs.mkdir(mediaDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 960 }, deviceScaleFactor: 1 });
const frames = [];
for (const route of ["/", "/release-center", "/reliability", "/incidents"]) {
  await page.goto(`${baseUrl}${route}`, { waitUntil: "networkidle" });
  const name = route === "/" ? "demo-overview.png" : route.slice(1).replace("-", "_") + ".png";
  await page.screenshot({ path: path.join(mediaDir, name), fullPage: true });
  frames.push({ route, screenshot: name });
}

const frameDir = path.join(mediaDir, ".frames");
await fs.mkdir(frameDir, { recursive: true });
for (let index = 0; index < 16; index += 1) {
  await page.goto(`${baseUrl}/release-center`, { waitUntil: "networkidle" });
  await page.screenshot({ path: path.join(frameDir, `frame-${String(index).padStart(3, "0")}.png`), fullPage: true });
  await page.waitForTimeout(250);
}

try {
  execFileSync("ffmpeg", ["-y", "-framerate", "4", "-i", path.join(frameDir, "frame-%03d.png"), "-vf", "scale=1200:-1:flags=lanczos", "-loop", "0", path.join(mediaDir, "demo-release.gif")], { stdio: "inherit" });
} catch {
  console.warn("FFmpeg is unavailable. PNG screenshots were captured, but the GIF was not generated.");
}
await fs.writeFile(path.join(mediaDir, "recording-manifest.json"), JSON.stringify({ baseUrl, frames, recordedAt: new Date().toISOString() }, null, 2));
await browser.close();
console.log("Recorded real browser screenshots and available GIF output.");
