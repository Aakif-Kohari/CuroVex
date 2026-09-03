import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Providers from "./providers";
import Link from "next/link";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CuroVex - Explainable AI for Drug Repurposing",
  description:
    "Explainable AI framework for drug repurposing with path-based and counterfactual reasoning.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.className} min-h-screen bg-navy-900 text-slate-100 flex flex-col`}
      >
        <Providers>
          <header className="border-b border-navy-700 bg-navy-800/50 backdrop-blur-md sticky top-0 z-50">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
              <Link href="/" className="flex items-center space-x-2 group">
                <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500 flex items-center justify-center group-hover:bg-teal-500/20 transition-colors">
                  <span className="text-teal-400 font-bold">C</span>
                </div>
                <div>
                  <h1 className="font-semibold text-lg leading-tight group-hover:text-teal-400 transition-colors">
                    CuroVex
                  </h1>
                  <p className="text-[10px] text-slate-400 font-medium uppercase tracking-wider hidden sm:block">
                    Explainable AI for Drug Repurposing
                  </p>
                </div>
              </Link>
              <nav className="flex items-center space-x-4">
                <Link
                  href="/search"
                  className="text-sm text-slate-300 hover:text-white transition-colors"
                >
                  Search
                </Link>
                <Link
                  href="/"
                  className="text-sm text-slate-300 hover:text-white transition-colors"
                >
                  About
                </Link>
              </nav>
            </div>
          </header>
          <main className="flex-1">{children}</main>
          <footer className="border-t border-navy-800 bg-navy-900 py-6 mt-12">
            <div className="container mx-auto px-4 text-center text-sm text-slate-500">
              &copy; {new Date().getFullYear()} CuroVex Framework.
            </div>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
