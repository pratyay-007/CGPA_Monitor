"use client";

import { useState, useEffect, useCallback, useRef, Suspense } from "react";
import { Trophy, Search, ChevronRight, GraduationCap, AlertCircle, Filter, X, User, ChevronDown } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams, usePathname } from "next/navigation";

interface Student {
  registration_number: string;
  name: string;
  branch: string;
  course: string;
  cgpa: number;
  original_cgpa: number;
  rank: number;
  sort_value: number;
  [key: string]: number | string | undefined;
}

interface Branch {
  name: string;
  count: number;
}

interface Meta {
  semesters: number[];
  branches: Branch[];
  data_fetched: string;
  total_students: number;
  generated_at: string;
}

interface LeaderboardData {
  meta: Meta;
  students: Student[];
}

// Loading quotes shown while the big JSON is being fetched
const LOADING_QUOTES = [
  "Fun fact: a CGPA is just a number. You are more than that 💜",
  "Calculating… also, drink some water 💧",
  "Loading rankings... your worth isn't in them though 🌟",
  "Crunching numbers so you don't have to 🧮",
];

function computeSortValue(student: Student, semester: string): number {
  if (!semester) return student.cgpa;
  const key = `sgpa_sem${semester}`;
  const val = student[key];
  return typeof val === "number" && val > 0 ? val : 0;
}

function LeaderboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();

  // All loaded data
  const [allStudents, setAllStudents] = useState<Student[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [quote] = useState(() => LOADING_QUOTES[Math.floor(Math.random() * LOADING_QUOTES.length)]);

  // Filters from URL or defaults
  const branch = searchParams.get("branch") || "";
  const course = searchParams.get("course") || "";
  const semester = searchParams.get("semester") || "";

  // Search
  const [searchQuery, setSearchQuery] = useState("");
  const [showSearchResults, setShowSearchResults] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  const [showFilters, setShowFilters] = useState(false);

  // Pagination
  const [page, setPage] = useState(1);
  const PER_PAGE = 25;
  const [pageInput, setPageInput] = useState("");

  // Windowed pagination
  const paginationItems = (totalPages: number, page: number): ({ type: "page"; num: number } | { type: "ellipsis" })[] => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => ({ type: "page" as const, num: i + 1 }));
    }
    const items: { type: "page"; num: number }[] = [{ type: "page", num: 1 }];
    if (page <= 4) {
      for (let n = 2; n <= 5; n++) items.push({ type: "page", num: n });
    } else if (page >= totalPages - 3) {
      for (let n = totalPages - 4; n <= totalPages - 1; n++) items.push({ type: "page", num: n });
    } else {
      items.push({ type: "page", num: page - 1 });
      items.push({ type: "page", num: page });
      items.push({ type: "page", num: page + 1 });
    }
    items.push({ type: "page", num: totalPages });
    const withEllipsis: ({ type: "page"; num: number } | { type: "ellipsis" })[] = [];
    items.forEach((item, i) => {
      if (i > 0 && item.num - items[i - 1].num > 1) {
        withEllipsis.push({ type: "ellipsis" });
      }
      withEllipsis.push(item);
    });
    return withEllipsis;
  };

  const handleGoToPage = () => {
    const pageNumber = parseInt(pageInput, 10);
    if (!isNaN(pageNumber) && pageNumber >= 1 && pageNumber <= totalPages) {
      setPage(pageNumber);
    }
    setPageInput("");
  };

  // Reset to page 1 on filter change
  useEffect(() => {
    setPage(1);
  }, [branch, course, semester]);

  // Fetch leaderboard.json ONCE
  useEffect(() => {
    fetch("/data/leaderboard.json")
      .then(res => {
        if (!res.ok) throw new Error("Failed to load leaderboard data");
        return res.json() as Promise<LeaderboardData>;
      })
      .then(data => {
        setMeta(data.meta);
        setAllStudents(data.students);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const updateFilters = (newBranch: string, newCourse: string, newSemester: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (newBranch) params.set("branch", newBranch);
    else params.delete("branch");
    if (newCourse) params.set("course", newCourse);
    else params.delete("course");
    if (newSemester) params.set("semester", newSemester);
    else params.delete("semester");
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  };

  const handleBranchChange = (newBranch: string) => {
    let newCourse = course;
    if (!newBranch) {
      newCourse = "";
    } else if (newBranch.toLowerCase().includes("bio technology") || newBranch.toLowerCase().includes("biotech")) {
      newCourse = "biotech";
    } else {
      newCourse = "btech";
    }
    updateFilters(newBranch, newCourse, semester);
  };

  // Close search dropdown on click outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSearchResults(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // --- Client-side filtering and sorting ---
  const filtered = allStudents.filter(s => {
    if (branch && s.branch !== branch) return false;
    if (course && s.course !== course) return false;
    if (semester) {
      const key = `sgpa_sem${semester}`;
      const val = s[key];
      if (typeof val !== "number" || val === 0) return false;
    }
    return true;
  });

  // Assign sort_value and re-rank within the filtered set
  const ranked = (() => {
    const withSort = filtered.map(s => ({
      ...s,
      sort_value: computeSortValue(s, semester),
    }));
    withSort.sort((a, b) => b.sort_value - a.sort_value || a.name.localeCompare(b.name));
    let prevVal: number | null = null;
    let prevRank = 0;
    return withSort.map((s, i) => {
      if (s.sort_value !== prevVal) {
        prevRank = i + 1;
        prevVal = s.sort_value;
      }
      return { ...s, rank: prevRank };
    });
  })();

  const totalPages = Math.max(1, Math.ceil(ranked.length / PER_PAGE));
  const leaderboard = ranked.slice((page - 1) * PER_PAGE, page * PER_PAGE);
  const totalCount = ranked.length;

  // Search: filter allStudents by query (min 2 chars)
  const searchResults = useCallback(() => {
    if (searchQuery.length < 2) return [];
    const q = searchQuery.toLowerCase();
    return allStudents
      .filter(s => s.name.toLowerCase().includes(q) || s.registration_number.toLowerCase().includes(q))
      .slice(0, 10)
      .map(s => ({
        registration_number: s.registration_number,
        name: s.name,
        branch: s.branch,
        cgpa: s.cgpa ?? null,
      }));
  }, [searchQuery, allStudents])();

  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
    setShowSearchResults(query.length >= 2);
  }, []);

  const branches: Branch[] = meta?.branches ?? [];
  const availableSemesters: number[] = meta?.semesters ?? [];

  return (
    <div className="min-h-screen bg-transparent text-neutral-900 dark:text-neutral-50 p-6 md:p-12 font-sans selection:bg-indigo-500/30">

      {/* Header */}
      <div className="max-w-6xl mx-auto flex flex-col items-center text-center gap-3 mb-6">
        <Link href="/" className="inline-flex items-center gap-2.5">
          <Trophy className="text-indigo-500 w-7 h-7" />
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 to-purple-500">
            CGPA Monitor
          </h1>
        </Link>
        <p className="text-neutral-500 dark:text-neutral-400 text-sm md:text-base max-w-xl">
          Trident Academy of Technology 2028 batch rankings. Track your SGPA/CGPA with back-paper handling.
        </p>

        {/* Search Bar */}
        <div className="w-full md:w-80 relative group" ref={searchRef}>
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none z-10">
            <Search className="h-5 w-5 text-neutral-400 group-focus-within:text-indigo-500 transition-colors" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            onFocus={() => searchQuery.length >= 2 && setShowSearchResults(true)}
            className="block w-full pl-10 pr-10 py-2.5 md:py-3 border border-neutral-200 dark:border-neutral-800 rounded-2xl leading-5 bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all shadow-sm text-sm md:text-base"
            placeholder="Search by name or reg no..."
          />
          {searchQuery && (
            <button
              onClick={() => { setSearchQuery(""); setShowSearchResults(false); }}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              <X className="h-4 w-4 text-neutral-400 hover:text-neutral-600" />
            </button>
          )}

          {/* Search Dropdown */}
          {showSearchResults && (
            <div className="absolute z-50 mt-2 w-full bg-white dark:bg-neutral-900 rounded-2xl shadow-xl border border-neutral-200 dark:border-neutral-800 overflow-hidden max-h-96 overflow-y-auto">
              {searchResults.length === 0 ? (
                <div className="p-6 text-center text-neutral-400 text-sm">
                  No students found for &quot;{searchQuery}&quot;
                </div>
              ) : (
                searchResults.map(s => (
                  <Link
                    key={s.registration_number}
                    href={`/student/${s.registration_number}`}
                    className="flex items-center gap-3 md:gap-4 px-4 md:px-5 py-3 md:py-4 hover:bg-neutral-50 dark:hover:bg-neutral-800/50 transition-colors border-b border-neutral-100 dark:border-neutral-800/50 last:border-b-0"
                    onClick={() => setShowSearchResults(false)}
                  >
                    <div className="w-9 h-9 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4 text-indigo-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm text-neutral-900 dark:text-neutral-100 break-words">
                        {s.name}
                      </div>
                      <div className="text-xs text-neutral-500 font-mono">
                        {s.registration_number} · {s.branch}
                      </div>
                    </div>
                    {s.cgpa !== null && (
                      <div className="text-sm font-bold text-indigo-600 dark:text-indigo-400 font-mono">
                        {s.cgpa.toFixed(2)}
                      </div>
                    )}
                    <ChevronRight className="w-4 h-4 text-neutral-300 flex-shrink-0" />
                  </Link>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto flex flex-col lg:flex-row gap-8">

        {/* Filters sidebar */}
        <div className="w-full lg:w-72 flex-shrink-0">
          <div className="lg:sticky lg:top-6">
            {/* Mobile pill toggle */}
            <div className="lg:hidden mb-4">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="w-full inline-flex items-center justify-between gap-2 px-4 py-2.5 rounded-full bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-sm text-sm font-medium text-neutral-800 dark:text-neutral-100"
              >
                <span className="inline-flex items-center gap-2">
                  <Filter className="w-4 h-4 text-indigo-500" />
                  Filters
                  {(branch || course || semester) && (
                    <span className="text-xs text-indigo-500 font-normal">· active</span>
                  )}
                </span>
                <ChevronDown className={`w-4 h-4 text-neutral-400 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
              </button>
            </div>

            <div className={`bg-white dark:bg-neutral-900 rounded-2xl border border-neutral-200 dark:border-neutral-800 shadow-sm ${showFilters ? '' : 'hidden'} lg:block p-4 lg:p-6`}>
              <div className="flex items-center justify-between mb-4 lg:mb-6">
                <h2 className="text-base font-semibold flex items-center gap-2">
                  <Filter className="w-4 h-4" />
                  Filters
                </h2>
                <button
                  className="lg:hidden p-1 text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition-colors"
                  onClick={() => setShowFilters(!showFilters)}
                >
                  <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1.5">Branch</label>
                  <select
                    value={branch}
                    onChange={(e) => handleBranchChange(e.target.value)}
                    className="w-full bg-neutral-100 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 appearance-none"
                  >
                    <option value="">All Branches</option>
                    {branches.map((b: Branch) => (
                      <option key={b.name} value={b.name}>{b.name} ({b.count})</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1.5">Course Type</label>
                  <select
                    value={course}
                    onChange={(e) => updateFilters(branch, e.target.value, semester)}
                    className="w-full bg-neutral-100 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 appearance-none"
                  >
                    <option value="">All Courses</option>
                    <option value="btech">B.Tech Only</option>
                    <option value="biotech">Biotech Only</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1.5">Semester Filter</label>
                  <select
                    value={semester}
                    onChange={(e) => updateFilters(branch, course, e.target.value)}
                    className="w-full bg-neutral-100 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 appearance-none"
                  >
                    <option value="">Overall CGPA</option>
                    {availableSemesters.map(sem => (
                      <option key={sem} value={String(sem)}>Semester {sem} SGPA</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Info Box */}
              <div className="mt-4 bg-indigo-50 dark:bg-indigo-950/30 rounded-xl p-3 border border-indigo-100 dark:border-indigo-900/50">
                <div className="flex gap-2">
                  <AlertCircle className="w-4 h-4 text-indigo-500 shrink-0" />
                  <p className="text-xs text-indigo-800 dark:text-indigo-300 leading-relaxed">
                    Calculations include back-paper clearance. Subjects cleared in later sessions update the original semester&apos;s SGPA.
                  </p>
                </div>
              </div>

              {/* Stats */}
              {meta && (
                <div className="mt-3 text-xs text-neutral-400 text-center">
                  {totalCount} of {meta.total_students} students · Updated {new Date(meta.data_fetched).toLocaleDateString()}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Leaderboard Table */}
        <div className="flex-1">
          <div className="bg-white dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 shadow-sm overflow-hidden">

            {loading ? (
              <div className="p-12 flex flex-col items-center justify-center">
                {/* Skeleton loading rows */}
                <div className="w-full max-w-4xl space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-9 bg-neutral-200 dark:bg-neutral-800 rounded-full animate-pulse"></div>
                        <div className="flex-1 space-y-2">
                          <div className="h-4 bg-neutral-200 dark:bg-neutral-800 rounded animate-pulse"></div>
                          <div className="h-3 bg-neutral-200 dark:bg-neutral-800 rounded w-3/4 animate-pulse"></div>
                        </div>
                        <div className="w-20 h-5 bg-neutral-200 dark:bg-neutral-800 rounded animate-pulse"></div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-8 max-w-md text-center">
                  <p className="text-sm text-neutral-500 dark:text-neutral-400 italic">{quote}</p>
                </div>
              </div>
            ) : error ? (
              <div className="p-12 text-center text-red-500">
                <p>{error}</p>
              </div>
            ) : leaderboard.length === 0 ? (
              <div className="p-12 text-center text-neutral-500">
                <GraduationCap className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No students found for this filter combination.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {leaderboard.map((student) => {
                  const isTop3 = page === 1 && student.rank <= 3;
                  const medalStyles = [
                    'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400',
                    'bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300',
                    'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-400',
                  ];
                  return (
                    <div
                      key={student.registration_number}
                      onClick={() => router.push(`/student/${student.registration_number}`)}
                      className={`p-4 rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 hover:bg-neutral-50 dark:hover:bg-neutral-800/40 transition-all cursor-pointer shadow-sm ${isTop3 ? 'bg-gradient-to-r from-amber-50 to-white dark:from-amber-900/20 dark:to-neutral-900' : ''}`}
                    >
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                        {/* Rank and value */}
                        <div className="flex items-center gap-3">
                          <span className={`inline-flex items-center justify-center min-w-[2.5rem] h-9 px-3 rounded-full font-bold text-sm
                            ${isTop3 ? medalStyles[student.rank - 1] : 'text-neutral-500 bg-neutral-100 dark:bg-neutral-800'}
                          `}>
                            <span className="mr-1 text-xs font-normal">#{student.rank}</span>
                          </span>
                          <div className="text-right md:text-left">
                            <div className="text-xs text-neutral-500 uppercase tracking-wider md:hidden mb-1">
                              {semester ? 'SGPA' : 'CGPA'}
                            </div>
                            <div className="font-mono font-bold text-lg md:text-base text-indigo-600 dark:text-indigo-400">
                              {student.sort_value.toFixed(2)}
                            </div>
                          </div>
                        </div>

                        {/* Student info */}
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold text-base text-neutral-900 dark:text-neutral-100 mb-1 md:mb-0">
                            {student.name}
                          </div>
                          <div className="flex flex-wrap items-center gap-2 text-sm text-neutral-500 font-mono">
                            <span className="break-all">{student.registration_number}</span>
                            <span className="hidden md:inline">·</span>
                            <span className="text-neutral-600 dark:text-neutral-400">{student.branch}</span>
                          </div>
                        </div>

                        {/* Arrow */}
                        <div className="hidden md:flex items-center text-neutral-400">
                          <ChevronRight className="w-5 h-5" />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="mt-6">
              <div className="flex sm:hidden items-center gap-1 overflow-x-auto pb-2 -mx-1 px-1 scrollbar-none">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1 || loading}
                  className="flex-shrink-0 px-3 py-2 rounded-lg bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 disabled:opacity-40 text-sm"
                >
                  ‹ Prev
                </button>
                {paginationItems(totalPages, page).map((item, i) => {
                  if (item.type === "ellipsis") {
                    return <span key={`ellipsis-${i}`} className="flex-shrink-0 px-1 text-neutral-400 text-sm">…</span>;
                  }
                  return (
                    <button
                      key={item.num}
                      onClick={() => setPage(item.num)}
                      className={`flex-shrink-0 w-10 h-10 rounded-lg text-sm font-medium transition-colors ${page === item.num
                        ? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400'
                        : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400'}`}
                    >
                      {item.num}
                    </button>
                  );
                })}
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages || loading}
                  className="flex-shrink-0 px-3 py-2 rounded-lg bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 disabled:opacity-40 text-sm"
                >
                  Next ›
                </button>
              </div>

              <div className="hidden sm:flex justify-center items-center gap-2">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1 || loading}
                  className="px-4 py-2 rounded-lg bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                <div className="flex items-center gap-2">
                  {paginationItems(totalPages, page).map((item, i) => {
                    if (item.type === "ellipsis") {
                      return <span key={`ellipsis-${i}`} className="px-2 text-neutral-400">...</span>;
                    }
                    return (
                      <button
                        key={item.num}
                        onClick={() => setPage(item.num)}
                        className={`px-4 py-2 rounded-lg transition-colors ${page === item.num
                          ? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400 font-medium'
                          : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-700'}`}
                      >
                        {item.num}
                      </button>
                    );
                  })}
                </div>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages || loading}
                  className="px-4 py-2 rounded-lg bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
                {/* Go to page input */}
                <div className="flex items-center gap-2 ml-2">
                  <input
                    type="number"
                    min="1"
                    max={totalPages}
                    value={pageInput}
                    onChange={(e) => setPageInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleGoToPage()}
                    className="w-20 px-2 py-2 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 text-sm text-center"
                    placeholder="Page"
                  />
                  <button
                    onClick={handleGoToPage}
                    className="px-3 py-2 rounded-lg bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400 text-sm font-medium hover:bg-indigo-200 dark:hover:bg-indigo-800 transition-colors"
                  >
                    Go
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="mt-6 text-center text-xs text-neutral-400">
            <p>Source: BPUT (Biju Patnaik University of Technology) · Results are unofficial</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Leaderboard() {
  return (
    <Suspense fallback={<div className="p-12 text-center">Loading...</div>}>
      <LeaderboardContent />
    </Suspense>
  );
}
