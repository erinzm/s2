
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
CREATE TABLE nodes (
    id bigserial PRIMARY KEY,
    exp_id bigint REFERENCES experiments(id) NOT NULL,
    image_id bigint REFERENCES images(id) NOT NULL,
    
    basis_coordinates integer[],
    label integer
)

CREATE TABLE images (
    id bigserial PRIMARY KEY,
    exp_id bigint REFERENCES experiments(id) NOT NULL,
    uri VARCHAR NOT NULL
)

CREATE TABLE bases (
    id bigserial PRIMARY KEY,
    image_id bigint REFERENCES images(id) NOT NULL,
    uri VARCHAR NOT NULL
)

CREATE TABLE experiments (
    id bigserial PRIMARY KEY
)
```