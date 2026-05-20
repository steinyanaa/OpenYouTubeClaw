import test from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

test("manifest icon assets exist", () => {
  const root = process.cwd();
  const manifest = JSON.parse(readFileSync(join(root, "manifest.json"), "utf8")) as {
    icons?: Record<string, string>;
    action?: {
      default_icon?: Record<string, string>;
      default_popup?: string;
    };
    permissions?: string[];
    side_panel?: { default_path?: string };
  };

  const iconPaths = new Set<string>([
    ...Object.values(manifest.icons ?? {}),
    ...Object.values(manifest.action?.default_icon ?? {}),
  ]);

  assert.ok(iconPaths.size > 0);
  for (const relativePath of iconPaths) {
    assert.equal(
      existsSync(join(root, relativePath)),
      true,
      `missing icon asset: ${relativePath}`,
    );
  }
});

test("manifest uses side panel instead of popup", () => {
  const root = process.cwd();
  const manifest = JSON.parse(readFileSync(join(root, "manifest.json"), "utf8")) as {
    action?: { default_popup?: string };
    permissions?: string[];
    side_panel?: { default_path?: string };
  };

  assert.equal(manifest.permissions?.includes("sidePanel"), true);
  assert.equal(manifest.side_panel?.default_path, "popup/popup.html");
  assert.equal("default_popup" in (manifest.action ?? {}), false);
});

test("extension package version files stay aligned", () => {
  const root = process.cwd();
  const manifest = JSON.parse(readFileSync(join(root, "manifest.json"), "utf8")) as {
    version?: string;
  };
  const packageJson = JSON.parse(readFileSync(join(root, "package.json"), "utf8")) as {
    version?: string;
  };
  const packageLock = JSON.parse(readFileSync(join(root, "package-lock.json"), "utf8")) as {
    version?: string;
    packages?: Record<string, { version?: string }>;
  };

  assert.equal(packageJson.version, manifest.version);
  assert.equal(packageLock.version, manifest.version);
  assert.equal(packageLock.packages?.[""]?.version, manifest.version);
});

test("Firefox manifest declares required data collection categories", () => {
  const root = process.cwd();
  const manifest = JSON.parse(
    readFileSync(join(root, "manifest.firefox.json"), "utf8"),
  ) as {
    browser_specific_settings?: {
      gecko?: {
        strict_min_version?: string;
        data_collection_permissions?: {
          required?: string[];
        };
      };
      gecko_android?: {
        strict_min_version?: string;
      };
    };
  };

  assert.equal(
    manifest.browser_specific_settings?.gecko?.strict_min_version,
    "140.0",
  );
  assert.equal(
    manifest.browser_specific_settings?.gecko_android?.strict_min_version,
    "142.0",
  );
  assert.deepEqual(
    manifest.browser_specific_settings?.gecko?.data_collection_permissions?.required,
    [
      "authenticationInfo",
      "browsingActivity",
      "personalCommunications",
      "searchTerms",
      "websiteActivity",
      "websiteContent",
    ],
  );
});

test("Chrome and Firefox manifests are YouTube-only plus local backend", () => {
  const root = process.cwd();
  const chromeManifest = JSON.parse(readFileSync(join(root, "manifest.json"), "utf8")) as {
    host_permissions?: string[];
    content_scripts?: Array<{ matches?: string[] }>;
  };
  const firefoxManifest = JSON.parse(
    readFileSync(join(root, "manifest.firefox.json"), "utf8"),
  ) as {
    host_permissions?: string[];
    content_scripts?: Array<{ matches?: string[] }>;
  };

  const expected = ["*://*.youtube.com/*", "http://127.0.0.1/*", "http://localhost/*"];
  assert.deepEqual(chromeManifest.host_permissions, expected);
  assert.deepEqual(firefoxManifest.host_permissions, expected);
  assert.deepEqual(chromeManifest.content_scripts?.flatMap((s) => s.matches ?? []), ["*://*.youtube.com/*"]);
  assert.equal(chromeManifest.host_permissions?.some((p) => p.includes("bilibili.com")), false);
  assert.equal(chromeManifest.host_permissions?.some((p) => p.includes("douyin.com")), false);
  assert.equal(chromeManifest.host_permissions?.some((p) => p.includes("xiaohongshu.com")), false);
});
