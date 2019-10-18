CREATE TABLE operations_queue (
id BIGINT NOT NULL AUTO_INCREMENT,
data_object LONGTEXT NOT NULL,
PRIMARY KEY(id)
);

CREATE TABLE peers (
peer_id BIGINT NOT NULL,
forbidden_genres TEXT NOT NULL,
PRIMARY KEY(peer_id)
);

CREATE TABLE users (
id BIGINT NOT NULL,
warns INT,
PRIMARY KEY(id)
);