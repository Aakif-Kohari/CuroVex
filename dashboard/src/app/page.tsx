"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Network, Search, ShieldCheck } from "lucide-react";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-8rem)]">
      {/* Hero Section */}
      <section className="w-full py-20 px-4 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto space-y-6"
        >
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-sm font-medium mb-4">
            <span className="w-2 h-2 rounded-full bg-teal-500 mr-2 animate-pulse"></span>
            Next-Gen Drug Repurposing
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
            Explainable AI for <br className="hidden md:block" />
            <span className="text-teal-400">Drug Discovery</span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Uncover novel therapeutic targets using advanced knowledge graphs
            and counterfactual reasoning to generate high-fidelity, transparent
            predictions.
          </p>
          <div className="pt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/search"
              className="w-full sm:w-auto px-8 py-4 bg-teal-500 hover:bg-teal-400 text-navy-900 font-bold rounded-lg transition-all shadow-[0_0_20px_rgba(20,184,166,0.3)] hover:shadow-[0_0_30px_rgba(20,184,166,0.5)] transform hover:-translate-y-1"
            >
              Start Searching
            </Link>
            <Link
              href="#features"
              className="w-full sm:w-auto px-8 py-4 bg-navy-800 hover:bg-navy-700 border border-navy-700 rounded-lg font-medium transition-all"
            >
              Learn More
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section id="features" className="w-full py-20 bg-navy-900/50">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.5 }}
              viewport={{ once: true }}
              className="p-8 rounded-2xl bg-navy-800/50 border border-navy-700 hover:border-teal-500/30 transition-colors group"
            >
              <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Network className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="text-xl font-bold mb-3">Knowledge Graphs</h3>
              <p className="text-slate-400">
                Leverages massive biomedical knowledge networks to find
                non-obvious links between diseases and potential treatments.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.5 }}
              viewport={{ once: true }}
              className="p-8 rounded-2xl bg-navy-800/50 border border-navy-700 hover:border-teal-500/30 transition-colors group"
            >
              <div className="w-12 h-12 bg-teal-500/10 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Search className="w-6 h-6 text-teal-400" />
              </div>
              <h3 className="text-xl font-bold mb-3">Deep Explanations</h3>
              <p className="text-slate-400">
                Move beyond black-box AI. View clear path-based and
                counterfactual evidence supporting every prediction we make.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.5 }}
              viewport={{ once: true }}
              className="p-8 rounded-2xl bg-navy-800/50 border border-navy-700 hover:border-teal-500/30 transition-colors group"
            >
              <div className="w-12 h-12 bg-purple-500/10 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <ShieldCheck className="w-6 h-6 text-purple-400" />
              </div>
              <h3 className="text-xl font-bold mb-3">Clinical Validation</h3>
              <p className="text-slate-400">
                Cross-references predictions with actual clinical trials and
                recent biomedical literature automatically.
              </p>
            </motion.div>
          </div>
        </div>
      </section>
    </div>
  );
}
