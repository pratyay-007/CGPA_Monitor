"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, GraduationCap, BookOpen, AlertTriangle,
  CheckCircle, XCircle, Award, TrendingUp, Info
} from "lucide-react";

interface SubjectDetail {
  subject_code: string;
  subject_name: string;
  subject_type: string;
  credits: number;
  best_grade: string;
  best_grade_points: number;
  credit_index: number;
  from_session: string;
  is_backpaper: boolean;
  grade?: string;
  grade_points?: number;
}

interface SemesterDetail {
  semester: number;
  sgpa: number;
  original_sgpa: number;
  sgpa_bput: string;
  credits: number;
  credit_index: number;
  subjects: SubjectDetail[];
}

interface BackPaperAttempt {
  session: string;
  grade: string;
  grade_points: number;
  is_pass: boolean;
}

interface BackPaper {
  subject_code: string;
  subject_name: string;
  original_semester: number;
  attempts: BackPaperAttempt[];
}

interface StudentData {
  registration_number: string;
  name: string;
  branch: string;
  college: string;
  photo_url: string;
  cgpa: number;
  original_cgpa: number;
  total_credits: number;
  overall_rank: number | null;
  total_students: number;
  class_rank: number | null;
  class_total: number;
  semesters: SemesterDetail[];
  back_papers: BackPaper[];
  source: string;
  disclaimer: string;
}

function getGradeColor(grade: string): string {
  let g = grade?.toUpperCase()?.trim() || "";
  if (g.includes("(")) g = g.split("(")[0].trim();
  if (g === "O") return "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30";
  if (g === "E") return "text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30";
  if (g === "A") return "text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30";
  if (g === "B") return "text-sky-600 dark:text-sky-400 bg-sky-50 dark:bg-sky-900/30";
  if (g === "C") return "text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/30";
  if (g === "D") return "text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/30";
  if (g === "F" || g === "M" || g === "S") return "text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30";
  return "text-neutral-500 bg-neutral-100 dark:bg-neutral-800";
}

function getSgpaColor(sgpa: number): string {
  if (sgpa >= 9) return "text-emerald-600 dark:text-emerald-400";
  if (sgpa >= 8) return "text-green-600 dark:text-green-400";
  if (sgpa >= 7) return "text-blue-600 dark:text-blue-400";
  if (sgpa >= 6) return "text-yellow-600 dark:text-yellow-400";
  if (sgpa >= 5) return "text-orange-600 dark:text-orange-400";
  return "text-red-600 dark:text-red-400";
}

function getSessionLabel(session: string): string {
  if (session.includes("Odd-(2024-25)")) return "Sem 1";
  if (session.includes("Even-(2024-25)")) return "Sem 2";
  if (session.includes("Odd-(2025-26)")) return "Sem 3";
  if (session.includes("Even-(2025-26)")) return "Sem 4";
  return session;
}

export default function StudentClient({ regNo }: { regNo: string }) {
  const router = useRouter();
  const [student, setStudent] = useState<StudentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSem, setExpandedSem] = useState<number | null>(null);

  useEffect(() => {
    if (!regNo) return;
    setLoading(true);
    fetch(`/data/students/${regNo}.json`)
      .then(res => {
        if (!res.ok) throw new Error("Student not found");
        return res.json();
      })
      .then(data => {
        setStudent(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [regNo]);

  if (loading) {
    return (
      <div className="min-h-screen bg-transparent flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-neutral-400">Loading student data...</p>
        </div>
      </div>
    );
  }

  if (error || !student) {
    return (
      <div className="min-h-screen bg-transparent flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">Student Not Found</h2>
          <p className="text-neutral-500 mb-6">{error || "No data available for this registration number."}</p>
          <Link href="/leaderboard" className="text-indigo-500 hover:text-indigo-600 font-medium">
            ← Back to Leaderboard
          </Link>
        </div>
      </div>
    );
  }

  const hasBackPaperImprovement = student.cgpa !== student.original_cgpa;

  return (
    <div className="min-h-screen bg-transparent text-neutral-900 dark:text-neutral-50 font-sans selection:bg-indigo-500/30">
      <div className="max-w-5xl mx-auto p-6 md:p-12">

        {/* Back Button */}
        <button
          onClick={() => router.back()}
          className="inline-flex items-center gap-2 text-sm text-neutral-500 hover:text-indigo-500 transition-colors mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Leaderboard
        </button>

        {/* Student Header Card */}
        <div className="bg-white dark:bg-neutral-900 rounded-2xl border border-neutral-200 dark:border-neutral-800 shadow-sm p-4 mb-6">
          <div className="flex items-start gap-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-indigo-500/20">
              <GraduationCap className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="text-xl font-extrabold tracking-tight text-neutral-900 dark:text-neutral-100 leading-tight truncate">
                {student.name}
              </h1>
              <div className="text-xs text-neutral-500 mt-0.5 font-mono truncate">
                {student.registration_number} · {student.branch}
              </div>
              <div className="text-xs text-neutral-400 mt-0.5 truncate">
                {student.college}
              </div>
            </div>
          </div>

          {/* Compact stat chips */}
          <div className="flex flex-wrap gap-2 mt-3">
            <div className="bg-indigo-50 dark:bg-indigo-950/30 rounded-lg px-3 py-1.5 border border-indigo-100 dark:border-indigo-900/50">
              <div className="text-[10px] text-indigo-600 dark:text-indigo-400 font-medium uppercase tracking-wider">CGPA</div>
              <div className="text-lg font-extrabold text-indigo-600 dark:text-indigo-400 font-mono leading-none">
                {student.cgpa.toFixed(2)}
              </div>
            </div>
            {student.overall_rank && student.total_students && (
              <div className="bg-amber-50 dark:bg-amber-950/30 rounded-lg px-3 py-1.5 border border-amber-100 dark:border-amber-900/50">
                <div className="text-[10px] text-amber-600 dark:text-amber-400 font-medium uppercase tracking-wider">Overall</div>
                <div className="text-base font-extrabold text-amber-600 dark:text-amber-400 font-mono leading-none">
                  #{student.overall_rank}/{student.total_students}
                </div>
              </div>
            )}
            {student.class_rank && student.class_total && (
              <div className="bg-blue-50 dark:bg-blue-950/30 rounded-lg px-3 py-1.5 border border-blue-100 dark:border-blue-900/50">
                <div className="text-[10px] text-blue-600 dark:text-blue-400 font-medium uppercase tracking-wider">Class</div>
                <div className="text-base font-extrabold text-blue-600 dark:text-blue-400 font-mono leading-none">
                  #{student.class_rank}/{student.class_total}
                </div>
              </div>
            )}
            {hasBackPaperImprovement && (
              <div className="bg-green-50 dark:bg-green-950/30 rounded-lg px-3 py-1.5 border border-green-100 dark:border-green-900/50">
                <div className="text-[10px] text-green-600 dark:text-green-400 font-medium uppercase tracking-wider flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" /> Improved
                </div>
                <div className="text-xs text-green-700 dark:text-green-300 leading-none">
                  <span className="line-through text-neutral-400">{student.original_cgpa.toFixed(2)}</span> → {student.cgpa.toFixed(2)}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Semester Cards */}
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-indigo-500" />
          Semester Results
        </h2>

        <div className="space-y-4 mb-8">
          {student.semesters.map(sem => {
            const isExpanded = expandedSem === sem.semester;
            const failedSubjects = sem.subjects.filter(s => {
              let g = (s.best_grade || s.grade || "").toUpperCase();
              if (g.includes("(")) g = g.split("(")[0].trim();
              return g === "F" || g === "M" || g === "S";
            });
            const backPaperSubjects = sem.subjects.filter(s => {
              if (!s.is_backpaper) return false;
              let g = (s.best_grade || s.grade || "").toUpperCase();
              if (g.includes("(")) g = g.split("(")[0].trim();
              return g !== "F" && g !== "M" && g !== "S";
            });
            return (
              <div
                key={sem.semester}
                className="bg-white dark:bg-neutral-900 rounded-2xl border border-neutral-200 dark:border-neutral-800 shadow-sm overflow-hidden"
              >
                {/* Semester Header */}
                <button
                  onClick={() => setExpandedSem(isExpanded ? null : sem.semester)}
                  className="w-full text-left p-4 flex items-center justify-between hover:bg-neutral-50 dark:hover:bg-neutral-800/30 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`text-xl font-extrabold font-mono ${getSgpaColor(sem.sgpa)}`}>
                      {sem.sgpa.toFixed(2)}
                    </div>
                    <div>
                      <div className="font-semibold text-neutral-900 dark:text-neutral-100 text-sm">
                        Semester {sem.semester}
                      </div>
                      <div className="text-xs text-neutral-500 flex flex-wrap items-center gap-x-2 gap-y-1 mt-0.5">
                        <span>{sem.credits} cr</span>
                        <span>·</span>
                        <span>{sem.subjects.length} subjects</span>
                        {sem.sgpa_bput && (
                          <span className="text-neutral-400">· BPUT {sem.sgpa_bput}</span>
                        )}
                        {sem.original_sgpa !== undefined && sem.original_sgpa !== sem.sgpa && (
                          <span className="text-green-500">· Orig {sem.original_sgpa.toFixed(2)}</span>
                        )}
                        {failedSubjects.length > 0 && (
                          <span className="text-red-500 flex items-center gap-1">
                            <XCircle className="w-3 h-3" /> {failedSubjects.length} failed
                          </span>
                        )}
                        {backPaperSubjects.length > 0 && (
                          <span className="text-green-500 flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" /> {backPaperSubjects.length} cleared
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                    <svg className="w-4 h-4 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </button>

                {/* Expanded Subject rows */}
                {isExpanded && (
                  <div className="border-t border-neutral-200 dark:border-neutral-800">
                    <div className="divide-y divide-neutral-100 dark:divide-neutral-800/60">
                      {sem.subjects.map((subj, idx) => {
                        const grade = subj.best_grade || subj.grade || "?";
                        const gp = subj.best_grade_points ?? subj.grade_points ?? 0;
                        const ci = subj.credit_index ?? (subj.credits * gp);

                        let bg = grade.toUpperCase();
                        if (bg.includes("(")) bg = bg.split("(")[0].trim();
                        const isFail = bg === "F" || bg === "M" || bg === "S";

                        return (
                          <div
                            key={idx}
                            className="flex items-center gap-3 px-4 py-2.5 hover:bg-neutral-50 dark:hover:bg-neutral-800/30 transition-colors"
                          >
                            {/* Grade badge */}
                            <span className={`inline-flex items-center justify-center w-9 h-9 rounded-lg font-bold text-xs flex-shrink-0 ${getGradeColor(grade)}`}>
                              {grade}
                            </span>

                            {/* Subject info */}
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">
                                {subj.subject_name}
                              </div>
                              <div className="text-[11px] text-neutral-400 font-mono truncate">
                                {subj.subject_code}
                              </div>
                            </div>

                            {/* Compact chips */}
                            <div className="flex items-center gap-1 flex-shrink-0">
                              <span className="text-[9px] font-medium px-1 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800 text-neutral-500 hidden xs:inline-block">
                                {subj.subject_type || "—"}
                              </span>
                              <span className="text-[10px] font-mono text-neutral-500 tabular-nums">
                                {subj.credits}cr
                              </span>
                              <span className="text-[10px] font-mono text-neutral-500 tabular-nums">
                                GP{gp}
                              </span>
                              <span className="text-[10px] font-mono font-medium text-neutral-700 dark:text-neutral-300 tabular-nums">
                                CI{ci.toFixed(1)}
                              </span>
                            </div>

                            {/* Status */}
                            <div className="flex-shrink-0">
                              {isFail ? (
                                <span className="inline-flex items-center gap-1 text-[10px] font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 px-1.5 py-0.5 rounded">
                                  <XCircle className="w-3 h-3" />
                                  {subj.is_backpaper ? `BP ${getSessionLabel(subj.from_session)}` : "Fail"}
                                </span>
                              ) : subj.is_backpaper ? (
                                <span className="inline-flex items-center gap-1 text-[10px] font-medium text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30 px-1.5 py-0.5 rounded">
                                  <Award className="w-3 h-3" />
                                  BP {getSessionLabel(subj.from_session)}
                                </span>
                              ) : (
                                <CheckCircle className="w-4 h-4 text-emerald-500" />
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Subject Footer */}
                    <div className="bg-neutral-50 dark:bg-neutral-950/30 px-4 py-3 border-t border-neutral-200 dark:border-neutral-800">
                      <div className="flex justify-between items-center">
                        <div className={`text-base font-bold ${getSgpaColor(sem.sgpa)}`}>
                          Updated SGPA: {sem.sgpa.toFixed(2)}
                        </div>
                        {sem.original_sgpa !== undefined && (
                          <div className="text-sm text-neutral-500">
                            Official SGPA (BPUT): {sem.sgpa_bput || sem.original_sgpa.toFixed(2)}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Back Papers Section */}
        {student.back_papers.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              Back Paper History
            </h2>
            <div className="bg-white dark:bg-neutral-900 rounded-2xl border border-neutral-200 dark:border-neutral-800 shadow-sm">
              <div className="space-y-4 p-4">
                {student.back_papers.map((bp, idx) => (
                  <div
                    key={idx}
                    className="border border-neutral-200 dark:border-neutral-800 rounded-lg p-4 hover:bg-neutral-50 dark:hover:bg-neutral-800/40 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="font-medium text-neutral-900 dark:text-neutral-100">{bp.subject_name}</div>
                        <div className="text-xs text-neutral-400 font-mono mt-1">{bp.subject_code}</div>
                      </div>
                      <div className="text-center text-sm font-medium bg-amber-100 dark:bg-amber-900/20 rounded px-3 py-1">
                        Sem {bp.original_semester}
                      </div>
                    </div>
                    <div className="space-y-2">
                      {bp.attempts.map((attempt, i) => (
                        <div
                          key={i}
                          className={`inline-flex items-center gap-2 text-sm font-medium px-3 py-2 rounded-lg ${
                            attempt.is_pass
                              ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                              : 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                          }`}
                        >
                          <span className="font-medium">
                            {getSessionLabel(attempt.session)}: {attempt.grade} ({attempt.grade_points} GP)
                          </span>
                          {attempt.is_pass ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Disclaimer */}
        <div className="bg-amber-50 dark:bg-amber-950/20 rounded-2xl p-5 border border-amber-100 dark:border-amber-900/50 flex gap-3">
          <Info className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed">
            <p className="font-medium mb-1">Disclaimer</p>
            <p>{student.disclaimer}</p>
            <p className="mt-1">Source: {student.source}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
