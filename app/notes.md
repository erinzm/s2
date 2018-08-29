
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
CREATE TABLE images (
    id BIGSERIAL PRIMARY KEY,
    exp_id BIGINT REFERENCES experiments(id) NOT NULL,
    uri VARCHAR NOT NULL
)

CREATE TABLE bases (
    id BIGSERIAL PRIMARY KEY,
    image_id BIGINT REFERENCES images(id) NOT NULL,
    uri VARCHAR NOT NULL
)

CREATE TABLE experiments (
    id BIGSERIAL PRIMARY KEY
)
```