CREATE TABLE IF NOT EXISTS sign_scores(
 trial text NOT NULL, learner text NOT NULL,
 score int NOT NULL CHECK(score BETWEEN 0 AND 100), actual_arm text NOT NULL,
 PRIMARY KEY(trial,learner),
 FOREIGN KEY(trial,learner,actual_arm) REFERENCES sign_assignments(trial,learner,arm)
);
