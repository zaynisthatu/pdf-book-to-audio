# Fixed regex to "Lesson" -- but also recommended switching PyPDF2 -> pdfplumber
# (more reliable text extraction for complex PDF layouts) as a robustness improvement,
# plus a flexible (Lesson|Lecture) pattern to handle either naming convention.
pattern = rf"(Lesson|Lecture)\s*{lecture_num}\b.*?(?=(Lesson|Lecture)\s*{lecture_num+1}\b|$)"
