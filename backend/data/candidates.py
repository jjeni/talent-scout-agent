"""
50 synthetic candidate profiles covering diverse skills, backgrounds, and match qualities.
Designed to test the full scoring pipeline with varied Match + Interest outcomes.
"""

CANDIDATES = [
    # ── PERFECT MATCHES (high technical fit) ──────────────────────────────────
    {
        "id": "cand_001", "name": "Priya Nair",
        "skills": ["React", "Node.js", "PostgreSQL", "AWS", "TypeScript", "GraphQL", "Stripe API"],
        "experience_years": 6.0, "location": "Remote (US timezone)",
        "email": "priya.nair@example.com", "current_title": "Senior Full-Stack Engineer",
        "education": {"degree": "B.Tech", "field": "Computer Science", "institution": "IIT Bombay"},
        "source_type": "csv"
    },
    {
        "id": "cand_002", "name": "James Okafor",
        "skills": ["React", "Node.js", "PostgreSQL", "Stripe API", "FinTech", "Docker", "Kubernetes"],
        "experience_years": 7.0, "location": "Remote (EST)",
        "email": "james.okafor@example.com", "current_title": "Lead Engineer - Payments",
        "education": {"degree": "B.Sc", "field": "Software Engineering", "institution": "University of Lagos"},
        "source_type": "csv"
    },
    {
        "id": "cand_003", "name": "Sofia Hernandez",
        "skills": ["React", "Node.js", "PostgreSQL", "AWS", "Redis", "Microservices"],
        "experience_years": 5.5, "location": "Remote",
        "email": "sofia.h@example.com", "current_title": "Full-Stack Developer",
        "education": {"degree": "M.S.", "field": "Computer Science", "institution": "Georgia Tech"},
        "source_type": "json"
    },
    {
        "id": "cand_004", "name": "Arjun Mehta",
        "skills": ["React", "TypeScript", "Node.js", "AWS", "RDS", "GraphQL", "CI/CD"],
        "experience_years": 8.0, "location": "New York, USA",
        "email": "arjun.mehta@example.com", "current_title": "Staff Engineer",
        "education": {"degree": "B.E.", "field": "Information Technology", "institution": "BITS Pilani"},
        "source_type": "github"
    },
    {
        "id": "cand_005", "name": "Emma Johansson",
        "skills": ["React", "Next.js", "Node.js", "PostgreSQL", "AWS", "Terraform"],
        "experience_years": 6.5, "location": "Remote (CET - flexible for US overlap)",
        "email": "emma.j@example.com", "current_title": "Senior Software Engineer",
        "education": {"degree": "M.Sc", "field": "Computer Science", "institution": "KTH Stockholm"},
        "source_type": "linkedin"
    },

    # ── STRONG MATCH, MEDIUM INTEREST ──────────────────────────────────────────
    {
        "id": "cand_006", "name": "Lucas Ferreira",
        "skills": ["React", "Node.js", "MySQL", "GCP", "Python", "FastAPI"],
        "experience_years": 5.0, "location": "São Paulo, Brazil (remote open)",
        "email": "lucas.f@example.com", "current_title": "Tech Lead",
        "education": {"degree": "B.Sc", "field": "Computer Science", "institution": "USP"},
        "source_type": "csv"
    },
    {
        "id": "cand_007", "name": "Aisha Mohammed",
        "skills": ["React", "Node.js", "PostgreSQL", "Azure", "TypeScript"],
        "experience_years": 5.0, "location": "Remote (UK timezone)",
        "email": "aisha.m@example.com", "current_title": "Senior Developer",
        "education": {"degree": "B.Sc", "field": "Software Systems", "institution": "University of Manchester"},
        "source_type": "pdf"
    },
    {
        "id": "cand_008", "name": "Chen Wei",
        "skills": ["React", "Vue.js", "Node.js", "AWS", "MongoDB", "TypeScript"],
        "experience_years": 6.0, "location": "San Francisco, CA (remote ok)",
        "email": "chen.wei@example.com", "current_title": "Senior Frontend Engineer",
        "education": {"degree": "M.S.", "field": "Software Engineering", "institution": "Carnegie Mellon"},
        "source_type": "json"
    },
    {
        "id": "cand_009", "name": "Fatima Al-Rashid",
        "skills": ["React", "Angular", "Node.js", "PostgreSQL", "AWS", "Docker"],
        "experience_years": 7.0, "location": "Remote",
        "email": "fatima.ar@example.com", "current_title": "Full-Stack Architect",
        "education": {"degree": "B.Tech", "field": "Computer Science", "institution": "AUB"},
        "source_type": "csv"
    },
    {
        "id": "cand_010", "name": "Diego Reyes",
        "skills": ["Node.js", "React", "PostgreSQL", "AWS S3", "GraphQL", "Redis"],
        "experience_years": 5.0, "location": "Mexico City (remote preferred)",
        "email": "diego.r@example.com", "current_title": "Backend Engineer",
        "education": {"degree": "B.Eng", "field": "Systems Engineering", "institution": "UNAM"},
        "source_type": "csv"
    },

    # ── MODERATE MATCH WITH HIGH ENTHUSIASM ────────────────────────────────────
    {
        "id": "cand_011", "name": "Yuki Tanaka",
        "skills": ["React", "Python", "Django", "PostgreSQL", "GCP", "TypeScript"],
        "experience_years": 4.0, "location": "Remote",
        "email": "yuki.t@example.com", "current_title": "Mid-level Full-Stack Developer",
        "education": {"degree": "B.Sc", "field": "Information Science", "institution": "Tokyo University"},
        "source_type": "linkedin"
    },
    {
        "id": "cand_012", "name": "Kwame Asante",
        "skills": ["React", "Node.js", "MongoDB", "Express", "JavaScript"],
        "experience_years": 3.5, "location": "Remote (GMT)",
        "email": "kwame.a@example.com", "current_title": "Full-Stack Developer",
        "education": {"degree": "B.Sc", "field": "Computer Science", "institution": "University of Ghana"},
        "source_type": "github"
    },
    {
        "id": "cand_013", "name": "Sara Lindqvist",
        "skills": ["React", "Vue.js", "Node.js", "MySQL", "AWS", "JavaScript"],
        "experience_years": 4.5, "location": "Remote (flexible timezone)",
        "email": "sara.l@example.com", "current_title": "Frontend Engineer (aspiring Full-Stack)",
        "education": {"degree": "M.Sc", "field": "Human-Computer Interaction", "institution": "Chalmers"},
        "source_type": "pdf"
    },
    {
        "id": "cand_014", "name": "Ravi Krishnamurthy",
        "skills": ["Node.js", "Express", "PostgreSQL", "REST API", "JavaScript", "TypeScript"],
        "experience_years": 4.0, "location": "Bangalore, India (open to remote)",
        "email": "ravi.k@example.com", "current_title": "Backend Developer",
        "education": {"degree": "B.E.", "field": "Computer Science", "institution": "VTU"},
        "source_type": "csv"
    },
    {
        "id": "cand_015", "name": "Mia Thompson",
        "skills": ["React", "JavaScript", "Python", "Flask", "SQLite", "Docker"],
        "experience_years": 3.0, "location": "Austin, TX (remote ok)",
        "email": "mia.t@example.com", "current_title": "Junior Full-Stack Engineer",
        "education": {"degree": "B.S.", "field": "Computer Science", "institution": "UT Austin"},
        "source_type": "pdf"
    },

    # ── GOOD EXPERIENCE, WRONG SKILLS ──────────────────────────────────────────
    {
        "id": "cand_016", "name": "Andreas Mueller",
        "skills": ["Java", "Spring Boot", "Kafka", "PostgreSQL", "AWS", "Microservices"],
        "experience_years": 10.0, "location": "Remote (CET)",
        "email": "andreas.m@example.com", "current_title": "Principal Backend Engineer",
        "education": {"degree": "M.Sc", "field": "Computer Science", "institution": "TU Munich"},
        "source_type": "json"
    },
    {
        "id": "cand_017", "name": "Priscilla Osei",
        "skills": ["Python", "Django", "FastAPI", "PostgreSQL", "AWS", "Celery"],
        "experience_years": 6.0, "location": "Remote",
        "email": "priscilla.o@example.com", "current_title": "Senior Python Developer",
        "education": {"degree": "M.Sc", "field": "Software Systems", "institution": "University of Edinburgh"},
        "source_type": "linkedin"
    },
    {
        "id": "cand_018", "name": "Marco Bianchi",
        "skills": ["PHP", "Laravel", "MySQL", "Vue.js", "Docker", "AWS"],
        "experience_years": 7.0, "location": "Remote (CET)",
        "email": "marco.b@example.com", "current_title": "Senior Web Developer",
        "education": {"degree": "B.Sc", "field": "Computer Science", "institution": "Politecnico di Milano"},
        "source_type": "csv"
    },
    {
        "id": "cand_019", "name": "Hana Park",
        "skills": ["iOS", "Swift", "SwiftUI", "Objective-C", "Firebase", "REST API"],
        "experience_years": 5.0, "location": "Remote (PST)",
        "email": "hana.p@example.com", "current_title": "iOS Engineer",
        "education": {"degree": "B.S.", "field": "Computer Engineering", "institution": "UC Berkeley"},
        "source_type": "github"
    },
    {
        "id": "cand_020", "name": "Ibrahim Hassan",
        "skills": ["Rust", "C++", "Go", "Systems Programming", "Linux", "gRPC"],
        "experience_years": 8.0, "location": "Remote",
        "email": "ibrahim.h@example.com", "current_title": "Systems Engineer",
        "education": {"degree": "M.S.", "field": "Computer Science", "institution": "MIT"},
        "source_type": "json"
    },

    # ── LOW EXPERIENCE, HIGH POTENTIAL ─────────────────────────────────────────
    {
        "id": "cand_021", "name": "Zara Ahmed",
        "skills": ["React", "JavaScript", "Node.js", "MongoDB", "CSS"],
        "experience_years": 1.5, "location": "Remote (UK)",
        "email": "zara.a@example.com", "current_title": "Junior Developer",
        "education": {"degree": "B.Sc", "field": "Computer Science", "institution": "University of Bristol"},
        "source_type": "pdf"
    },
    {
        "id": "cand_022", "name": "Carlos Pinto",
        "skills": ["React", "Node.js", "PostgreSQL", "JavaScript"],
        "experience_years": 2.0, "location": "Lisbon, Portugal (remote ok)",
        "email": "carlos.p@example.com", "current_title": "Full-Stack Developer (bootcamp grad)",
        "education": {"degree": "B.Eng", "field": "Electrical Engineering", "institution": "IST Lisbon"},
        "source_type": "linkedin"
    },
    {
        "id": "cand_023", "name": "Nora Al-Amin",
        "skills": ["React", "TypeScript", "Node.js", "Express", "REST API"],
        "experience_years": 2.5, "location": "Remote",
        "email": "nora.a@example.com", "current_title": "Software Developer",
        "education": {"degree": "B.S.", "field": "Computer Science", "institution": "AUC"},
        "source_type": "csv"
    },
    {
        "id": "cand_024", "name": "Tom Bradley",
        "skills": ["JavaScript", "React", "Express", "SQLite", "Git"],
        "experience_years": 1.0, "location": "New York, USA (remote preferred)",
        "email": "tom.b@example.com", "current_title": "Junior Web Developer",
        "education": {"degree": "B.S.", "field": "Information Systems", "institution": "NYU"},
        "source_type": "pdf"
    },
    {
        "id": "cand_025", "name": "Yemi Adeyemi",
        "skills": ["React", "Node.js", "Firebase", "JavaScript", "Tailwind CSS"],
        "experience_years": 1.5, "location": "Remote (WAT)",
        "email": "yemi.a@example.com", "current_title": "Frontend Developer",
        "education": {"degree": "B.Sc", "field": "Computer Science", "institution": "University of Ibadan"},
        "source_type": "github"
    },

    # ── OVERQUALIFIED / SENIOR LEAD PROFILES ───────────────────────────────────
    {
        "id": "cand_026", "name": "Hiroshi Yamamoto",
        "skills": ["React", "Node.js", "PostgreSQL", "AWS", "Architecture", "Team Leadership", "TypeScript"],
        "experience_years": 15.0, "location": "Tokyo (remote open)",
        "email": "hiroshi.y@example.com", "current_title": "CTO",
        "education": {"degree": "M.Eng", "field": "Computer Science", "institution": "Tokyo Tech"},
        "source_type": "linkedin"
    },
    {
        "id": "cand_027", "name": "Rachel Cohen",
        "skills": ["React", "Node.js", "AWS", "PostgreSQL", "Engineering Management", "System Design"],
        "experience_years": 12.0, "location": "San Francisco, CA",
        "email": "rachel.c@example.com", "current_title": "VP of Engineering",
        "education": {"degree": "M.S.", "field": "Software Engineering", "institution": "Stanford"},
        "source_type": "json"
    },

    # ── WRONG LOCATION ──────────────────────────────────────────────────────────
    {
        "id": "cand_028", "name": "Pavel Novak",
        "skills": ["React", "Node.js", "PostgreSQL", "AWS", "TypeScript", "GraphQL"],
        "experience_years": 6.0, "location": "Prague, Czech Republic (no remote)",
        "email": "pavel.n@example.com", "current_title": "Senior Full-Stack Developer",
        "education": {"degree": "M.Sc", "field": "Computer Science", "institution": "Czech Technical University"},
        "source_type": "csv"
    },
    {
        "id": "cand_029", "name": "Amara Diallo",
        "skills": ["React", "Node.js", "MySQL", "AWS", "JavaScript"],
        "experience_years": 5.0, "location": "Dakar, Senegal (on-site only)",
        "email": "amara.d@example.com", "current_title": "Full-Stack Engineer",
        "education": {"degree": "B.Sc", "field": "Computer Science", "institution": "UCAD"},
        "source_type": "csv"
    },

    # ── DATA SCIENCE / ML ADJACENT ──────────────────────────────────────────────
    {
        "id": "cand_030", "name": "Ananya Iyer",
        "skills": ["Python", "TensorFlow", "React", "PostgreSQL", "AWS", "Data Engineering"],
        "experience_years": 5.0, "location": "Remote",
        "email": "ananya.i@example.com", "current_title": "ML Engineer",
        "education": {"degree": "M.Tech", "field": "AI & ML", "institution": "IISc Bangalore"},
        "source_type": "linkedin"
    },

    # ── CAREER CHANGERS ─────────────────────────────────────────────────────────
    {
        "id": "cand_031", "name": "Oliver Wright",
        "skills": ["React", "JavaScript", "Node.js", "PostgreSQL"],
        "experience_years": 2.0, "location": "Remote (UK)",
        "email": "oliver.w@example.com", "current_title": "Software Developer (ex-Accountant)",
        "education": {"degree": "B.A.", "field": "Mathematics", "institution": "Oxford"},
        "source_type": "pdf"
    },
    {
        "id": "cand_032", "name": "Mei Lin",
        "skills": ["React", "TypeScript", "Node.js", "AWS", "PostgreSQL"],
        "experience_years": 3.0, "location": "Remote (PST)",
        "email": "mei.lin@example.com", "current_title": "Developer (formerly UX designer)",
        "education": {"degree": "B.A.", "field": "Design", "institution": "Parsons"},
        "source_type": "github"
    },

    # ── MORE DIVERSE PROFILES ───────────────────────────────────────────────────
    {
        "id": "cand_033", "name": "Samuel Okonkwo",
        "skills": ["React", "Node.js", "AWS", "PostgreSQL", "GraphQL", "TypeScript", "Docker"],
        "experience_years": 6.0, "location": "Remote (GMT+1)",
        "email": "samuel.o@example.com", "current_title": "Senior Engineer",
        "education": {"degree": "B.Sc", "field": "Computer Science", "institution": "Covenant University"},
        "source_type": "csv"
    },
    {
        "id": "cand_034", "name": "Valentina Cruz",
        "skills": ["React", "Node.js", "PostgreSQL", "GCP", "TypeScript"],
        "experience_years": 5.5, "location": "Buenos Aires (remote)",
        "email": "valentina.c@example.com", "current_title": "Full-Stack Engineer",
        "education": {"degree": "B.Sc", "field": "Systems Engineering", "institution": "UBA"},
        "source_type": "json"
    },
    {
        "id": "cand_035", "name": "David Kim",
        "skills": ["React", "Redux", "Node.js", "AWS", "PostgreSQL", "Jest"],
        "experience_years": 7.0, "location": "Seattle, WA (hybrid ok)",
        "email": "david.kim@example.com", "current_title": "Senior Software Engineer",
        "education": {"degree": "B.S.", "field": "Computer Science", "institution": "University of Washington"},
        "source_type": "linkedin"
    },
    {
        "id": "cand_036", "name": "Beatriz Santos",
        "skills": ["React", "Node.js", "MongoDB", "AWS", "JavaScript", "Python"],
        "experience_years": 4.0, "location": "Remote (Portuguese timezone)",
        "email": "beatriz.s@example.com", "current_title": "Software Developer",
        "education": {"degree": "M.Sc", "field": "Computer Engineering", "institution": "University of Porto"},
        "source_type": "pdf"
    },
    {
        "id": "cand_037", "name": "Ali Hassan",
        "skills": ["React", "Node.js", "PostgreSQL", "AWS", "Stripe API", "TypeScript", "Next.js"],
        "experience_years": 5.0, "location": "Remote (Dubai timezone)",
        "email": "ali.h@example.com", "current_title": "Full-Stack Developer",
        "education": {"degree": "B.Sc", "field": "Computer Science", "institution": "AUS"},
        "source_type": "csv"
    },
    {
        "id": "cand_038", "name": "Chloe Martin",
        "skills": ["React", "TypeScript", "Node.js", "AWS", "PostgreSQL", "Redis"],
        "experience_years": 5.5, "location": "Remote (EST overlap)",
        "email": "chloe.m@example.com", "current_title": "Senior Developer",
        "education": {"degree": "B.S.", "field": "Computer Science", "institution": "McGill"},
        "source_type": "json"
    },
    {
        "id": "cand_039", "name": "Hassan Ibrahim",
        "skills": ["Vue.js", "Nuxt.js", "Node.js", "PostgreSQL", "AWS", "DevOps"],
        "experience_years": 6.0, "location": "Remote",
        "email": "hassan.i@example.com", "current_title": "Full-Stack Engineer",
        "education": {"degree": "B.Sc", "field": "Computer Engineering", "institution": "Cairo University"},
        "source_type": "github"
    },
    {
        "id": "cand_040", "name": "Nina Patel",
        "skills": ["React", "Node.js", "PostgreSQL", "AWS", "TypeScript", "Microservices"],
        "experience_years": 6.0, "location": "London, UK (remote ok for US hours)",
        "email": "nina.p@example.com", "current_title": "Senior Software Engineer",
        "education": {"degree": "M.Sc", "field": "Software Engineering", "institution": "Imperial College London"},
        "source_type": "linkedin"
    },

    # ── MORE EDGE CASES ─────────────────────────────────────────────────────────
    {
        "id": "cand_041", "name": "Jason Brooks",
        "skills": ["React", "JavaScript", "Node.js", "AWS", "PostgreSQL"],
        "experience_years": 5.0, "location": "Chicago, IL (open to fully remote)",
        "email": "jason.b@example.com", "current_title": "Full-Stack Developer",
        "education": {"degree": "B.S.", "field": "MIS", "institution": "UIUC"},
        "source_type": "csv"
    },
    {
        "id": "cand_042", "name": "Selin Yildiz",
        "skills": ["React", "TypeScript", "GraphQL", "AWS", "Node.js", "Prisma"],
        "experience_years": 5.0, "location": "Remote (CET - open to US hours)",
        "email": "selin.y@example.com", "current_title": "Senior Frontend Developer",
        "education": {"degree": "B.Sc", "field": "Computer Science", "institution": "METU Ankara"},
        "source_type": "json"
    },
    {
        "id": "cand_043", "name": "Marcus Johnson",
        "skills": ["Node.js", "Express", "React", "MongoDB", "Docker", "CI/CD"],
        "experience_years": 4.5, "location": "Atlanta, GA (remote ok)",
        "email": "marcus.j@example.com", "current_title": "Full-Stack Engineer",
        "education": {"degree": "B.S.", "field": "Computer Science", "institution": "GA Tech"},
        "source_type": "pdf"
    },
    {
        "id": "cand_044", "name": "Leila Ahmadi",
        "skills": ["React", "Node.js", "AWS", "GraphQL", "PostgreSQL", "TypeScript"],
        "experience_years": 7.0, "location": "Remote (CEST - flexible)",
        "email": "leila.a@example.com", "current_title": "Senior Full-Stack Engineer",
        "education": {"degree": "M.Sc", "field": "Computer Science", "institution": "Sharif University"},
        "source_type": "linkedin"
    },
    {
        "id": "cand_045", "name": "Benjamin Osei",
        "skills": ["React", "Vue.js", "Node.js", "PostgreSQL", "AWS", "JavaScript"],
        "experience_years": 5.0, "location": "Remote",
        "email": "benjamin.o@example.com", "current_title": "Full-Stack Developer",
        "education": {"degree": "B.Sc", "field": "Computer Science", "institution": "KNUST"},
        "source_type": "csv"
    },
    {
        "id": "cand_046", "name": "Isabelle Dupont",
        "skills": ["React", "Node.js", "PostgreSQL", "Docker", "AWS", "TypeScript"],
        "experience_years": 5.5, "location": "Remote (CET / flexible)",
        "email": "isabelle.d@example.com", "current_title": "Senior Developer",
        "education": {"degree": "M.Sc", "field": "Software Engineering", "institution": "EPFL"},
        "source_type": "pdf"
    },
    {
        "id": "cand_047", "name": "Rafael Morales",
        "skills": ["React", "Node.js", "MySQL", "AWS", "PHP", "JavaScript"],
        "experience_years": 6.0, "location": "Bogotá, Colombia (remote ok)",
        "email": "rafael.m@example.com", "current_title": "Full-Stack Developer",
        "education": {"degree": "B.Sc", "field": "Systems Engineering", "institution": "Universidad de los Andes"},
        "source_type": "csv"
    },
    {
        "id": "cand_048", "name": "Ekaterina Volkov",
        "skills": ["React", "TypeScript", "Node.js", "AWS", "Kubernetes", "PostgreSQL"],
        "experience_years": 6.0, "location": "Amsterdam, Netherlands (remote)",
        "email": "ekat.v@example.com", "current_title": "Senior Software Engineer",
        "education": {"degree": "M.Sc", "field": "Computer Science", "institution": "TU Delft"},
        "source_type": "linkedin"
    },
    {
        "id": "cand_049", "name": "Takeshi Watanabe",
        "skills": ["React", "Node.js", "TypeScript", "AWS", "PostgreSQL", "Redis"],
        "experience_years": 7.0, "location": "Remote (JST - open to US hours)",
        "email": "takeshi.w@example.com", "current_title": "Senior Full-Stack Engineer",
        "education": {"degree": "B.Eng", "field": "Information Engineering", "institution": "Waseda University"},
        "source_type": "github"
    },
    {
        "id": "cand_050", "name": "Aditi Sharma",
        "skills": ["React", "Node.js", "PostgreSQL", "AWS", "Python", "TypeScript", "Stripe API"],
        "experience_years": 5.0, "location": "Remote (IST - US timezone overlap ok)",
        "email": "aditi.s@example.com", "current_title": "Full-Stack Engineer",
        "education": {"degree": "B.Tech", "field": "Computer Science", "institution": "NIT Trichy"},
        "source_type": "csv"
    }
]
