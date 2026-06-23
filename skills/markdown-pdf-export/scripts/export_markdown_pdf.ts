const assert = require("node:assert/strict");
const childProcess = require("node:child_process");
const fsSync = require("node:fs");
const fs = require("node:fs/promises");
const path = require("node:path");
const os = require("node:os");
const { pathToFileURL } = require("node:url");

type Payload = {
  configPath?: string;
  workDir?: string;
  styleRoot?: string;
  pandocPath?: string;
  browserPath?: string;
};

type DocumentConfig = {
  input: string;
  output: string;
  title?: string;
  preset?: string;
  css?: string;
  resourcePath?: string;
  virtualTimeBudget?: number;
};

type ExportConfig = {
  defaults?: {
    preset?: string;
    resourcePath?: string;
    virtualTimeBudget?: number;
  };
  documents: DocumentConfig[];
};

const ALLOWED_PRESETS = new Set(["default", "compact", "resume"]);

// ponytail: one TS file is enough until config or browser handling truly diverges.

function parsePayload(): Payload {
  const payloadArg = process.argv.slice(2).find((arg: string) => arg.startsWith("--payload-base64="));
  if (!payloadArg) {
    throw new Error("Missing --payload-base64.");
  }

  return JSON.parse(Buffer.from(payloadArg.slice("--payload-base64=".length), "base64").toString("utf8"));
}

function stripBom(text: string): string {
  return text.replace(/^\uFEFF/, "");
}

async function readJson(filePath: string): Promise<ExportConfig> {
  const raw = stripBom(await fs.readFile(filePath, "utf8"));
  return JSON.parse(raw);
}

function runCommand(command: string, args: string[]): void {
  const result = childProcess.spawnSync(command, args, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });

  if (result.error) {
    throw result.error;
  }

  if (result.status !== 0) {
    const detail = (result.stderr || result.stdout || "").trim();
    throw new Error(`${path.basename(command)} failed${detail ? `: ${detail}` : ""}`);
  }
}

function findExecutable(commandName: string, candidatePaths: string[]): string {
  for (const candidate of candidatePaths) {
    if (candidate && fsSync.existsSync(candidate)) {
      try {
        return path.resolve(candidate);
      } catch {
        // ignore bad path candidates
      }
    }
  }

  const probeCommand = process.platform === "win32" ? "where.exe" : "which";
  const probe = childProcess.spawnSync(probeCommand, [commandName], { encoding: "utf8" });
  if (probe.status === 0) {
    const firstLine = (probe.stdout || "")
      .split(/\r?\n/)
      .map((line: string) => line.trim())
      .find((line: string) => line.length > 0);
    if (firstLine) {
      return firstLine;
    }
  }

  throw new Error(`Could not find executable: ${commandName}`);
}

function resolveMaybeAbsolute(value: string, baseDir: string): string {
  return path.isAbsolute(value) ? value : path.resolve(baseDir, value);
}

async function resolveStylePath(styleRootPath: string, workDir: string, preset?: string, css?: string): Promise<string> {
  if (css && css.trim()) {
    const candidate = resolveMaybeAbsolute(css.trim(), workDir);
    await fs.access(candidate);
    return candidate;
  }

  const presetName = preset && preset.trim() ? preset.trim() : "default";
  if (!ALLOWED_PRESETS.has(presetName)) {
    throw new Error(`Unsupported preset '${presetName}'. Supported presets: default, compact, resume`);
  }

  const presetPath = path.join(styleRootPath, `${presetName}.css`);
  await fs.access(presetPath);
  return presetPath;
}

async function waitForFileReady(filePath: string, timeoutMilliseconds = 60000): Promise<void> {
  const deadline = Date.now() + timeoutMilliseconds;
  let lastSize = -1;
  let stableChecks = 0;

  while (Date.now() <= deadline) {
    try {
      const stats = await fs.stat(filePath);
      if (stats.size > 0) {
        if (stats.size === lastSize) {
          stableChecks += 1;
          if (stableChecks >= 2) {
            return;
          }
        } else {
          stableChecks = 0;
        }

        lastSize = stats.size;
      }
    } catch {
      // wait for the file to appear
    }

    await new Promise((resolve) => setTimeout(resolve, 1000));
  }

  throw new Error(`Timed out waiting for output file: ${filePath}`);
}

function validateConfig(config: ExportConfig): void {
  if (!config || typeof config !== "object") {
    throw new Error("Config must be a JSON object.");
  }

  if (!Array.isArray(config.documents) || config.documents.length === 0) {
    throw new Error("Config must contain at least one document entry.");
  }

  for (const document of config.documents) {
    if (!document.input || !document.output) {
      throw new Error("Each document entry must contain both 'input' and 'output'.");
    }
  }
}

async function convertDocument(
  document: DocumentConfig,
  defaults: ExportConfig["defaults"],
  resolvedWorkDir: string,
  resolvedStyleRoot: string,
  resolvedPandocPath: string,
  resolvedBrowserPath: string,
  tempRoot: string,
  index: number,
): Promise<{ input: string; output: string; title: string; preset: string }> {
  const inputPath = resolveMaybeAbsolute(document.input, resolvedWorkDir);
  const outputPath = resolveMaybeAbsolute(document.output, resolvedWorkDir);

  await fs.access(inputPath);
  await fs.mkdir(path.dirname(outputPath), { recursive: true });

  const title = document.title?.trim() || path.basename(inputPath, path.extname(inputPath));
  const preset = document.preset?.trim() || defaults?.preset?.trim() || "default";
  const cssPath = await resolveStylePath(resolvedStyleRoot, resolvedWorkDir, preset, document.css);
  const resourcePath = resolveMaybeAbsolute(document.resourcePath?.trim() || defaults?.resourcePath?.trim() || ".", resolvedWorkDir);
  const virtualTimeBudget = Number.isInteger(document.virtualTimeBudget)
    ? Number(document.virtualTimeBudget)
    : Number.isInteger(defaults?.virtualTimeBudget)
      ? Number(defaults?.virtualTimeBudget)
      : 5000;

  const safeKey = `${String(index + 1).padStart(2, "0")}-${path.basename(outputPath, path.extname(outputPath)).replace(/[^a-zA-Z0-9._-]+/g, "-") || "document"}`;
  const htmlPath = path.join(tempRoot, `${safeKey}.html`);
  const headPath = path.join(tempRoot, `${safeKey}-head.html`);
  const tempPdfPath = path.join(tempRoot, `${safeKey}.pdf`);

  const styleMarkup = `<style>\n${await fs.readFile(cssPath, "utf8")}\n</style>\n`;
  await fs.writeFile(headPath, styleMarkup, "utf8");

  runCommand(resolvedPandocPath, [
    inputPath,
    "-f",
    "gfm",
    "-t",
    "html5",
    "-s",
    "--quiet",
    `--metadata=title:${title}`,
    "--embed-resources",
    `--resource-path=${resourcePath}`,
    "-H",
    headPath,
    "-o",
    htmlPath,
  ]);

  try {
    await fs.rm(tempPdfPath, { force: true });
  } catch {
    // ignore stale temp files
  }

  runCommand(resolvedBrowserPath, [
    "--headless",
    "--disable-gpu",
    "--allow-file-access-from-files",
    "--no-first-run",
    "--no-default-browser-check",
    `--virtual-time-budget=${virtualTimeBudget}`,
    "--no-pdf-header-footer",
    `--print-to-pdf=${tempPdfPath}`,
    pathToFileURL(htmlPath).href,
  ]);

  await waitForFileReady(tempPdfPath);
  await fs.copyFile(tempPdfPath, outputPath);

  return {
    input: inputPath,
    output: outputPath,
    title,
    preset: document.css?.trim() ? "custom" : preset,
  };
}

async function run(): Promise<void> {
  const payload = parsePayload();
  const resolvedWorkDir = path.resolve(payload.workDir?.trim() || ".");
  const resolvedConfigPath = resolveMaybeAbsolute(payload.configPath?.trim() || "pdf-export.config.json", resolvedWorkDir);
  const config = await readJson(resolvedConfigPath);
  validateConfig(config);

  const resolvedStyleRoot = payload.styleRoot?.trim()
    ? resolveMaybeAbsolute(payload.styleRoot.trim(), resolvedWorkDir)
    : path.resolve(path.join(__dirname, "..", "assets"));

  await fs.access(resolvedStyleRoot);

  const resolvedPandocPath = payload.pandocPath?.trim()
    ? (path.isAbsolute(payload.pandocPath.trim()) ? payload.pandocPath.trim() : findExecutable(payload.pandocPath.trim(), []))
    : findExecutable("pandoc", [path.join(process.env.LOCALAPPDATA || "", "Pandoc", "pandoc.exe")]);

  const resolvedBrowserPath = payload.browserPath?.trim()
    ? (path.isAbsolute(payload.browserPath.trim()) ? payload.browserPath.trim() : findExecutable(payload.browserPath.trim(), []))
    : findExecutable("msedge", [
        path.join(process.env["ProgramFiles(x86)"] || "", "Microsoft", "Edge", "Application", "msedge.exe"),
        path.join(process.env.ProgramFiles || "", "Microsoft", "Edge", "Application", "msedge.exe"),
        path.join(process.env.ProgramFiles || "", "Google", "Chrome", "Application", "chrome.exe"),
        "google-chrome",
        "chromium",
        "chromium-browser",
      ]);

  const tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "markdown-pdf-export-"));

  try {
    const generated = [];
    for (let index = 0; index < config.documents.length; index += 1) {
      generated.push(
        await convertDocument(
          config.documents[index],
          config.defaults,
          resolvedWorkDir,
          resolvedStyleRoot,
          resolvedPandocPath,
          resolvedBrowserPath,
          tempRoot,
          index,
        ),
      );
    }

    console.log(
      JSON.stringify(
        {
          workDir: resolvedWorkDir,
          configPath: resolvedConfigPath,
          generated,
        },
        null,
        2,
      ),
    );
  } finally {
    await fs.rm(tempRoot, { recursive: true, force: true });
  }
}

async function main(): Promise<void> {
  if (process.argv.includes("--self-check")) {
    const tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "markdown-pdf-export-self-check-"));
    try {
      const styleRoot = path.join(tempRoot, "styles");
      await fs.mkdir(styleRoot, { recursive: true });
      await fs.writeFile(path.join(styleRoot, "default.css"), "body { color: black; }\n", "utf8");

      const resolved = await resolveStylePath(styleRoot, tempRoot, "default", "");
      assert.equal(path.basename(resolved), "default.css");
      assert.throws(() => validateConfig({ documents: [] }), /at least one document entry/);
      assert.equal(resolveMaybeAbsolute("file.md", tempRoot), path.join(tempRoot, "file.md"));
      console.log("markdown-pdf-export self-check ok");
    } finally {
      await fs.rm(tempRoot, { recursive: true, force: true });
    }

    return;
  }

  await run();
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message);
  process.exitCode = 1;
});
