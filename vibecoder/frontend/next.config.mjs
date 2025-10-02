const resolvePreviewHost = () => {
  const explicit =
    process.env.NEXT_PUBLIC_PREVIEW_HOST ||
    process.env.PREVIEW_BASE_HOST ||
    "";

  const candidate = explicit.trim()
    ? explicit
    : process.env.NODE_ENV === "development"
      ? "localhost"
      : "preview.vibe.llmlab.io";

  return candidate
    .replace(/^https?:\/\//, "")
    .replace(/:\d+$/, "")
    .replace(/\/$/, "");
};

const previewHost = resolvePreviewHost();
const backendPreviewBase =
  process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://backend:8000";

const normalizedBackendBase = backendPreviewBase.replace(/\/$/, "");
const shouldProxyPreviews =
  previewHost && previewHost !== "localhost" && previewHost !== "127.0.0.1";
const escapedPreviewHost = shouldProxyPreviews ? previewHost.replace(/\./g, "\\.") : "";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    appDir: true,
  },
  async rewrites() {
    if (!shouldProxyPreviews) {
      return [];
    }
    return [
      {
        source: "/:path*",
        has: [
          {
            type: "host",
            value: `^(?<revision>[^.]+)\\.${escapedPreviewHost}(?::\\d+)?$`,
          },
        ],
        destination: `${normalizedBackendBase}/previews/:revision/:path*`,
      },
    ];
  },
};

export default nextConfig;
