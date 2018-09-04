CREATE TABLE experiments (
    id bigserial PRIMARY KEY
);

CREATE TABLE images (
    id bigserial PRIMARY KEY,
    exp_id bigint REFERENCES experiments(id) NOT NULL,
    uri VARCHAR NOT NULL
);

CREATE TABLE nodes (
    id bigint NOT NULL,
    exp_id bigint REFERENCES experiments(id) NOT NULL,
    graph_id bigint REFERENCES images(id) NOT NULL,
    
    basis_weights float[] NOT NULL,
    label integer NULL,

    PRIMARY KEY (exp_id, graph_id, id)
);

CREATE TABLE edges (
    exp_id bigint NOT NULL,
    graph_id bigint NOT NULL,

    i bigint NOT NULL,
    j bigint NOT NULL,

    FOREIGN KEY (exp_id, graph_id, i) REFERENCES nodes(exp_id, graph_id, id),
    FOREIGN KEY (exp_id, graph_id, j) REFERENCES nodes(exp_id, graph_id, id)
);

CREATE TABLE bases (
    id bigserial PRIMARY KEY,
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
    status jobstatus NOT NULL,

    FOREIGN KEY (exp_id, graph_id, node_id) REFERENCES nodes (exp_id, graph_id, id)
);