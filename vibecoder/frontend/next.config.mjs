const previewHost = process.env.NEXT_PUBLIC_PREVIEW_HOST || "preview.localtest.me";
const backendPreviewBase =
  process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://backend:8000";

const normalizedBackendBase = backendPreviewBase.replace(/\/$/, "");
const escapedPreviewHost = previewHost.replace(/\./g, "\\.");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    appDir: true,
  },
  async rewrites() {
    return [
      {
        source: "/:path*",
        has: [
          {
            type: "host",
            value: `(?<revision>[^.]+)\\.${escapedPreviewHost}`,
          },
        ],
        destination: `${normalizedBackendBase}/previews/:revision/:path*`,
      },
    ];
  },
};

export default nextConfig;
