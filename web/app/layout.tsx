import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { BeamsBackground } from "@/components/ui/beams-background";
import { SpotlightCursor } from "@/components/ui/spotlight-cursor";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "CGPA Monitor",
  description: "Trident Academy of Technology student rankings and SGPA tracking.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <BeamsBackground className="fixed inset-0 z-[-1]" />
        <SpotlightCursor />
        <div className="relative z-0 flex-1 flex flex-col">
          <div className="flex-1">
            {children}
          </div>
          <footer className="w-full py-6 mt-auto flex justify-center items-center gap-6 text-sm text-neutral-500 border-t border-neutral-200/20 dark:border-neutral-800/20 bg-neutral-50/50 dark:bg-neutral-900/50 backdrop-blur-sm">
            <Link href="/about#about" className="hover:text-neutral-900 dark:hover:text-neutral-300 transition-colors">About</Link>
            <Link href="/about#terms" className="hover:text-neutral-900 dark:hover:text-neutral-300 transition-colors">T&C</Link>
            <Link href="/about#privacy" className="hover:text-neutral-900 dark:hover:text-neutral-300 transition-colors">Privacy Policy</Link>
          </footer>
        </div>
      </body>
    </html>
  );
}
