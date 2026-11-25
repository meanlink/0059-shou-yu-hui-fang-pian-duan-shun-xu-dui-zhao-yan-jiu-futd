CREATE TABLE IF NOT EXISTS sign_trials(
 code text PRIMARY KEY, lesson text NOT NULL,
 state text NOT NULL DEFAULT 'open' CHECK(state IN('open','frozen','evaluated','signed'))
);
CREATE TABLE IF NOT EXISTS sign_versions(
 trial text NOT NULL REFERENCES sign_trials(code),
 arm text NOT NULL CHECK(arm IN('A','B')), clips text[] NOT NULL CHECK(cardinality(clips)=3),
 PRIMARY KEY(trial,arm)
);
CREATE TABLE IF NOT EXISTS sign_assignments(
 trial text NOT NULL, learner text NOT NULL,
 level text NOT NULL CHECK(level IN('beginner','returning')), arm text NOT NULL,
 PRIMARY KEY(trial,learner), UNIQUE(trial,learner,arm),
 FOREIGN KEY(trial,arm) REFERENCES sign_versions(trial,arm)
);
