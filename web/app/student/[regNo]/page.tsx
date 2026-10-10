import { readdirSync } from "fs";
import { join } from "path";
import StudentClient from "./StudentClient";

export const dynamicParams = false;

export async function generateStaticParams() {
  const studentsDir = join(process.cwd(), "public", "data", "students");
  const files = readdirSync(studentsDir);
  return files
    .filter((f) => f.endsWith(".json"))
    .map((f) => ({ regNo: f.replace(".json", "") }));
}

export default async function StudentPage({
  params,
}: {
  params: Promise<{ regNo: string }>;
}) {
  const { regNo } = await params;
  return <StudentClient regNo={regNo} />;
}
