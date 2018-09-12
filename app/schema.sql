CREATE EXTENSION postgis;
CREATE EXTENSION pgrouting;

CREATE TABLE experiments (
    id bigserial PRIMARY KEY,
    required_votes_per_node bigint
);

CREATE TABLE images (
    id bigserial PRIMARY KEY,
    exp_id bigint REFERENCES experiments(id) NOT NULL,
    uri VARCHAR NOT NULL
);

CREATE TABLE nodes (
    id integer NOT NULL, -- integer to keep pgrouting happy :)
    exp_id bigint REFERENCES experiments(id) NOT NULL,
    graph_id bigint REFERENCES images(id) NOT NULL,
    
    basis_weights float[] NOT NULL,
    label integer NULL,

    PRIMARY KEY (exp_id, graph_id, id)
);

CREATE TABLE edges (
    id bigserial PRIMARY KEY,

    exp_id bigint NOT NULL,
    graph_id bigint NOT NULL,

    i integer NOT NULL,
    j integer NOT NULL,

    FOREIGN KEY (exp_id, graph_id, i) REFERENCES nodes(exp_id, graph_id, id),
    FOREIGN KEY (exp_id, graph_id, j) REFERENCES nodes(exp_id, graph_id, id)
);

CREATE TABLE bases (
    id bigserial PRIMARY KEY,
    exp_id bigint REFERENCES experiments(id) NOT NULL,
    image_id bigint REFERENCES images(id) NOT NULL,
    uri VARCHAR NOT NULL
);

CREATE TYPE jobstatus AS ENUM ('unassigned', 'waiting', 'completed');
CREATE TABLE jobs (
    id bigserial PRIMARY KEY,

    exp_id bigint NOT NULL,
    graph_id bigint NOT NULL,
    node_id bigint NOT NULL,
    
    ballot_id int NOT NULL,
    vote_label int NULL,
    status jobstatus NOT NULL,

    FOREIGN KEY (exp_id, graph_id, node_id) REFERENCES nodes (exp_id, graph_id, id)
);