export const frontendPorts = {
  landing: 3000,
  auth: 3001,
  platform: 3002,
  docs: 3003,
} as const;

export const frontendUrls = {
  landing: "http://127.0.0.1:3000",
  auth: "http://127.0.0.1:3001",
  platform: "http://127.0.0.1:3002",
  docs: "http://127.0.0.1:3003",
} as const;

export const apiBaseUrl = "http://127.0.0.1:8000";

export const privacyNoticeVersion = "privacy-2026-09-v1";
