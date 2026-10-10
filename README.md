<div align="center">

# 🏆 CGPA Monitor

### Trident Academy of Technology · 2028 Batch Rankings
**Track your SGPA / CGPA with back-paper handling** 🎓

[![Live Site](https://img.shields.io/badge/🌐_Live_Site-tat--results--2028.vercel.app-6366f1?style=for-the-badge)](https://tat-results-2028.vercel.app/)

![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=nextdotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat&logo=tailwindcss&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat&logo=vercel&logoColor=white)

**🔗 Live website: [https://tat-results-2028.vercel.app/](https://tat-results-2028.vercel.app/)**

</div>

---

## ✨ What is this?

**CGPA Monitor** is a free, student-made website that ranks the students of **Trident Academy of Technology (TAT)**, affiliated to **BPUT (Biju Patnaik University of Technology), Odisha**, by their CGPA. 📊

Open the link and you can:

- 🥇 See the **leaderboard** of the whole **2028 batch**
- 🔍 **Search** any student by name or registration number
- 📚 Open a student's page to see **every semester**: subjects, credits, grades and SGPA
- 🔁 See the **updated SGPA/CGPA after back papers are cleared**, which is not shown on the official BPUT result site

No login, no sign-up, no ads. Just open and use it. 🚀

---

## 🎯 Why was it built?

The official BPUT result portal has two problems for students who have a back paper (backlog):

1. ❌ If you fail a subject in Semester 1 and clear it later in a re-exam (for example in Semester 3), the **Semester 1 page still shows the subject as failed**. The pass only appears under the later semester, so you cannot see in one place that you have cleared it.
2. ❌ The **SGPA does not update** after you clear the back paper, so students cannot easily see their real, updated SGPA/CGPA.

CGPA Monitor puts all semesters in one place, **merges cleared back papers into their original semester**, and recalculates SGPA and CGPA using BPUT's own credit-weighted formula. ✅

---

## 🚀 Features

| | Feature |
|---|---|
| 🏆 | **Leaderboard** of all students ranked by overall CGPA |
| 🎛️ | **Filters**: by branch, by course type (B.Tech / Biotech) and by a single semester's SGPA |
| 🔍 | **Instant search** by name or registration number |
| 👤 | **Student page** with every semester, subject, credit and grade |
| 🔁 | **Back-paper aware**: cleared back papers count for the original semester |
| 📊 | **Official vs Updated SGPA** shown separately, so nothing is hidden |
| 🔗 | **Filters stay in the URL**: press Back and your filters are still there, and you can share a filtered link |
| 📱 | **Mobile friendly**: designed to work well on phones |
| ⚡ | **Very fast**: a fully static site served from a CDN, with no server or database at runtime |
| 🌙 | **Modern dark UI** with smooth loading messages |
| 📄 | **About, Terms & Conditions and Privacy Policy** page |

---

## 🧮 How the grades are calculated

BPUT uses a credit-based grading system. The grade points are:

| Grade | Meaning | Marks (out of 100) | Grade point |
|:---:|---|---|:---:|
| **O** | Outstanding | 90 and above | **10** |
| **E** | Excellent | 80 to below 90 | **9** |
| **A** | Very Good | 70 to below 80 | **8** |
| **B** | Good | 60 to below 70 | **7** |
| **C** | Fair | 50 to below 60 | **6** |
| **D** | Below Average | 37 to below 50 | **5** |
| **F** | Failed | Below 37 | **2** |
| **M** | Malpractice | n/a | **0** |
| **S** | Absent | n/a | **0** |

> 📝 Grade **D** is the pass grade for theory subjects. Grade **C** is the pass grade for practical, sessional, project, seminar and viva subjects.

### Formulas

```text
Credit Index of a subject = Credits × Grade point

SGPA = Σ Credit Index of the semester  ÷  Σ Credits of the semester

CGPA = Σ Credit Index of ALL semesters  ÷  Σ Credits of ALL semesters
```

⚠️ **CGPA is credit-weighted. It is NOT a simple average of the SGPAs.**

---

## 🛠️ Tech stack

| Layer | Technology |
|---|---|
| 🖥️ **Frontend** | [Next.js](https://nextjs.org/) |
| 🎨 **Styling** | [Tailwind CSS](https://tailwindcss.com/) |
| 🐍 **Data collection** | Python |
| 🗄️ **Database (local only)** | SQLite |
| 📦 **Data export** | Python script that generates static JSON |
| ☁️ **Hosting** | [Vercel](https://vercel.com/) |
| 🔀 **Version control** | Git and GitHub |
| 🤖 **Development** | Built with the help of AI coding assistants (Antigravity + Claude) |

---

## ⚠️ Disclaimer

> **This is an unofficial student project.** 🎓

- ❌ This website is **not official**. It has **no affiliation** with **BPUT**, **Trident Academy of Technology** or any university or college authority.
- 🌐 All results shown are taken from the **public BPUT result website**.
- 🧮 The **Updated SGPA / CGPA** and the **rankings** are **unofficial calculations**. They may contain mistakes or may differ from the official marksheet.
- 📄 Results are shown **as they were when last fetched** and may not reflect later corrections made by BPUT.
- ✅ For anything important (scholarships, placements, applications, certificates), **always refer to the official BPUT result and your official marksheet.**
- 🙅 The author takes no responsibility for any decision made on the basis of this website.

---

## 🔒 Privacy and data removal

- 🌍 The BPUT result portal has **no login or lock**, so anyone can already view anyone's result with a registration number. This website only shows that **same publicly available data**, organised in one place.
- 🙈 If you want your **name and results removed** from the website, send a request by **DM on Instagram: [@hazra_anecdotes](https://www.instagram.com/hazra_anecdotes/)**. Your data will be removed from the site.
- 🍪 The website has no login, and it does not ask visitors for personal information.

---

## 🤝 Feedback and corrections

Found a wrong grade, a wrong SGPA, or a bug? 🐞

- 📩 Send a DM on Instagram: [@hazra_anecdotes](https://www.instagram.com/hazra_anecdotes/)
- 💡 Ideas to make it better are welcome too.

Please include your **registration number** and a short description (a screenshot of the official BPUT result helps a lot). 🙏

---

## 👨‍💻 Author

**Pratyay Hazra**
B.Tech CSE student · Trident Academy of Technology · 2028 batch 🎓

[![LinkedIn](https://img.shields.io/badge/LinkedIn-pratyay--hazra-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/pratyay-hazra)
[![Instagram](https://img.shields.io/badge/Instagram-@hazra__anecdotes-E4405F?style=flat&logo=instagram&logoColor=white)](https://www.instagram.com/hazra_anecdotes/)

<div align="center">

⭐ **If this project helped you, tell a friend or give the repo a star!** ⭐

Made with ❤️ by a student, for students.

</div>
