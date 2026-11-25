-- 冻结后成绩更正：修订轮次、结果失效、历史留痕

-- 1) 先解除旧外键，才能重建 sign_effect 的主键
ALTER TABLE sign_memos DROP CONSTRAINT IF EXISTS sign_memos_trial_fkey;
ALTER TABLE sign_memos DROP CONSTRAINT IF EXISTS sign_memos_pkey;

-- 2) 试教增加修订轮次，并允许“更正中”状态
ALTER TABLE sign_trials
    ADD COLUMN IF NOT EXISTS revision integer NOT NULL DEFAULT 1;
ALTER TABLE sign_trials DROP CONSTRAINT IF EXISTS sign_trials_state_check;
ALTER TABLE sign_trials ADD CONSTRAINT sign_trials_state_check
    CHECK (state IN ('open','frozen','evaluated','signed','revising'));

-- 3) 同一试教的每一轮修订各保留一份置换结果，旧轮次结果标记失效后仍可追溯
ALTER TABLE sign_effect ADD COLUMN IF NOT EXISTS revision integer NOT NULL DEFAULT 1;
ALTER TABLE sign_effect ADD COLUMN IF NOT EXISTS valid boolean NOT NULL DEFAULT true;
ALTER TABLE sign_effect DROP CONSTRAINT IF EXISTS sign_effect_pkey;
ALTER TABLE sign_effect DROP CONSTRAINT IF EXISTS sign_effect_trial_revision_key;
ALTER TABLE sign_effect ADD CONSTRAINT sign_effect_trial_revision_key UNIQUE (trial, revision);
ALTER TABLE sign_effect ADD CONSTRAINT sign_effect_pkey PRIMARY KEY (trial, revision);

-- 4) 教材意见每轮可各签一条，每条绑定签署当时的修订轮次与结果
ALTER TABLE sign_memos ADD COLUMN IF NOT EXISTS revision integer NOT NULL DEFAULT 1;
ALTER TABLE sign_memos ADD COLUMN IF NOT EXISTS signed_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE sign_memos ADD COLUMN IF NOT EXISTS memo_id bigint GENERATED ALWAYS AS IDENTITY;
ALTER TABLE sign_memos ADD CONSTRAINT sign_memos_pkey PRIMARY KEY (memo_id);
ALTER TABLE sign_memos DROP CONSTRAINT IF EXISTS sign_memos_trial_revision_key;
ALTER TABLE sign_memos ADD CONSTRAINT sign_memos_trial_revision_key UNIQUE (trial, revision);
ALTER TABLE sign_memos ADD CONSTRAINT sign_memos_trial_fkey
    FOREIGN KEY (trial, revision) REFERENCES sign_effect(trial, revision);

-- 5) 更正受理单：复核员在原试教登记上发起更正
CREATE TABLE IF NOT EXISTS sign_corrections(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trial text NOT NULL REFERENCES sign_trials(code),
    revision integer NOT NULL CHECK (revision >= 1),
    reason text NOT NULL CHECK (length(reason) >= 6),
    accepted_by text NOT NULL,
    accepted_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS sign_corrections_trial ON sign_corrections (trial, revision);

-- 6) 成绩变更流水：初次登记与每次更正都留痕，支持回看签署当时的成绩
CREATE TABLE IF NOT EXISTS sign_score_history(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trial text NOT NULL,
    learner text NOT NULL,
    score integer NOT NULL CHECK (score BETWEEN 0 AND 100),
    actual_arm text NOT NULL,
    revision integer NOT NULL CHECK (revision >= 1),
    source text NOT NULL CHECK (source IN ('register','correction')),
    changed_by text NOT NULL,
    changed_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS sign_score_history_lookup
    ON sign_score_history (trial, learner, changed_at, id);
