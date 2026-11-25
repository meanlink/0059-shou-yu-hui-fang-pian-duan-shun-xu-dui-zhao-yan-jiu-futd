from effects import calculate


def seed(cx):
    for code, lesson in [('SR-12', '问路课回放动词'), ('SR-11', '买菜课回放数字'), ('SR-10', '休息日三片段复盘')]:
        if not cx.execute("""INSERT INTO sign_trials(code,lesson) VALUES (%s,%s)
           ON CONFLICT DO NOTHING RETURNING code""", (code, lesson)).fetchone():
            continue
        cx.execute("""INSERT INTO sign_versions VALUES (%s,'A',%s),(%s,'B',%s)""",
                   (code, ['词组示范', '情境应用', '镜像练习'],
                    code, ['情境应用', '词组示范', '镜像练习']))
        for level, stem, scores in [('beginner', 'N', [45, 55, 57, 67]),
                                    ('returning', 'R', [65, 75, 77, 87])]:
            for i, score in enumerate(scores, 1):
                learner = f"{stem}-{i}"
                arm = "A" if i <= 2 else "B"
                cx.execute("INSERT INTO sign_assignments VALUES (%s,%s,%s,%s)",
                           (code, learner, level, arm))
                if code != 'SR-11' or i < 4:
                    cx.execute("INSERT INTO sign_scores VALUES (%s,%s,%s,%s)",
                               (code, learner, score, arm))
                    cx.execute("""
                        INSERT INTO sign_score_history
                            (trial, learner, score, actual_arm, revision, source, changed_by)
                        VALUES (%s,%s,%s,%s,1,'register','operator@demo.local')
                    """, (code, learner, score, arm))
        if code == 'SR-10':
            calculate(cx, code, 1)
            cx.execute("""
                INSERT INTO sign_memos(trial, revision, decision, rationale, signed_by)
                VALUES (%s,1,'keep','沿用首版课件，待下一次复查。','reviewer@demo.local')
            """, (code,))
            cx.execute("UPDATE sign_trials SET state='signed' WHERE code=%s", (code,))
