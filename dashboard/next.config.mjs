/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone', // Required by your Dockerfile for production builds
  reactStrictMode: true,
};

export default nextConfig;