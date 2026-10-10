"use client";

import Link from "next/link";
import { ArrowLeft, Info, Shield, FileText } from "lucide-react";
import { useRouter } from "next/navigation";

export default function AboutPage() {
  const router = useRouter();
  return (
    <div className="min-h-screen bg-transparent text-neutral-900 dark:text-neutral-50 p-6 md:p-12 font-sans selection:bg-indigo-500/30">
      <div className="max-w-4xl mx-auto space-y-12">
        {/* Header */}
        <div className="mb-12">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center gap-2 text-sm font-medium text-neutral-500 hover:text-indigo-600 dark:hover:text-indigo-400 mb-8 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Leaderboard
          </button>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 to-purple-500">
            Information & Policies
          </h1>
        </div>

        {/* About Section */}
        <section id="about" className="scroll-mt-24 bg-white dark:bg-neutral-900 rounded-3xl p-8 md:p-10 border border-neutral-200 dark:border-neutral-800 shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <Info className="w-8 h-8 text-indigo-500" />
            <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">About CGPA Monitor</h2>
          </div>
          <div className="space-y-4 text-neutral-600 dark:text-neutral-300 leading-relaxed">
            <p>
              CGPA Monitor puts all semesters of a student in one place. BPUT&apos;s official result site keeps showing a failed subject as a &quot;back&quot; even after it is cleared in a later re-exam, and it does not update the SGPA.
            </p>
            <p>
              This website merges cleared back papers into the original semester, shows the updated SGPA/CGPA (credit-weighted, same formula as BPUT) and ranks the students of Trident Academy of Technology, 2028 batch.
            </p>
            <p className="pt-4 border-t border-neutral-100 dark:border-neutral-800">
              It is a student project made by <strong>Pratyay Hazra</strong>.{' '}
              <a
                href="https://www.linkedin.com/in/pratyay-hazra"
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 dark:text-indigo-400 hover:underline font-medium"
              >
                Connect on LinkedIn
              </a>
            </p>
          </div>
        </section>

        {/* Terms & Conditions Section */}
        <section id="terms" className="scroll-mt-24 bg-white dark:bg-neutral-900 rounded-3xl p-8 md:p-10 border border-neutral-200 dark:border-neutral-800 shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <FileText className="w-8 h-8 text-amber-500" />
            <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">Terms & Conditions</h2>
          </div>
          <div className="space-y-4 text-neutral-600 dark:text-neutral-300 leading-relaxed">
            <p>
              All results are taken from the public BPUT result website. This is not an official website and has no connection with BPUT or the college.
            </p>
            <p className="font-semibold text-neutral-800 dark:text-neutral-200">
              Nothing here is official.
            </p>
            <p>
              Updated SGPA/CGPA are unofficial calculations and may have mistakes. Always check the official BPUT result and marksheet for anything important.
            </p>
          </div>
        </section>

        {/* Privacy Policy Section */}
        <section id="privacy" className="scroll-mt-24 bg-white dark:bg-neutral-900 rounded-3xl p-8 md:p-10 border border-neutral-200 dark:border-neutral-800 shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <Shield className="w-8 h-8 text-emerald-500" />
            <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">Privacy Policy</h2>
          </div>
          <div className="space-y-4 text-neutral-600 dark:text-neutral-300 leading-relaxed">
            <p>
              The BPUT result portal has no login or lock, so anyone can already view anyone&apos;s result with a registration number. This website only shows that same public data.
            </p>
            <p>
              Anyone who wants their name and result removed can send a request by DM on Instagram:{' '}
              <a
                href="https://www.instagram.com/hazra_anecdotes/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 dark:text-indigo-400 hover:underline font-medium"
              >
                @hazra_anecdotes
              </a>
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
