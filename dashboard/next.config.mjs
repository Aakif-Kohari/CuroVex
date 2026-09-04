/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone', // Required by your Dockerfile for production builds
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.API_URL || 'http://localhost:8000'}/:path*`,
      },
    ];
  },
};

export default nextConfig;
