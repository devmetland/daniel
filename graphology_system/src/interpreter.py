"""
Graphology Interpretation Module
Converts numerical scores into descriptive, actionable insights for HR interviews.

ETHICAL NOTICE:
- These interpretations are for DISCUSSION STARTERS only
- NOT definitive personality assessments
- Use to guide interview questions, not make decisions
"""

from typing import Dict, Tuple
import numpy as np


class GraphologyInterpreter:
    """
    Converts psychological scores into human-readable interpretations.
    
    Each interpretation includes:
    - Score value (0-100)
    - Level category (Low/Moderate/High)
    - Descriptive paragraph
    - Interview suggestions
    - Cautionary notes
    """
    
    def __init__(self):
        """Initialize the interpreter with interpretation templates."""
        
        self.interpretation_templates = {
            'leadership_score': {
                'low': {
                    'range': (0, 49),
                    'level': 'DEVELOPING',
                    'description': (
                        "Individu ini mungkin lebih nyaman bekerja dalam tim sebagai anggota daripada sebagai pemimpin. "
                        "Mereka cenderung menghindari tanggung jawab kepemimpinan dan lebih suka mengikuti arahan yang jelas. "
                        "Dalam situasi kelompok, mereka mungkin tidak secara alami mengambil inisiatif untuk memimpin."
                    ),
                    'interview_suggestions': [
                        "Tanyakan tentang pengalaman mereka dalam memimpin proyek atau tim",
                        "Eksplorasi kenyamanan mereka dengan pengambilan keputusan",
                        "Diskusikan situasi di mana mereka harus mengambil inisiatif",
                        "Tanyakan bagaimana mereka menangani tanggung jawab tambahan"
                    ],
                    'strengths': [
                        "Kemungkinan besar adalah pengikut yang baik",
                        "Cenderung kooperatif dalam tim",
                        "Mungkin detail-oriented dalam eksekusi tugas"
                    ],
                    'development_areas': [
                        "Perlu dorongan untuk mengambil kepemimpinan",
                        "Mungkin perlu pelatihan confidence-building",
                        "Bisa dikembangkan melalui mentorship bertahap"
                    ]
                },
                'moderate': {
                    'range': (50, 74),
                    'level': 'EMERGING',
                    'description': (
                        "Individu ini menunjukkan potensi kepemimpinan yang sedang berkembang. Mereka dapat memimpin dalam "
                        "situasi tertentu, terutama ketika merasa kompeten dan percaya diri. Kepemimpinan mereka mungkin "
                        "bersituasional - kuat di area keahlian mereka, namun kurang di area lain."
                    ),
                    'interview_suggestions': [
                        "Tanyakan tentang situasi di mana mereka berhasil memimpin",
                        "Eksplorasi gaya kepemimpinan alami mereka",
                        "Diskusikan bagaimana mereka memotivasi orang lain",
                        "Tanyakan tentang tantangan kepemimpinan yang pernah mereka hadapi"
                    ],
                    'strengths': [
                        "Dapat beradaptasi antara peran pemimpin dan anggota tim",
                        "Memiliki dasar keterampilan kepemimpinan",
                        "Cenderung fleksibel dalam pendekatan"
                    ],
                    'development_areas': [
                        "Dapat dikembangkan melalui pelatihan kepemimpinan formal",
                        "Perlu lebih banyak kesempatan memimpin",
                        "Mungkin perlu membangun confidence dalam situasi baru"
                    ]
                },
                'high': {
                    'range': (75, 100),
                    'level': 'STRONG',
                    'description': (
                        "Individu ini menunjukkan karakteristik kepemimpinan yang kuat. Mereka secara alami mengambil "
                        "inisiatif, mengarahkan orang lain, dan merasa nyaman dengan tanggung jawab pengambilan keputusan. "
                        "Mereka cenderung memiliki visi yang jelas dan dapat memotivasi orang lain untuk mencapainya."
                    ),
                    'interview_suggestions': [
                        "Tanyakan tentang filosofi kepemimpinan mereka",
                        "Eksplorasi bagaimana mereka menangani konflik dalam tim",
                        "Diskusikan pengalaman mereka dalam mengubah visi menjadi realitas",
                        "Tanyakan bagaimana mereka mengembangkan anggota tim mereka"
                    ],
                    'strengths': [
                        "Inisiatif tinggi dan proaktif",
                        "Kemampuan menginspirasi dan memotivasi",
                        "Nyaman dengan pengambilan keputusan strategis"
                    ],
                    'development_areas': [
                        "Perlu memastikan tidak terlalu dominan",
                        "Harus belajar mendelegasikan dengan efektif",
                        "Perlu mendengarkan masukan dari tim"
                    ]
                }
            },
            
            'emotional_stability_score': {
                'low': {
                    'range': (0, 49),
                    'level': 'SENSITIVE',
                    'description': (
                        "Individu ini mungkin lebih sensitif terhadap stres dan tekanan emosional. Mereka dapat mengalami "
                        "fluktuasi mood yang lebih signifikan dan mungkin membutuhkan waktu lebih lama untuk pulih dari "
                        "kekecewaan atau kegagalan. Dalam lingkungan kerja yang penuh tekanan, mereka mungkin memerlukan "
                        "dukungan tambahan."
                    ),
                    'interview_suggestions': [
                        "Tanyakan tentang cara mereka mengelola stres",
                        "Eksplorasi mekanisme coping yang mereka gunakan",
                        "Diskusikan situasi tekanan tinggi yang pernah mereka hadapi",
                        "Tanyakan bagaimana mereka bangkit dari kegagalan"
                    ],
                    'strengths': [
                        "Mungkin lebih empatik terhadap perasaan orang lain",
                        "Cenderung reflektif dan introspektif",
                        "Dapat sangat kreatif karena sensitivitas emosional"
                    ],
                    'development_areas': [
                        "Perlu mengembangkan strategi manajemen stres",
                        "Dapat受益于 mindfulness atau resilience training",
                        "Mungkin perlu environment kerja yang lebih supportive"
                    ],
                    'cautions': [
                        "Monitor workload untuk mencegah burnout",
                        "Berikan feedback dengan cara yang konstruktif",
                        "Sediakan saluran dukungan yang jelas"
                    ]
                },
                'moderate': {
                    'range': (50, 74),
                    'level': 'BALANCED',
                    'description': (
                        "Individu ini menunjukkan keseimbangan emosional yang sehat. Mereka dapat mengelola stres dengan "
                        "cukup baik, meskipun situasi yang sangat menantang masih dapat mempengaruhi mereka. Secara umum, "
                        "mereka mampu mempertahankan komposure dan kembali ke baseline emosional setelah menghadapi kesulitan."
                    ),
                    'interview_suggestions': [
                        "Tanyakan tentang teknik manajemen stres favorit mereka",
                        "Eksplorasi bagaimana mereka menjaga work-life balance",
                        "Diskusikan situasi di mana mereka tetap tenang di bawah tekanan",
                        "Tanyakan tentang pembelajaran dari pengalaman emosional sulit"
                    ],
                    'strengths': [
                        "Resilien dalam menghadapi tantangan sehari-hari",
                        "Dapat diandalkan dalam situasi moderat-stress",
                        "Memiliki kesadaran emosional yang baik"
                    ],
                    'development_areas': [
                        "Dapat meningkatkan resilience untuk situasi ekstrem",
                        "Perlu terus mengembangkan coping strategies",
                        "Dapat benefited dari advanced stress management training"
                    ]
                },
                'high': {
                    'range': (75, 100),
                    'level': 'VERY STABLE',
                    'description': (
                        "Individu ini menunjukkan stabilitas emosional yang sangat tinggi. Mereka tetap tenang dan terkendali "
                        "bahkan dalam situasi yang sangat menekan. Mereka jarang terpengaruh oleh drama atau konflik di sekitar "
                        "mereka dan dapat menjadi anchor emosional bagi tim mereka."
                    ),
                    'interview_suggestions': [
                        "Tanyakan tentang pengalaman mereka dalam krisis",
                        "Eksplorasi bagaimana mereka membantu orang lain mengelola emosi",
                        "Diskusikan filosofi mereka tentang menghadapi tekanan",
                        "Tanyakan tentang maintenance emotional health jangka panjang"
                    ],
                    'strengths': [
                        "Tetap tenang dalam krisis",
                        "Dapat diandalkan dalam situasi tekanan tinggi",
                        "Sering menjadi stabilisator dalam tim"
                    ],
                    'development_areas': [
                        "Perlu memastikan tidak mengabaikan emosi sendiri",
                        "Harus tetap empatik terhadap mereka yang kurang stabil",
                        "Jangan sampai terlihat tidak peduli atau dingin"
                    ]
                }
            },
            
            'confidence_score': {
                'low': {
                    'range': (0, 49),
                    'level': 'BUILDING',
                    'description': (
                        "Individu ini mungkin mengalami keraguan diri dan kurang percaya pada kemampuan mereka sendiri. "
                        "Mereka mungkin ragu-ragu dalam mengemukakan pendapat atau mengambil risiko. Namun, ini bukan "
                        "indikator kompetensi - mereka mungkin sangat capable tetapi kurang yakin dalam menampilkan kemampuan tersebut."
                    ),
                    'interview_suggestions': [
                        "Tanyakan tentang pencapaian yang paling mereka banggakan",
                        "Eksplorasi situasi di mana mereka merasa paling confident",
                        "Diskusikan bagaimana mereka menangani kritik atau feedback",
                        "Tanyakan tentang proses mereka dalam membangun self-belief"
                    ],
                    'strengths': [
                        "Cenderung humble dan open to learning",
                        "Mungkin lebih teliti karena double-check pekerjaan",
                        "Sering receptive terhadap feedback dan coaching"
                    ],
                    'development_areas': [
                        "Perlu encouragement dan positive reinforcement",
                        "Dapat benefited dari skill-building untuk boost confidence",
                        "Mungkin perlu mentor yang supportive"
                    ],
                    'cautions': [
                        "Jangan confuse dengan lack of competence",
                        "Berikan specific praise untuk achievements",
                        "Create safe space untuk berpendapat"
                    ]
                },
                'moderate': {
                    'range': (50, 74),
                    'level': 'MODERATE',
                    'description': (
                        "Individu ini menunjukkan tingkat kepercayaan diri yang sehat dan realistis. Mereka percaya pada "
                        "kemampuan mereka sendiri tetapi tetap aware akan keterbatasan. Mereka dapat mengemukakan pendapat "
                        "dengan jelas sambil tetap terbuka terhadap perspektif lain."
                    ),
                    'interview_suggestions': [
                        "Tanyakan tentang times when they had to advocate for themselves",
                        "Eksplorasi bagaimana mereka balance confidence dengan humility",
                        "Diskusikan situasi di mana confidence mereka diuji",
                        "Tanyakan tentang continuous self-improvement approach"
                    ],
                    'strengths': [
                        "Balanced view of own abilities",
                        "Can assert themselves appropriately",
                        "Open to feedback without being defensive"
                    ],
                    'development_areas': [
                        "Dapat terus build confidence melalui mastery experiences",
                        "Perlu maintain balance saat menghadapi setbacks",
                        "Dapat develop more assertiveness dalam situasi tertentu"
                    ]
                },
                'high': {
                    'range': (75, 100),
                    'level': 'HIGHLY CONFIDENT',
                    'description': (
                        "Individu ini menunjukkan kepercayaan diri yang sangat tinggi. Mereka yakin dengan kemampuan dan "
                        "penilaian mereka, tidak ragu untuk mengemukakan pendapat, dan comfortable mengambil risiko yang "
                        "diperhitungkan. Mereka cenderung persuasif dan dapat mempengaruhi orang lain dengan mudah."
                    ),
                    'interview_suggestions': [
                        "Tanyakan tentang times when their confidence was challenged",
                        "Eksplorasi bagaimana mereka handle failure atau mistakes",
                        "Diskusikan balance antara confidence dan overconfidence",
                        "Tanyakan tentang approach mereka dalam continuous learning"
                    ],
                    'strengths': [
                        "Tidak ragu mengambil initiative",
                        "Persuasif dan influential",
                        "Comfortable dengan visibility dan spotlight"
                    ],
                    'development_areas': [
                        "Perlu memastikan confidence tidak menjadi arrogance",
                        "Harus tetap open to feedback dan criticism",
                        "Jangan sampai overlook input dari orang lain"
                    ],
                    'cautions': [
                        "Monitor untuk signs of overconfidence",
                        "Ensure mereka tetap humble dan teachable",
                        "Check bahwa confidence based on actual competence"
                    ]
                }
            },
            
            'discipline_score': {
                'low': {
                    'range': (0, 49),
                    'level': 'FLEXIBLE',
                    'description': (
                        "Individu ini mungkin lebih menyukai fleksibilitas daripada struktur yang ketat. Mereka dapat "
                        "bekerja dengan baik dalam environment yang dinamis dan berubah, tetapi mungkin mengalami "
                        "kesulitan dengan rutinitas yang kaku atau deadline yang ketat. Mereka cenderung spontaneous "
                        "dan adaptable."
                    ),
                    'interview_suggestions': [
                        "Tanyakan tentang bagaimana mereka mengatur waktu dan prioritas",
                        "Eksplorasi strategies untuk meeting deadlines",
                        "Diskusikan pengalaman mereka dengan structured vs flexible environments",
                        "Tanyakan tentang tools atau systems yang mereka gunakan untuk organization"
                    ],
                    'strengths': [
                        "Adaptable dan flexible dalam perubahan",
                        "Creative dan open to new approaches",
                        "Dapat thrive dalam dynamic environments"
                    ],
                    'development_areas': [
                        "Perlu develop time management skills",
                        "Dapat benefited dari structure dan accountability systems",
                        "Mungkin perlu tools untuk tracking progress"
                    ],
                    'cautions': [
                        "Provide clear deadlines dan expectations",
                        "Regular check-ins dapat membantu stay on track",
                        "Consider role fit - mungkin lebih cocok di creative/dynamic roles"
                    ]
                },
                'moderate': {
                    'range': (50, 74),
                    'level': 'BALANCED',
                    'description': (
                        "Individu ini menunjukkan keseimbangan antara disiplin dan fleksibilitas. Mereka dapat mengikuti "
                        "struktur dan rutinitas ketika diperlukan, tetapi juga dapat beradaptasi ketika situasi menuntut. "
                        "Mereka umumnya reliable dalam memenuhi komitmen sambil tetap open to adjustments."
                    ),
                    'interview_suggestions': [
                        "Tanyakan tentang approach mereka terhadap planning vs spontaneity",
                        "Eksplorasi bagaimana mereka prioritize tasks",
                        "Diskusikan situations where they had to adapt plans",
                        "Tanyakan tentang systems mereka untuk staying organized"
                    ],
                    'strengths': [
                        "Reliable dalam大多数情况下",
                        "Flexible ketika diperlukan",
                        "Good balance of structure and adaptability"
                    ],
                    'development_areas': [
                        "Dapat strengthen consistency dalam long-term projects",
                        "Perlu maintain discipline saat motivation rendah",
                        "Dapat develop more robust planning habits"
                    ]
                },
                'high': {
                    'range': (75, 100),
                    'level': 'HIGHLY DISCIPLINED',
                    'description': (
                        "Individu ini menunjukkan tingkat disiplin yang sangat tinggi. Mereka sangat terorganisir, konsisten, "
                        "dan reliable dalam memenuhi komitmen. Mereka cenderung memiliki rutinitas yang kuat, memperhatikan "
                        "detail, dan menyelesaikan tugas-tugas tepat waktu. Mereka excel dalam environment yang membutuhkan "
                        "konsistensi dan precision."
                    ),
                    'interview_suggestions': [
                        "Tanyakan tentang daily routines dan habits mereka",
                        "Eksplorasi bagaimana mereka maintain motivation untuk long-term goals",
                        "Diskusikan situations di mana flexibility lebih penting daripada discipline",
                        "Tanyakan tentang approach mereka terhadap work-life balance"
                    ],
                    'strengths': [
                        "Sangat reliable dan consistent",
                        "Excellent time management",
                        "Detail-oriented dan thorough"
                    ],
                    'development_areas': [
                        "Perlu avoid becoming too rigid atau inflexible",
                        "Harus learn to adapt ketika plans change unexpectedly",
                        "Jangan sampai perfectionism menghambat progress"
                    ],
                    'cautions': [
                        "Monitor untuk signs of burnout dari over-discipline",
                        "Ensure mereka dapat flex ketika situasi menuntut",
                        "Watch untuk perfectionism yang counterproductive"
                    ]
                }
            }
        }
    
    def get_level(self, score: float, trait: str) -> Tuple[str, str]:
        """
        Get the level category and description key for a given score.
        
        Args:
            score: Numerical score (0-100)
            trait: Trait name (e.g., 'leadership_score')
            
        Returns:
            Tuple of (level_name, description_key)
        """
        if trait not in self.interpretation_templates:
            raise ValueError(f"Unknown trait: {trait}")
        
        template = self.interpretation_templates[trait]
        
        # Determine level based on score ranges
        if score < 50:
            return ('LOW', 'low')
        elif score < 75:
            return ('MODERATE', 'moderate')
        else:
            return ('HIGH', 'high')
    
    def interpret_single(self, trait: str, score: float) -> Dict:
        """
        Generate detailed interpretation for a single trait.
        
        Args:
            trait: Trait name (e.g., 'leadership_score')
            score: Numerical score (0-100)
            
        Returns:
            Dictionary with full interpretation
        """
        if trait not in self.interpretation_templates:
            raise ValueError(f"Unknown trait: {trait}")
        
        level_name, level_key = self.get_level(score, trait)
        template = self.interpretation_templates[trait][level_key]
        
        # Build interpretation result
        result = {
            'trait': trait,
            'score': round(score, 1),
            'level': level_name,
            'category': template['level'],
            'description': template['description'],
            'interview_suggestions': template['interview_suggestions'],
            'strengths': template['strengths'],
            'development_areas': template['development_areas']
        }
        
        # Add cautions if available
        if 'cautions' in template:
            result['cautions'] = template['cautions']
        
        return result
    
    def interpret_all(self, scores: Dict[str, float]) -> Dict:
        """
        Generate comprehensive interpretation for all traits.
        
        Args:
            scores: Dictionary of trait scores
            
        Returns:
            Dictionary with interpretations for all traits plus summary
        """
        interpretations = {}
        
        for trait, score in scores.items():
            if trait in self.interpretation_templates:
                interpretations[trait] = self.interpret_single(trait, score)
        
        # Generate overall summary
        summary = self._generate_summary(interpretations)
        
        return {
            'scores': scores,
            'interpretations': interpretations,
            'summary': summary,
            'ethical_notice': (
                "⚠️  PENTING: Interpretasi ini adalah untuk MEMANDU INTERVIEW saja. "
                "BUKAN penilaian definitif tentang karakter atau kemampuan kandidat. "
                "Selalu kombinasikan dengan metode assessment lainnya dan judgment profesional HR. "
                "Pastikan penggunaan sesuai dengan regulasi ketenagakerjaan yang berlaku."
            )
        }
    
    def _generate_summary(self, interpretations: Dict) -> Dict:
        """
        Generate an overall summary and interview strategy.
        
        Args:
            interpretations: Dictionary of trait interpretations
            
        Returns:
            Summary dictionary
        """
        # Calculate average score
        avg_score = np.mean([interp['score'] for interp in interpretations.values()])
        
        # Identify strongest and developing areas
        strongest = max(interpretations.items(), key=lambda x: x[1]['score'])
        developing = min(interpretations.items(), key=lambda x: x[1]['score'])
        
        # Count high/moderate/low
        level_counts = {'HIGH': 0, 'MODERATE': 0, 'LOW': 0}
        for interp in interpretations.values():
            level_counts[interp['level']] += 1
        
        # Generate priority focus areas
        focus_areas = []
        for trait, interp in interpretations.items():
            if interp['level'] == 'LOW':
                focus_areas.append({
                    'trait': trait,
                    'reason': f"Area pengembangan - skor {interp['score']:.1f} ({interp['category']})",
                    'suggestion': interp['development_areas'][0] if interp['development_areas'] else "Perlu eksplorasi lebih lanjut"
                })
        
        # Generate interview opening suggestion
        if level_counts['HIGH'] >= 3:
            opening_approach = (
                "Kandidat menunjukkan profil yang sangat kuat di sebagian besar area. "
                "Fokus interview dapat diarahkan pada pemahaman mendalam tentang bagaimana "
                "karakteristik ini diterapkan dalam situasi kerja nyata, serta memastikan "
                "tidak ada blind spots dari kepercayaan diri yang tinggi."
            )
        elif level_counts['LOW'] >= 2:
            opening_approach = (
                "Kandidat menunjukkan beberapa area yang perlu pengembangan. "
                "Pendekatan interview sebaiknya supportive dan exploratory, "
                "fokus pada pemahaman konteks dan potensi growth mindset. "
                "Hindari judgemental questioning dan berikan ruang untuk kandidat menjelaskan."
            )
        else:
            opening_approach = (
                "Kandidat menunjukkan profil yang balanced dengan kombinasi kekuatan dan area pengembangan. "
                "Interview dapat mengeksplorasi bagaimana kandidat leverage strengths mereka "
                "dan strategi mereka dalam mengatasi area yang perlu dikembangkan."
            )
        
        return {
            'average_score': round(avg_score, 1),
            'strongest_area': {
                'trait': strongest[0],
                'score': strongest[1]['score'],
                'level': strongest[1]['level'],
                'category': strongest[1]['category']
            },
            'developing_area': {
                'trait': developing[0],
                'score': developing[1]['score'],
                'level': developing[1]['level'],
                'category': developing[1]['category']
            },
            'level_distribution': level_counts,
            'priority_focus_areas': focus_areas,
            'recommended_opening_approach': opening_approach,
            'total_interview_suggestions': sum(
                len(interp['interview_suggestions']) 
                for interp in interpretations.values()
            )
        }
    
    def generate_report(self, scores: Dict[str, float], candidate_id: str = None) -> str:
        """
        Generate a formatted text report for HR review.
        
        Args:
            scores: Dictionary of trait scores
            candidate_id: Optional candidate identifier
            
        Returns:
            Formatted report string
        """
        result = self.interpret_all(scores)
        
        report_lines = [
            "=" * 80,
            "LAPORAN ANALISIS GRAFOLOGI - HR INTERVIEW SUPPORT",
            "=" * 80,
            f"Candidate ID: {candidate_id}" if candidate_id else "",
            f"Tanggal Analisis: {np.datetime64('now')}",
            "",
            "⚠️  DISCLAIMER: Laporan ini adalah tool pendukung insight untuk interview HR.",
            "   BUKAN dasar untuk keputusan hiring/firing otomatis.",
            "   Gunakan secara bertanggung jawab dan etis.",
            "",
            "-" * 80,
            "RINGKASAN PROFIL",
            "-" * 80,
            f"Skor Rata-rata: {result['summary']['average_score']:.1f}/100",
            f"Area Terkuat: {result['summary']['strongest_area']['trait']} "
            f"({result['summary']['strongest_area']['score']:.1f} - {result['summary']['strongest_area']['category']})",
            f"Area Pengembangan: {result['summary']['developing_area']['trait']} "
            f"({result['summary']['developing_area']['score']:.1f} - {result['summary']['developing_area']['category']})",
            "",
            "Distribusi Level:",
            f"  HIGH: {result['summary']['level_distribution']['HIGH']} trait(s)",
            f"  MODERATE: {result['summary']['level_distribution']['MODERATE']} trait(s)",
            f"  LOW: {result['summary']['level_distribution']['LOW']} trait(s)",
            "",
            "Pendekatan Interview yang Direkomendasikan:",
            result['summary']['recommended_opening_approach'],
            ""
        ]
        
        # Add detailed interpretations for each trait
        for trait, interp in result['interpretations'].items():
            report_lines.extend([
                "-" * 80,
                f"{trait.upper().replace('_', ' ')}",
                "-" * 80,
                f"Skor: {interp['score']:.1f}/100 | Level: {interp['level']} | Kategori: {interp['category']}",
                "",
                "Deskripsi:",
                interp['description'],
                "",
                "Kekuatan Potensial:",
                *[f"  ✓ {s}" for s in interp['strengths']],
                "",
                "Area Pengembangan:",
                *[f"  → {a}" for a in interp['development_areas']],
                "",
                "Saran Pertanyaan Interview:",
                *[f"  • {q}" for q in interp['interview_suggestions'][:3]],  # Top 3 suggestions
            ])
            
            if 'cautions' in interp:
                report_lines.extend([
                    "",
                    "Perhatian Khusus:",
                    *[f"  ⚠️  {c}" for c in interp['cautions']],
                ])
            
            report_lines.append("")
        
        # Add ethical notice
        report_lines.extend([
            "=" * 80,
            "PANDUAN PENGGUNAAN ETIS",
            "=" * 80,
            "✅ GUNAKAN laporan ini sebagai starting point untuk diskusi interview",
            "✅ KOMBINASIKAN dengan assessment methods lainnya (tes kompetensi, reference check, dll)",
            "✅ DOKUMENTASIKAN decision rationale secara terpisah dari hasil grafologi",
            "✅ PASTIKAN kandidat memberikan informed consent jika grafologi digunakan",
            "✅ COMPLIANCE dengan regulasi ketenagakerjaan lokal dan anti-diskriminasi",
            "",
            "❌ JANGAN gunakan sebagai satu-satunya kriteria keputusan hiring",
            "❌ JANGAN buat automated hiring/firing decisions berdasarkan hasil ini",
            "❌ JANGAN diskriminasikan kandidat berdasarkan profil grafologi",
            "❌ JANGAN share hasil ini dengan pihak yang tidak berkepentingan",
            "",
            "=" * 80,
            "END OF REPORT",
            "=" * 80
        ])
        
        return "\n".join(report_lines)


def main():
    """Example usage of the GraphologyInterpreter."""
    
    print("=" * 80)
    print("GRAPHOLOGY INTERPRETATION SYSTEM")
    print("HR Interview Support Tool - Internal Use Only")
    print("=" * 80)
    
    # Sample scores from ML prediction
    sample_scores = {
        'leadership_score': 72.5,
        'emotional_stability_score': 58.3,
        'confidence_score': 81.2,
        'discipline_score': 45.7
    }
    
    print("\nInput Scores:")
    for trait, score in sample_scores.items():
        print(f"  {trait}: {score:.1f}")
    
    # Initialize interpreter
    interpreter = GraphologyInterpreter()
    
    # Get full interpretation
    print("\n" + "=" * 80)
    print("GENERATING INTERPRETATION...")
    print("=" * 80)
    
    result = interpreter.interpret_all(sample_scores)
    
    # Display summary
    print("\n📊 SUMMARY")
    print("-" * 80)
    print(f"Average Score: {result['summary']['average_score']:.1f}/100")
    print(f"Strongest Area: {result['summary']['strongest_area']['trait']} "
          f"({result['summary']['strongest_area']['score']:.1f})")
    print(f"Developing Area: {result['summary']['developing_area']['trait']} "
          f"({result['summary']['developing_area']['score']:.1f})")
    print(f"\nRecommended Approach:")
    print(result['summary']['recommended_opening_approach'])
    
    # Display one trait interpretation as example
    print("\n\n📋 EXAMPLE INTERPRETATION (Leadership)")
    print("-" * 80)
    leadership_interp = result['interpretations']['leadership_score']
    print(f"Score: {leadership_interp['score']:.1f} | Level: {leadership_interp['level']}")
    print(f"Category: {leadership_interp['category']}")
    print(f"\nDescription:\n{leadership_interp['description']}")
    print(f"\nStrengths:")
    for s in leadership_interp['strengths']:
        print(f"  ✓ {s}")
    print(f"\nDevelopment Areas:")
    for a in leadership_interp['development_areas']:
        print(f"  → {a}")
    print(f"\nInterview Questions:")
    for q in leadership_interp['interview_suggestions'][:3]:
        print(f"  • {q}")
    
    # Generate full report
    print("\n\n" + "=" * 80)
    print("FULL TEXT REPORT")
    print("=" * 80)
    
    report = interpreter.generate_report(sample_scores, candidate_id="CAND-2025-001")
    print(report)
    
    print("\n\n✅ Interpretation complete!")
    print("Remember: Use responsibly and ethically for HR interview support only.")


if __name__ == "__main__":
    main()
