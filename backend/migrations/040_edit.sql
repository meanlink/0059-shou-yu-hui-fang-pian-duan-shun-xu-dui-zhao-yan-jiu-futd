CREATE TABLE IF NOT EXISTS sign_memos(
 trial text PRIMARY KEY REFERENCES sign_effect(trial),
 decision text NOT NULL CHECK(decision IN('adopt','keep','defer')),
 rationale text NOT NULL CHECK(length(rationale)>=6),
 signed_by text NOT NULL
);
