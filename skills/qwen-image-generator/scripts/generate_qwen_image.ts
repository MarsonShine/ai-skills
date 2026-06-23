const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const path = require("node:path");

type Payload = {
  prompt: string;
  model?: string;
  size?: string;
  outputPath?: string;
  promptExtend?: boolean;
  watermark?: boolean;
  count?: number;
  timeoutSeconds?: number;
  pollIntervalSeconds?: number;
};

const DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/api/v1";
const SUCCESS_STATES = new Set(["SUCCEEDED", "SUCCESS", "COMPLETED"]);
const FAILURE_STATES = new Set(["FAILED", "FAILURE", "ERROR", "CANCELED", "CANCELLED"]);

// ponytail: keep one file until the API flow actually splits in practice.

function parsePayload(): Payload {
  const payloadArg = process.argv.slice(2).find((arg: string) => arg.startsWith("--payload-base64="));
  if (!payloadArg) {
    throw new Error("Missing --payload-base64.");
  }

  const encoded = payloadArg.slice("--payload-base64=".length);
  if (!encoded) {
    throw new Error("Empty --payload-base64 value.");
  }

  return JSON.parse(Buffer.from(encoded, "base64").toString("utf8"));
}

function getApiKey(): string {
  const apiKey = process.env.QWEN_IMAGE_API_KEY || process.env.DASHSCOPE_API_KEY;
  if (!apiKey || !apiKey.trim()) {
    throw new Error("Set QWEN_IMAGE_API_KEY or DASHSCOPE_API_KEY before running this script.");
  }

  return apiKey.trim();
}

function getBaseUrl(): string {
  const override = process.env.DASHSCOPE_BASE_URL;
  return (override && override.trim() ? override : DEFAULT_BASE_URL).replace(/\/+$/, "");
}

function normalizeSize(size: string): string {
  return /^\d+x\d+$/i.test(size) ? size.replace("x", "*") : size;
}

function newSlug(value: string): string {
  const slug = value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  if (!slug) {
    return "image";
  }

  return slug.length > 48 ? slug.slice(0, 48).replace(/-+$/g, "") || "image" : slug;
}

function getNestedValue(root: unknown, keys: string[]): unknown {
  let current = root as Record<string, unknown> | undefined;
  for (const key of keys) {
    if (!current || typeof current !== "object" || !(key in current)) {
      return undefined;
    }

    current = current[key] as Record<string, unknown>;
  }

  return current;
}

function getTaskId(response: unknown): string | null {
  const candidates = [
    getNestedValue(response, ["task_id"]),
    getNestedValue(response, ["taskId"]),
    getNestedValue(response, ["output", "task_id"]),
    getNestedValue(response, ["output", "taskId"]),
    getNestedValue(response, ["output", "id"]),
  ];

  for (const value of candidates) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  return null;
}

function getStatusValue(response: unknown): string | null {
  const candidates = [
    getNestedValue(response, ["status"]),
    getNestedValue(response, ["task_status"]),
    getNestedValue(response, ["output", "status"]),
    getNestedValue(response, ["output", "task_status"]),
  ];

  for (const value of candidates) {
    if (typeof value === "string" && value.trim()) {
      return value.trim().toUpperCase();
    }
  }

  return null;
}

function getImageUrls(response: unknown): string[] {
  const urls = new Set<string>();
  const output = getNestedValue(response, ["output"]) as Record<string, unknown> | undefined;
  const results = Array.isArray(output?.results) ? output.results : [];

  for (const item of results) {
    if (!item || typeof item !== "object") {
      continue;
    }

    const maybeUrl = (item as Record<string, unknown>).url;
    const maybeImageUrl = (item as Record<string, unknown>).image_url;
    if (typeof maybeUrl === "string" && maybeUrl.trim()) {
      urls.add(maybeUrl.trim());
      continue;
    }

    if (typeof maybeImageUrl === "string" && maybeImageUrl.trim()) {
      urls.add(maybeImageUrl.trim());
    }
  }

  const choices = Array.isArray(output?.choices) ? output.choices : [];
  for (const choice of choices) {
    if (!choice || typeof choice !== "object") {
      continue;
    }

    const message = (choice as Record<string, unknown>).message as Record<string, unknown> | undefined;
    const content = Array.isArray(message?.content) ? message.content : [];
    for (const contentItem of content) {
      if (!contentItem || typeof contentItem !== "object") {
        continue;
      }

      const image = (contentItem as Record<string, unknown>).image;
      if (typeof image === "string" && image.trim()) {
        urls.add(image.trim());
      }
    }
  }

  return Array.from(urls);
}

function extractErrorMessage(response: unknown): string {
  const candidates = [
    getNestedValue(response, ["message"]),
    getNestedValue(response, ["error", "message"]),
    getNestedValue(response, ["output", "message"]),
    getNestedValue(response, ["code"]),
  ];

  for (const candidate of candidates) {
    if (typeof candidate === "string" && candidate.trim()) {
      return candidate.trim();
    }
  }

  return safeStringify(response);
}

function safeStringify(value: unknown): string {
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

async function fetchJson(url: string, init: RequestInit): Promise<unknown> {
  const response = await fetch(url, init);
  const text = await response.text();
  let body: unknown = {};

  if (text.trim()) {
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
  }

  if (!response.ok) {
    throw new Error(`DashScope request failed (${response.status}): ${extractErrorMessage(body)}`);
  }

  return body;
}

async function sleep(milliseconds: number): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function pollTask(
  baseUrl: string,
  taskId: string,
  headers: Record<string, string>,
  timeoutSeconds: number,
  pollIntervalSeconds: number,
): Promise<unknown> {
  const deadline = Date.now() + timeoutSeconds * 1000;
  let lastResponse: unknown = null;

  while (Date.now() <= deadline) {
    const response = await fetchJson(`${baseUrl}/tasks/${encodeURIComponent(taskId)}`, { headers });
    lastResponse = response;

    const imageUrls = getImageUrls(response);
    if (imageUrls.length > 0) {
      return response;
    }

    const status = getStatusValue(response);
    if (status && SUCCESS_STATES.has(status)) {
      return response;
    }

    if (status && FAILURE_STATES.has(status)) {
      throw new Error(`DashScope task ${taskId} failed: ${extractErrorMessage(response)}`);
    }

    await sleep(pollIntervalSeconds * 1000);
  }

  throw new Error(`Timed out waiting for DashScope task ${taskId}. Last payload=${safeStringify(lastResponse)}`);
}

function resolveOutputTargets(baseOutputPath: string, imageCount: number, promptText: string): string[] {
  const timestamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\..+/, "").replace("T", "-");
  const slug = newSlug(promptText);

  if (!baseOutputPath) {
    const directory = path.join(process.cwd(), "generated-images");
    if (imageCount === 1) {
      return [path.join(directory, `${slug}-${timestamp}.png`)];
    }

    return Array.from({ length: imageCount }, (_: unknown, index: number) =>
      path.join(directory, `${slug}-${timestamp}-${String(index + 1).padStart(2, "0")}.png`),
    );
  }

  const resolvedPath = path.resolve(baseOutputPath);
  const extension = path.extname(resolvedPath);
  if (imageCount === 1 && extension) {
    return [resolvedPath];
  }

  const baseDirectory = extension ? path.dirname(resolvedPath) : resolvedPath;
  const baseName = extension ? path.basename(resolvedPath, extension) : `${slug}-${timestamp}`;

  return Array.from({ length: imageCount }, (_: unknown, index: number) => {
    const suffix = imageCount === 1 ? "" : `-${String(index + 1).padStart(2, "0")}`;
    return path.join(baseDirectory || process.cwd(), `${baseName}${suffix}.png`);
  });
}

async function downloadFile(url: string, targetPath: string): Promise<void> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to download generated image (${response.status}): ${url}`);
  }

  const buffer = Buffer.from(await response.arrayBuffer());
  await fs.mkdir(path.dirname(targetPath), { recursive: true });
  await fs.writeFile(targetPath, buffer);
}

function normalizePayload(input: Payload): Required<Payload> {
  const prompt = typeof input.prompt === "string" ? input.prompt.trim() : "";
  if (!prompt) {
    throw new Error("Prompt is required.");
  }

  const count = Number.isInteger(input.count) ? Number(input.count) : 1;
  const timeoutSeconds = Number.isInteger(input.timeoutSeconds) ? Number(input.timeoutSeconds) : 180;
  const pollIntervalSeconds = Number.isInteger(input.pollIntervalSeconds) ? Number(input.pollIntervalSeconds) : 2;

  if (count < 1 || count > 4) {
    throw new Error("Count must be between 1 and 4.");
  }

  if (timeoutSeconds < 10 || timeoutSeconds > 600) {
    throw new Error("TimeoutSeconds must be between 10 and 600.");
  }

  if (pollIntervalSeconds < 1 || pollIntervalSeconds > 10) {
    throw new Error("PollIntervalSeconds must be between 1 and 10.");
  }

  return {
    prompt,
    model: typeof input.model === "string" && input.model.trim() ? input.model.trim() : "qwen-image-2.0",
    size: typeof input.size === "string" && input.size.trim() ? input.size.trim() : "1024x1024",
    outputPath: typeof input.outputPath === "string" ? input.outputPath.trim() : "",
    promptExtend: input.promptExtend ?? true,
    watermark: input.watermark ?? false,
    count,
    timeoutSeconds,
    pollIntervalSeconds,
  };
}

async function run(): Promise<void> {
  const payload = normalizePayload(parsePayload());
  const apiKey = getApiKey();
  const baseUrl = getBaseUrl();
  const normalizedSize = normalizeSize(payload.size);
  const headers = {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  };

  const requestBody = {
    model: payload.model,
    input: {
      messages: [
        {
          role: "user",
          content: [{ text: payload.prompt }],
        },
      ],
    },
    parameters: {
      size: normalizedSize,
      prompt_extend: payload.promptExtend,
      watermark: payload.watermark,
      n: payload.count,
    },
  };

  let finalResponse = await fetchJson(`${baseUrl}/services/aigc/multimodal-generation/generation`, {
    method: "POST",
    headers,
    body: JSON.stringify(requestBody),
  });

  const taskId = getTaskId(finalResponse);
  let imageUrls = getImageUrls(finalResponse);
  if (imageUrls.length === 0 && taskId) {
    finalResponse = await pollTask(baseUrl, taskId, headers, payload.timeoutSeconds, payload.pollIntervalSeconds);
    imageUrls = getImageUrls(finalResponse);
  }

  if (imageUrls.length === 0) {
    throw new Error(`DashScope did not return an image URL. Payload=${safeStringify(finalResponse)}`);
  }

  const targets = resolveOutputTargets(payload.outputPath, imageUrls.length, payload.prompt);
  const savedFiles: string[] = [];

  for (let index = 0; index < imageUrls.length; index += 1) {
    const target = path.resolve(targets[index]);
    await downloadFile(imageUrls[index], target);
    savedFiles.push(target);
  }

  console.log(
    JSON.stringify(
      {
        model: payload.model,
        size: normalizedSize,
        taskId,
        imageUrls,
        savedFiles,
      },
      null,
      2,
    ),
  );
}

async function main(): Promise<void> {
  if (process.argv.includes("--self-check")) {
    const sample = {
      output: {
        results: [{ url: "https://example.com/a.png" }],
      },
    };
    assert.deepEqual(getImageUrls(sample), ["https://example.com/a.png"]);
    assert.equal(getTaskId({ output: { task_id: "task-1" } }), "task-1");
    assert.equal(getStatusValue({ status: "succeeded" }), "SUCCEEDED");
    assert.equal(newSlug("A/B test"), "a-b-test");
    assert.equal(resolveOutputTargets("out", 2, "Apple").length, 2);
    console.log("qwen-image-generator self-check ok");
    return;
  }

  await run();
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message);
  process.exitCode = 1;
});
