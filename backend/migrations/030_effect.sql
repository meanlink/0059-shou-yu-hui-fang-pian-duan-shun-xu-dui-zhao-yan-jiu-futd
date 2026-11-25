CREATE TABLE IF NOT EXISTS sign_effect(
 trial text PRIMARY KEY REFERENCES sign_trials(code),
 effect numeric(7,4) NOT NULL, p_value numeric(8,6) NOT NULL CHECK(p_value BETWEEN 0 AND 1),
 permutations integer NOT NULL CHECK(permutations>0), detail jsonb NOT NULL
);
