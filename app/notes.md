
per node:
* id
* basis coordinates

per image:
* base image
* Vec<basis image>

per experiment
* list of images

# Tables

```sql
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
    
    basis_coordinates integer[] NOT NULL,
    label integer NOT NULL
);

CREATE TABLE bases (
    id bigserial PRIMARY KEY,
    image_id bigint REFERENCES images(id) NOT NULL,
    uri VARCHAR NOT NULL
);

CREATE TYPE jobstatus AS ENUM ('unassigned', 'waiting', 'completed');
CREATE TABLE jobs (
    exp_id bigint REFERENCES experiments(id) NOT NULL,
    node_id bigint REFERENCES nodes(id) NOT NULL,
    
    ballot_id int NOT NULL,
    status jobstatus NOT NULL
);
```