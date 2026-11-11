CREATE TABLE IF NOT EXISTS fragrances (
    fragrance_id TEXT PRIMARY KEY,
    nom TEXT NOT NULL,
    famille_olfactive TEXT,
    cible_genre TEXT,
    origine_naturelle_pct NUMERIC(5, 2) CHECK (
        origine_naturelle_pct IS NULL OR origine_naturelle_pct BETWEEN 0 AND 100
    ),
    positionnement TEXT,
    volume_min_tranche_kg TEXT,
    prix_indicatif_eur_kg NUMERIC(12, 2),
    delai_proposition_jours_ouvres INTEGER,
    description_courte TEXT
);

CREATE TABLE IF NOT EXISTS fragrance_categories (
    fragrance_id TEXT NOT NULL REFERENCES fragrances(fragrance_id) ON DELETE CASCADE,
    categorie TEXT NOT NULL,
    PRIMARY KEY (fragrance_id, categorie)
);

CREATE TABLE IF NOT EXISTS fragrance_facets (
    fragrance_id TEXT NOT NULL REFERENCES fragrances(fragrance_id) ON DELETE CASCADE,
    facette TEXT NOT NULL,
    PRIMARY KEY (fragrance_id, facette)
);

CREATE TABLE IF NOT EXISTS fragrance_aromas (
    fragrance_id TEXT NOT NULL REFERENCES fragrances(fragrance_id) ON DELETE CASCADE,
    aroma TEXT NOT NULL,
    PRIMARY KEY (fragrance_id, aroma)
);

CREATE TABLE IF NOT EXISTS fragrance_certifications (
    fragrance_id TEXT NOT NULL REFERENCES fragrances(fragrance_id) ON DELETE CASCADE,
    certification TEXT NOT NULL,
    PRIMARY KEY (fragrance_id, certification)
);

CREATE TABLE IF NOT EXISTS fragrance_markets (
    fragrance_id TEXT NOT NULL REFERENCES fragrances(fragrance_id) ON DELETE CASCADE,
    marche TEXT NOT NULL,
    PRIMARY KEY (fragrance_id, marche)
);

CREATE TABLE IF NOT EXISTS needs_taxonomy (
    besoin TEXT NOT NULL,
    type_cible TEXT NOT NULL,
    cible TEXT NOT NULL,
    poids NUMERIC(5, 3),
    justification TEXT,
    PRIMARY KEY (besoin, type_cible, cible)
);

CREATE TABLE IF NOT EXISTS trends (
    tendance_id TEXT PRIMARY KEY,
    nom TEXT NOT NULL,
    theme TEXT,
    marche TEXT,
    croissance TEXT,
    indice_momentum_0_100 INTEGER CHECK (
        indice_momentum_0_100 IS NULL OR indice_momentum_0_100 BETWEEN 0 AND 100
    ),
    periode TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS trend_families (
    tendance_id TEXT NOT NULL REFERENCES trends(tendance_id) ON DELETE CASCADE,
    famille TEXT NOT NULL,
    PRIMARY KEY (tendance_id, famille)
);

CREATE TABLE IF NOT EXISTS trend_facets (
    tendance_id TEXT NOT NULL REFERENCES trends(tendance_id) ON DELETE CASCADE,
    facette TEXT NOT NULL,
    PRIMARY KEY (tendance_id, facette)
);

CREATE TABLE IF NOT EXISTS trend_aromas (
    tendance_id TEXT NOT NULL REFERENCES trends(tendance_id) ON DELETE CASCADE,
    aroma TEXT NOT NULL,
    PRIMARY KEY (tendance_id, aroma)
);

CREATE TABLE IF NOT EXISTS trend_attributes (
    tendance_id TEXT NOT NULL REFERENCES trends(tendance_id) ON DELETE CASCADE,
    attribut TEXT NOT NULL,
    PRIMARY KEY (tendance_id, attribut)
);

CREATE TABLE IF NOT EXISTS market_rules (
    regle_id TEXT PRIMARY KEY,
    type_regle TEXT,
    objet TEXT,
    effet TEXT,
    message TEXT,
    avertissement TEXT
);

CREATE TABLE IF NOT EXISTS market_rule_markets (
    regle_id TEXT NOT NULL REFERENCES market_rules(regle_id) ON DELETE CASCADE,
    marche TEXT NOT NULL,
    PRIMARY KEY (regle_id, marche)
);

CREATE TABLE IF NOT EXISTS category_dosages (
    categorie_produit TEXT PRIMARY KEY,
    dosage_min_pct NUMERIC(7, 3),
    dosage_max_pct NUMERIC(7, 3),
    dosage_recommande_pct NUMERIC(7, 3),
    note TEXT,
    CHECK (
        dosage_min_pct IS NULL OR dosage_max_pct IS NULL
        OR dosage_min_pct <= dosage_max_pct
    )
);

CREATE TABLE IF NOT EXISTS brief_fields (
    champ TEXT NOT NULL,
    etape INTEGER NOT NULL,
    libelle TEXT,
    obligatoire BOOLEAN,
    condition_text TEXT,
    field_type TEXT,
    valeurs_possibles TEXT,
    origine TEXT,
    PRIMARY KEY (champ, etape)
);

CREATE TABLE IF NOT EXISTS briefs (
    brief_id TEXT PRIMARY KEY,
    langue TEXT,
    type_brief TEXT,
    texte_libre TEXT,
    cible_genre TEXT,
    mode_direction TEXT,
    produit_reference TEXT,
    famille_olfactive TEXT,
    facette TEXT,
    volume_tranche_kg TEXT,
    budget_min_eur NUMERIC(14, 2),
    budget_max_eur NUMERIC(14, 2),
    marche_vente TEXT,
    positionnement TEXT,
    commentaire TEXT,
    completude TEXT,
    comportement_attendu TEXT,
    is_synthetic BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (
        budget_min_eur IS NULL OR budget_max_eur IS NULL
        OR budget_min_eur <= budget_max_eur
    )
);

CREATE TABLE IF NOT EXISTS brief_categories (
    brief_id TEXT NOT NULL REFERENCES briefs(brief_id) ON DELETE CASCADE,
    categorie TEXT NOT NULL,
    PRIMARY KEY (brief_id, categorie)
);

CREATE TABLE IF NOT EXISTS brief_aromas (
    brief_id TEXT NOT NULL REFERENCES briefs(brief_id) ON DELETE CASCADE,
    aroma TEXT NOT NULL,
    PRIMARY KEY (brief_id, aroma)
);

CREATE TABLE IF NOT EXISTS brief_certifications (
    brief_id TEXT NOT NULL REFERENCES briefs(brief_id) ON DELETE CASCADE,
    certification TEXT NOT NULL,
    PRIMARY KEY (brief_id, certification)
);

CREATE TABLE IF NOT EXISTS brief_missing_fields (
    brief_id TEXT NOT NULL REFERENCES briefs(brief_id) ON DELETE CASCADE,
    champ TEXT NOT NULL,
    PRIMARY KEY (brief_id, champ)
);

CREATE TABLE IF NOT EXISTS brief_expected_fragrances (
    brief_id TEXT NOT NULL REFERENCES briefs(brief_id) ON DELETE CASCADE,
    fragrance_id TEXT NOT NULL REFERENCES fragrances(fragrance_id),
    PRIMARY KEY (brief_id, fragrance_id)
);

CREATE TABLE IF NOT EXISTS evaluations (
    eval_id TEXT PRIMARY KEY,
    brief_id TEXT NOT NULL REFERENCES briefs(brief_id),
    fragrance_id TEXT NOT NULL REFERENCES fragrances(fragrance_id),
    intensite_percue TEXT,
    tenue TEXT,
    fidelite_au_brief_1_5 INTEGER CHECK (
        fidelite_au_brief_1_5 IS NULL OR fidelite_au_brief_1_5 BETWEEN 1 AND 5
    ),
    commentaire TEXT,
    decision TEXT,
    ajustement_suggere TEXT,
    note_globale_1_5 INTEGER CHECK (
        note_globale_1_5 IS NULL OR note_globale_1_5 BETWEEN 1 AND 5
    ),
    is_synthetic BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS vocabularies (
    type TEXT NOT NULL,
    valeur TEXT NOT NULL,
    PRIMARY KEY (type, valeur)
);

CREATE INDEX IF NOT EXISTS idx_evaluations_brief_id ON evaluations(brief_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_fragrance_id ON evaluations(fragrance_id);
CREATE INDEX IF NOT EXISTS idx_briefs_completude ON briefs(completude);
CREATE INDEX IF NOT EXISTS idx_fragrance_categories_categorie
    ON fragrance_categories(categorie);
