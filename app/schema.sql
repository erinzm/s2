CREATE TABLE experiments (
    id bigserial PRIMARY KEY
);

CREATE TABLE images (
    id bigserial PRIMARY KEY,
    exp_id bigint REFERENCES experiments(id) NOT NULL,
    uri VARCHAR NOT NULL
);

CREATE TABLE nodes (
    id bigserial PRIMARY KEY,
    exp_id bigint REFERENCES experiments(id) NOT NULL,
    image_id bigint REFERENCES images(id) NOT NULL,
    
    basis_coordinates integer[],
    label integer
);

CREATE TABLE bases (
    id bigserial PRIMARY KEY,
    image_id bigint REFERENCES images(id) NOT NULL,
    uri VARCHAR NOT NULL
);
